"""
管理端接口模块
提供场景配置管理、统计查询等管理功能

作者：成员 B
日期：2026-04-02
"""

from flask import Blueprint, request
from app.utils.response import success_response, error_response
from app.services.config_manager import ConfigManager
from app.services.scenario_adapter import get_scenario_adapter
from app.enums import StationQueueMode
from typing import Dict, Any

admin_bp = Blueprint('admin', __name__)


# ============================================
# 场景配置管理接口
# ============================================

@admin_bp.route('/scenario', methods=['POST'])
def create_scenario():
    """
    创建场景配置
    
    Request Body:
        {
            "config_name": "测试场景",
            "fast_station_count": 2,
            "slow_station_count": 3,
            "waiting_area_capacity": 6,
            "station_queue_mode": "UNIFORM_CAPACITY",
            "station_queue_capacity": 3,
            "description": "场景描述"
        }
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "config_id": 1,
                "config_name": "测试场景"
            }
        }
    """
    data = request.get_json()
    
    if not data:
        return error_response(1001, "请求体不能为空")
    
    # 提取参数
    config_name = data.get('config_name')
    if not config_name:
        return error_response(1001, "config_name 不能为空")
    
    fast_count = data.get('fast_station_count', 2)
    slow_count = data.get('slow_station_count', 3)
    waiting_capacity = data.get('waiting_area_capacity', 6)
    queue_mode = data.get('station_queue_mode', 'UNIFORM_CAPACITY')
    queue_capacity = data.get('station_queue_capacity', 3)
    description = data.get('description', '')
    
    # 验证队列模式
    if queue_mode not in [m.value for m in StationQueueMode]:
        return error_response(1001, f"无效的队列模式: {queue_mode}")
    
    # 创建配置
    success, config_id, message = ConfigManager.create_config(
        config_name=config_name,
        fast_station_count=fast_count,
        slow_station_count=slow_count,
        waiting_area_capacity=waiting_capacity,
        station_queue_mode=queue_mode,
        station_queue_capacity=queue_capacity,
        description=description
    )
    
    if not success:
        return error_response(1003, message)
    
    return success_response({
        "config_id": config_id,
        "config_name": config_name
    })


@admin_bp.route('/scenario/<int:config_id>', methods=['GET'])
def get_scenario(config_id: int):
    """
    获取场景配置详情
    
    Args:
        config_id: 场景配置ID
    
    Returns:
        场景配置详情
    """
    config = ConfigManager.get_config(config_id)
    
    if not config:
        return error_response(1002, "场景配置不存在")
    
    return success_response(config.to_dict())


@admin_bp.route('/scenario', methods=['GET'])
def list_scenarios():
    """
    获取所有场景配置列表
    
    Returns:
        场景配置列表
    """
    configs = ConfigManager.get_all_configs()
    
    return success_response({
        "total": len(configs),
        "scenarios": [config.to_dict() for config in configs]
    })


@admin_bp.route('/scenario/<int:config_id>', methods=['PUT'])
def update_scenario(config_id: int):
    """
    更新场景配置
    
    注意：已激活的配置不能修改，需要先停用
    """
    data = request.get_json()
    
    if not data:
        return error_response(1001, "请求体不能为空")
    
    # 提取可更新字段
    allowed_fields = [
        'config_name', 'fast_station_count', 'slow_station_count',
        'waiting_area_capacity', 'station_queue_mode',
        'station_queue_capacity', 'description'
    ]
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_data:
        return error_response(1001, "没有可更新的字段")
    
    success, message = ConfigManager.update_config(config_id, **update_data)
    
    if not success:
        return error_response(1003, message)
    
    return success_response({"message": message})


@admin_bp.route('/scenario/<int:config_id>', methods=['DELETE'])
def delete_scenario(config_id: int):
    """
    删除场景配置
    
    注意：不能删除已激活的配置
    """
    success, message = ConfigManager.delete_config(config_id)
    
    if not success:
        return error_response(1003, message)
    
    return success_response({"message": message})


@admin_bp.route('/scenario/<int:config_id>/activate', methods=['POST'])
def activate_scenario(config_id: int):
    """
    激活场景配置
    
    激活新配置时会自动停用其他配置
    """
    success, message = ConfigManager.activate_config(config_id)
    
    if not success:
        return error_response(1003, message)
    
    return success_response({"message": message})


@admin_bp.route('/scenario/<int:config_id>/initialize', methods=['POST'])
def initialize_scenario(config_id: int):
    """
    初始化场景（创建充电桩）
    """
    success, message = ConfigManager.initialize_stations_for_scenario(config_id)
    
    if not success:
        return error_response(1003, message)
    
    return success_response({"message": message})


@admin_bp.route('/scenario/<int:config_id>/reset', methods=['POST'])
def reset_scenario(config_id: int):
    """
    重置场景到初始状态
    """
    adapter = get_scenario_adapter()
    success, message = adapter.reset_scenario(config_id)
    
    if not success:
        return error_response(1003, message)
    
    return success_response({"message": message})


@admin_bp.route('/scenario/<int:config_id>/summary', methods=['GET'])
def get_scenario_summary(config_id: int):
    """
    获取场景摘要信息
    
    包括充电桩状态统计、等待池状态等
    """
    summary = ConfigManager.get_scenario_summary(config_id)
    
    if not summary:
        return error_response(1002, "场景配置不存在")
    
    return success_response(summary)


# ============================================
# 等待池状态查询接口
# ============================================

@admin_bp.route('/waiting-pools/status', methods=['GET'])
def get_waiting_pools_status():
    """
    获取当前等待池状态
    
    Returns:
        {
            "fast_pool": {...},
            "slow_pool": {...},
            "total_waiting": 5,
            "capacity": 6,
            "available_slots": 1
        }
    """
    from app.services.waiting_pool import get_waiting_pool_manager
    
    manager = get_waiting_pool_manager()
    status = manager.get_pool_status()
    
    if not status:
        return error_response(1003, "无法获取等待池状态")
    
    return success_response(status)


@admin_bp.route('/waiting-pools/statistics', methods=['GET'])
def get_waiting_pools_statistics():
    """
    获取等待池统计信息
    """
    from app.services.waiting_pool import get_waiting_pool_manager
    
    manager = get_waiting_pool_manager()
    stats = manager.get_pool_statistics()
    
    if not stats:
        return error_response(1003, "无法获取等待池统计")
    
    return success_response(stats)


# ============================================
# 系统状态接口
# ============================================

@admin_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """
    获取系统整体状态
    
    包括当前激活场景、等待池状态、充电桩概况
    """
    # 获取当前激活场景
    active_config = ConfigManager.get_active_config()
    
    if not active_config:
        return error_response(1003, "没有激活的场景配置")
    
    # 获取场景摘要
    summary = ConfigManager.get_scenario_summary(active_config.id)
    
    # 获取等待池状态
    from app.services.waiting_pool import get_waiting_pool_manager
    manager = get_waiting_pool_manager()
    pool_status = manager.get_pool_status()
    
    return success_response({
        "active_scenario": active_config.to_dict(),
        "scenario_summary": summary,
        "waiting_pools": pool_status
    })
