"""
批量模拟接口模块
实现系统验收要求的批量测试接口

路径：POST /api/batch/simulate

作者：成员 B
日期：2026-04-02
版本：V1.0
"""

from flask import Blueprint, request
from app.utils.response import success_response, error_response
from app.services.scheduler_engine import simulate_batch_case
from app.enums import StationQueueMode
from typing import Dict, Any, List

batch_bp = Blueprint('batch', __name__)


@batch_bp.route('/simulate', methods=['POST'])
def batch_simulate():
    """
    批量模拟接口
    
    根据验收场景参数和用户行为模拟数据，执行批量测试
    
    Request Body:
        {
            "test_case_id": "BATCH_001",
            "scenario": {
                "fast_station_count": 2,
                "slow_station_count": 3,
                "waiting_area_capacity": 6,
                "station_queue_mode": "UNIFORM_CAPACITY",
                "station_queue_capacity": 3
            },
            "users": [
                {
                    "user_id": "U001",
                    "request_time": "2026-03-30T10:00:00",
                    "charge_mode": "FAST",
                    "request_energy": 20.0,
                    "cancel_queue": false,
                    "cancel_time": null,
                    "confirm_arrival_delay_seconds": 60,
                    "interrupt_charge": false,
                    "interrupt_time": null,
                    "leave_delay_seconds": 120
                }
            ]
        }
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "test_case_id": "BATCH_001",
                "summary": {
                    "total_users": 10,
                    "completed_users": 9,
                    "avg_wait_seconds": 320,
                    "avg_finish_seconds": 1850,
                    "total_finish_seconds": 16650,
                    "station_utilization": 0.81
                },
                "results": [
                    {
                        "user_id": "U001",
                        "detail": {...},
                        "bill": {...}
                    }
                ]
            }
        }
    """
    data = request.get_json()
    
    # 参数校验
    is_valid, errors = validate_batch_request(data)
    if not is_valid:
        return error_response(1001, "Invalid parameters", {"errors": errors})
    
    try:
        # 1. 解析场景参数
        scenario_config = data.get('scenario', {})
        test_case_id = data.get('test_case_id', 'BATCH_UNKNOWN')
        users_config = data.get('users', [])
        
        simulation = simulate_batch_case(test_case_id, scenario_config, users_config)
        return success_response(simulation)
        
    except Exception as e:
        return error_response(1099, f"批量模拟执行失败: {str(e)}")


def validate_batch_request(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    校验批量模拟请求参数
    
    Returns:
        (是否有效, 错误列表)
    """
    errors = []
    
    if not data:
        errors.append("请求体不能为空")
        return False, errors
    
    # 校验 test_case_id
    if not data.get('test_case_id'):
        errors.append("test_case_id 不能为空")
    
    # 校验 scenario
    scenario = data.get('scenario')
    if not scenario:
        errors.append("scenario 不能为空")
    else:
        # 校验必填字段
        required_fields = ['fast_station_count', 'slow_station_count', 'waiting_area_capacity']
        for field in required_fields:
            if field not in scenario:
                errors.append(f"scenario.{field} 不能为空")
        
        # 校验队列模式
        mode = scenario.get('station_queue_mode', 'UNIFORM_CAPACITY')
        if mode not in [m.value for m in StationQueueMode]:
            errors.append(f"无效的 station_queue_mode: {mode}")
        
        # 快照模式下需要 station_snapshots
        if mode == StationQueueMode.STATION_SNAPSHOT.value:
            if not scenario.get('station_snapshots'):
                errors.append("STATION_SNAPSHOT 模式下需要提供 station_snapshots")
    
    # 校验 users
    users = data.get('users', [])
    if not isinstance(users, list):
        errors.append("users 必须是数组")
    else:
        for i, user in enumerate(users):
            user_errors = validate_user_config(user, i)
            errors.extend(user_errors)
    
    return len(errors) == 0, errors


def validate_user_config(user: Dict[str, Any], index: int) -> List[str]:
    """校验单个用户配置"""
    errors = []
    prefix = f"users[{index}]"
    
    # 必填字段
    required = ['user_id', 'request_time', 'charge_mode', 'request_energy']
    for field in required:
        if field not in user:
            errors.append(f"{prefix}.{field} 不能为空")
    
    # 校验 charge_mode
    if user.get('charge_mode') not in ['FAST', 'SLOW']:
        errors.append(f"{prefix}.charge_mode 必须是 FAST 或 SLOW")
    
    # 校验 request_energy
    if user.get('request_energy', 0) <= 0:
        errors.append(f"{prefix}.request_energy 必须大于0")
    
    # 校验布尔字段
    boolean_fields = ['cancel_queue', 'interrupt_charge']
    for field in boolean_fields:
        if field in user and not isinstance(user[field], bool):
            errors.append(f"{prefix}.{field} 必须是布尔值")
    
    return errors

