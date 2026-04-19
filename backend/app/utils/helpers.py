"""
辅助工具模块
提供全局通用的辅助函数，避免循环导入问题

作者：成员 B
日期：2026-04-02
"""

from app.utils.db import query_db
from typing import Optional, Dict, Any


def get_active_scenario() -> Optional[Dict[str, Any]]:
    """
    获取当前激活的场景配置
    
    这是一个独立函数，避免循环导入问题
    
    Returns:
        场景配置字典或None
    """
    data = query_db(
        """SELECT id, config_name, fast_station_count, slow_station_count,
                   waiting_area_capacity, station_queue_mode, 
                   station_queue_capacity, is_active, description
            FROM system_scenario_config 
            WHERE is_active = 1 
            LIMIT 1""",
        one=True
    )
    
    if data:
        return {
            'id': data['id'],
            'config_name': data['config_name'],
            'fast_station_count': data['fast_station_count'],
            'slow_station_count': data['slow_station_count'],
            'waiting_area_capacity': data['waiting_area_capacity'],
            'station_queue_mode': data['station_queue_mode'],
            'station_queue_capacity': data['station_queue_capacity'],
            'is_active': bool(data['is_active']),
            'description': data['description']
        }
    return None


def get_active_scenario_id() -> Optional[int]:
    """获取当前激活的场景配置ID"""
    scenario = get_active_scenario()
    return scenario['id'] if scenario else None


def can_accept_request(charge_mode: str) -> tuple[bool, str]:
    """
    检查是否可以接受新请求
    
    检查等待区是否已满
    
    Args:
        charge_mode: 充电模式 ('FAST' 或 'SLOW')
    
    Returns:
        (是否可以接收, 原因说明)
    """
    from app.enums import ChargeMode, RequestStatus
    
    scenario = get_active_scenario()
    if not scenario:
        return False, "没有激活的场景配置"
    
    # 统计当前等待人数
    waiting_count = query_db("""
        SELECT COUNT(*) as cnt 
        FROM charge_request 
        WHERE scenario_id = ? AND status = ?
    """, [scenario['id'], 'WAITING'], one=True)
    
    if waiting_count['cnt'] >= scenario['waiting_area_capacity']:
        return False, f"等待区已满（{waiting_count['cnt']}/{scenario['waiting_area_capacity']}）"
    
    return True, f"可以接收请求（当前等待: {waiting_count['cnt']}/{scenario['waiting_area_capacity']}）"


def format_datetime(dt) -> Optional[str]:
    """
    格式化日期时间为ISO 8601字符串
    
    Args:
        dt: datetime对象或字符串
    
    Returns:
        ISO 8601格式字符串
    """
    from datetime import datetime
    
    if dt is None:
        return None
    
    if isinstance(dt, str):
        # 尝试解析并重新格式化
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    return str(dt)


def calculate_service_time(request_energy: float, charge_mode: str) -> float:
    """
    计算预计服务时长（分钟）
    
    Args:
        request_energy: 申请充电量（kWh）
        charge_mode: 充电模式
    
    Returns:
        预计服务时长（分钟）
    """
    # 快充功率 30kW，慢充功率 7kW
    power_kw = 30.0 if charge_mode == 'FAST' else 7.0
    
    # 计算小时数，转换为分钟
    hours = request_energy / power_kw
    minutes = hours * 60
    
    return round(minutes, 2)


def generate_request_id(prefix: str = "REQ") -> str:
    """
    生成请求ID
    
    Args:
        prefix: ID前缀
    
    Returns:
        请求ID字符串
    """
    count = query_db("SELECT COUNT(*) as cnt FROM charge_request", one=True)
    return f"{prefix}{count['cnt'] + 1:03d}"


def safe_get(dictionary: Dict, key: str, default=None):
    """安全获取字典值"""
    if dictionary is None:
        return default
    return dictionary.get(key, default)
