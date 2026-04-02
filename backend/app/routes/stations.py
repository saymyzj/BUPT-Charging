"""
充电桩总览接口模块
提供充电桩状态总览信息

路径：GET /api/stations/overview

作者：成员 B
日期：2026-04-02
"""

from flask import Blueprint
from app.utils.response import success_response, error_response
from app.utils.db import query_db
from app.services.config_manager import get_active_scenario
from app.services.waiting_pool import get_waiting_pool_manager

stations_bp = Blueprint('stations', __name__)


@stations_bp.route('/overview', methods=['GET'])
def get_stations_overview():
    """
    获取充电桩总览
    
    返回所有充电桩的状态、排队人数等信息
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "fast_stations": [
                    {
                        "station_id": "FAST_01",
                        "station_type": "FAST",
                        "power_kw": 30.0,
                        "status": "IDLE",
                        "current_request_id": null,
                        "available_time": "2026-03-31T10:00:00"
                    }
                ],
                "slow_stations": [
                    {
                        "station_id": "SLOW_01",
                        "station_type": "SLOW",
                        "power_kw": 7.0,
                        "status": "IDLE",
                        "current_request_id": null,
                        "available_time": "2026-03-31T10:00:00"
                    }
                ],
                "waiting_queue": {
                    "fast_queue_count": 0,
                    "slow_queue_count": 0,
                    "total_waiting": 0,
                    "capacity": 6
                }
            }
        }
    """
    # 获取当前激活场景
    active_scenario = get_active_scenario()
    if not active_scenario:
        return error_response(1003, "No active scenario configuration")
    
    # 查询所有充电桩
    stations = query_db(
        """SELECT id, station_code, station_type, power_kw, status, 
                   current_request_id, available_time
            FROM charging_station 
            WHERE scenario_id = ?
            ORDER BY station_code""",
        [active_scenario.id]
    )
    
    # 分类整理充电桩
    fast_stations = []
    slow_stations = []
    
    if stations:
        for station in stations:
            station_data = {
                "station_id": station['station_code'],
                "station_type": station['station_type'],
                "power_kw": station['power_kw'],
                "status": station['status'],
                "current_request_id": station['current_request_id'],
                "available_time": station['available_time']
            }
            
            if station['station_type'] == 'FAST':
                fast_stations.append(station_data)
            else:
                slow_stations.append(station_data)
    
    # 获取等待池状态
    pool_manager = get_waiting_pool_manager()
    pool_status = pool_manager.get_pool_status()
    
    waiting_queue = {
        "fast_queue_count": pool_status['fast_pool']['count'] if pool_status else 0,
        "slow_queue_count": pool_status['slow_pool']['count'] if pool_status else 0,
        "total_waiting": pool_status['total_waiting'] if pool_status else 0,
        "capacity": active_scenario.waiting_area_capacity
    }
    
    return success_response({
        "fast_stations": fast_stations,
        "slow_stations": slow_stations,
        "waiting_queue": waiting_queue
    })
