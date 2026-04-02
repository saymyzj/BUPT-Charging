"""
批量模拟接口模块【框架版本 - 待完善】

当前状态：框架完成，核心逻辑待实现
- 场景参数解析：已完成
- 用户行为解析：已完成
- 批量模拟执行：基础顺序模拟，时间序列模拟待实现
- 结果统计：占位值，真实计算待实现

路径：POST /api/batch/simulate

作者：成员 B
日期：2026-04-02
版本：V1.0-framework
"""

from flask import Blueprint, request
from app.utils.response import success_response, error_response
from app.services.scenario_adapter import adapt_and_initialize, get_scenario_adapter
from app.services.config_manager import ConfigManager
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
        
        # 2. 适配并初始化场景
        success, message, config_id = adapt_and_initialize(scenario_config)
        if not success:
            return error_response(1003, f"场景初始化失败: {message}")
        
        # 3. 执行批量模拟（基础版本：顺序执行）
        # TODO: 后续优化为时间序列模拟
        results = execute_batch_simulation_basic(config_id, users_config)
        
        # 4. 计算统计指标
        summary = calculate_summary(results)
        
        # 5. 组装响应
        return success_response({
            "test_case_id": test_case_id,
            "summary": summary,
            "results": results
        })
        
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


def execute_batch_simulation_basic(config_id: int, users_config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    执行基础批量模拟（顺序执行版本）【框架实现】

    当前实现：按顺序处理每个用户请求（简化版本）
    待完善：时间序列模拟引擎，真实调度接入

    Args:
        config_id: 场景配置ID
        users_config: 用户配置列表

    Returns:
        每个用户的执行结果列表（含占位数据）
    """
    results = []
    
    for user_config in users_config:
        user_result = simulate_single_user(config_id, user_config)
        results.append(user_result)
    
    return results


def simulate_single_user(config_id: int, user_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    模拟单个用户的完整流程【框架实现 - 占位返回】

    当前实现：仅返回用户ID和占位结果
    待完善：
    1. 创建请求并加入等待池
    2. 根据行为参数模拟用户行为
    3. 等待调度模块分配充电桩
    4. 模拟充电过程
    5. 生成详单和账单
    """
    user_id = user_config.get('user_id')
    
    try:
        # TODO: 完整流程模拟
        # 1. 创建请求
        # 2. 根据行为参数模拟用户行为
        # 3. 等待调度
        # 4. 模拟充电过程
        # 5. 生成详单账单
        
        # 当前简化版本：只返回用户ID和占位结果
        return {
            "user_id": user_id,
            "status": "SIMULATED",
            "detail": {
                "request_id": f"REQ_{user_id}",
                "charge_mode": user_config.get('charge_mode'),
                "request_energy": user_config.get('request_energy'),
                "note": "基础模拟版本，完整流程待实现"
            },
            "bill": {
                "total_fee": 0.0,
                "note": "基础模拟版本，账单待计算"
            }
        }
        
    except Exception as e:
        return {
            "user_id": user_id,
            "status": "FAILED",
            "error": str(e),
            "detail": {},
            "bill": {}
        }


def calculate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算批量模拟的统计指标【框架实现 - 占位值】

    当前实现：仅统计用户数量，其他指标为0
    待完善：根据真实模拟结果计算
    - 平均等待时间
    - 平均完成时间
    - 总完成时间
    - 充电桩利用率
    """
    total_users = len(results)
    completed_users = sum(1 for r in results if r.get('status') == 'SIMULATED')
    failed_users = sum(1 for r in results if r.get('status') == 'FAILED')
    
    # 基础版本使用模拟值
    # TODO: 后续根据真实结果计算
    return {
        "total_users": total_users,
        "completed_users": completed_users,
        "failed_users": failed_users,
        "avg_wait_seconds": 0,        # 待实现
        "avg_finish_seconds": 0,      # 待实现
        "total_finish_seconds": 0,    # 待实现
        "station_utilization": 0.0,   # 待实现
        "note": "基础版本，统计指标待完善"
    }


# TODO: 后续实现时间序列模拟引擎
# class BatchSimulationEngine:
#     """批量模拟引擎（时间序列版本）"""
#     pass
