"""
场景配置管理模块
管理系统场景配置的CRUD操作和激活切换
支持动态配置验收场景参数

作者：成员 B
日期：2026-04-02
"""

from app.utils.db import query_db, execute_db
from app.enums import StationQueueMode, ChargeMode
from typing import Optional, List, Dict, Any
from datetime import datetime


class ScenarioConfig:
    """场景配置数据类"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.config_name = data.get('config_name')
        self.fast_station_count = data.get('fast_station_count', 2)
        self.slow_station_count = data.get('slow_station_count', 3)
        self.waiting_area_capacity = data.get('waiting_area_capacity', 6)
        self.station_queue_mode = data.get('station_queue_mode', 'UNIFORM_CAPACITY')
        self.station_queue_capacity = data.get('station_queue_capacity', 3)
        self.is_active = data.get('is_active', 0)
        self.description = data.get('description', '')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'config_name': self.config_name,
            'fast_station_count': self.fast_station_count,
            'slow_station_count': self.slow_station_count,
            'waiting_area_capacity': self.waiting_area_capacity,
            'station_queue_mode': self.station_queue_mode,
            'station_queue_capacity': self.station_queue_capacity,
            'is_active': bool(self.is_active),
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def validate(self) -> tuple[bool, str]:
        """验证配置有效性"""
        if self.fast_station_count < 0 or self.slow_station_count < 0:
            return False, "充电桩数量不能为负数"
        
        if self.waiting_area_capacity < 0:
            return False, "等待区容量不能为负数"
        
        if self.station_queue_mode not in [mode.value for mode in StationQueueMode]:
            return False, f"无效的队列模式: {self.station_queue_mode}"
        
        if self.station_queue_capacity < 0:
            return False, "队列容量不能为负数"
        
        return True, "验证通过"


class ConfigManager:
    """场景配置管理器"""
    
    @staticmethod
    def create_config(
        config_name: str,
        fast_station_count: int = 2,
        slow_station_count: int = 3,
        waiting_area_capacity: int = 6,
        station_queue_mode: str = 'UNIFORM_CAPACITY',
        station_queue_capacity: int = 3,
        description: str = ''
    ) -> tuple[bool, int, str]:
        """
        创建新场景配置
        
        Returns:
            (success, config_id, message)
        """
        # 验证数据
        config = ScenarioConfig({
            'config_name': config_name,
            'fast_station_count': fast_station_count,
            'slow_station_count': slow_station_count,
            'waiting_area_capacity': waiting_area_capacity,
            'station_queue_mode': station_queue_mode,
            'station_queue_capacity': station_queue_capacity,
            'description': description
        })
        
        is_valid, message = config.validate()
        if not is_valid:
            return False, -1, message
        
        try:
            execute_db("""
                INSERT INTO system_scenario_config (
                    config_name, fast_station_count, slow_station_count,
                    waiting_area_capacity, station_queue_mode,
                    station_queue_capacity, is_active, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                config_name, fast_station_count, slow_station_count,
                waiting_area_capacity, station_queue_mode,
                station_queue_capacity, 0, description
            ])
            
            # 获取新创建的ID
            result = query_db(
                "SELECT id FROM system_scenario_config WHERE config_name = ?",
                [config_name],
                one=True
            )
            
            return True, result['id'], "场景配置创建成功"
            
        except Exception as e:
            return False, -1, f"创建失败: {str(e)}"
    
    @staticmethod
    def get_config(config_id: int) -> Optional[ScenarioConfig]:
        """获取指定场景配置"""
        data = query_db(
            "SELECT * FROM system_scenario_config WHERE id = ?",
            [config_id],
            one=True
        )
        
        if data:
            return ScenarioConfig(dict(data))
        return None
    
    @staticmethod
    def get_active_config() -> Optional[ScenarioConfig]:
        """获取当前激活的场景配置"""
        data = query_db(
            "SELECT * FROM system_scenario_config WHERE is_active = 1 LIMIT 1",
            one=True
        )
        
        if data:
            return ScenarioConfig(dict(data))
        return None
    
    @staticmethod
    def get_all_configs() -> List[ScenarioConfig]:
        """获取所有场景配置"""
        datas = query_db(
            "SELECT * FROM system_scenario_config ORDER BY created_at DESC"
        )
        
        return [ScenarioConfig(dict(data)) for data in datas] if datas else []
    
    @staticmethod
    def update_config(config_id: int, **kwargs) -> tuple[bool, str]:
        """
        更新场景配置
        
        Args:
            config_id: 配置ID
            **kwargs: 要更新的字段
        
        Returns:
            (success, message)
        """
        # 获取现有配置
        existing = ConfigManager.get_config(config_id)
        if not existing:
            return False, "配置不存在"
        
        # 不允许修改已激活的配置（需要先停用）
        if existing.is_active and kwargs:
            return False, "请先停用该配置后再修改"
        
        # 构建更新字段
        allowed_fields = [
            'config_name', 'fast_station_count', 'slow_station_count',
            'waiting_area_capacity', 'station_queue_mode',
            'station_queue_capacity', 'description'
        ]
        
        update_fields = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if not update_fields:
            return False, "没有可更新的字段"
        
        # 添加更新时间
        update_fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(config_id)
        
        try:
            execute_db(f"""
                UPDATE system_scenario_config
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, values)
            
            return True, "配置更新成功"
            
        except Exception as e:
            return False, f"更新失败: {str(e)}"
    
    @staticmethod
    def delete_config(config_id: int) -> tuple[bool, str]:
        """删除场景配置"""
        config = ConfigManager.get_config(config_id)
        if not config:
            return False, "配置不存在"
        
        if config.is_active:
            return False, "不能删除已激活的配置，请先切换"
        
        try:
            execute_db(
                "DELETE FROM system_scenario_config WHERE id = ?",
                [config_id]
            )
            return True, "配置删除成功"
        except Exception as e:
            return False, f"删除失败: {str(e)}"
    
    @staticmethod
    def activate_config(config_id: int) -> tuple[bool, str]:
        """
        激活指定场景配置
        
        注意：激活新配置时会自动停用其他配置
        """
        config = ConfigManager.get_config(config_id)
        if not config:
            return False, "配置不存在"
        
        if config.is_active:
            return True, "该配置已经是激活状态"
        
        try:
            # 先停用所有配置
            execute_db(
                "UPDATE system_scenario_config SET is_active = 0"
            )
            
            # 激活指定配置
            execute_db(
                "UPDATE system_scenario_config SET is_active = 1 WHERE id = ?",
                [config_id]
            )
            
            return True, f"配置 '{config.config_name}' 已激活"
            
        except Exception as e:
            return False, f"激活失败: {str(e)}"
    
    @staticmethod
    def initialize_stations_for_scenario(config_id: int) -> tuple[bool, str]:
        """
        根据场景配置初始化充电桩
        
        根据配置中的 fast_station_count 和 slow_station_count
        动态生成充电桩记录
        """
        config = ConfigManager.get_config(config_id)
        if not config:
            return False, "配置不存在"
        
        try:
            # 获取现有桩数量
            existing = query_db(
                "SELECT COUNT(*) as cnt FROM charging_station WHERE scenario_id = ?",
                [config_id],
                one=True
            )
            
            if existing['cnt'] > 0:
                return False, "该场景已初始化过充电桩"
            
            # 生成快充桩
            for i in range(1, config.fast_station_count + 1):
                execute_db("""
                    INSERT INTO charging_station (
                        station_code, station_type, power_kw, scenario_id
                    ) VALUES (?, ?, ?, ?)
                """, [
                    f"FAST_{i:02d}",
                    ChargeMode.FAST.value,
                    30.0,  # 快充功率30kW
                    config_id
                ])
            
            # 生成慢充桩
            for i in range(1, config.slow_station_count + 1):
                execute_db("""
                    INSERT INTO charging_station (
                        station_code, station_type, power_kw, scenario_id
                    ) VALUES (?, ?, ?, ?)
                """, [
                    f"SLOW_{i:02d}",
                    ChargeMode.SLOW.value,
                    7.0,  # 慢充功率7kW
                    config_id
                ])
            
            total = config.fast_station_count + config.slow_station_count
            return True, f"成功初始化 {total} 个充电桩（{config.fast_station_count}快/{config.slow_station_count}慢）"
            
        except Exception as e:
            return False, f"初始化失败: {str(e)}"
    
    @staticmethod
    def get_scenario_summary(config_id: int) -> Dict[str, Any]:
        """获取场景配置摘要信息"""
        config = ConfigManager.get_config(config_id)
        if not config:
            return None
        
        # 统计充电桩状态
        station_stats = query_db("""
            SELECT 
                status,
                COUNT(*) as count
            FROM charging_station
            WHERE scenario_id = ?
            GROUP BY status
        """, [config_id])
        
        # 统计等待池人数
        waiting_stats = query_db("""
            SELECT 
                waiting_pool_type,
                COUNT(*) as count
            FROM charge_request
            WHERE scenario_id = ? AND status = 'WAITING'
            GROUP BY waiting_pool_type
        """, [config_id])
        
        return {
            'config': config.to_dict(),
            'station_status': {s['status']: s['count'] for s in station_stats} if station_stats else {},
            'waiting_pool': {w['waiting_pool_type']: w['count'] for w in waiting_stats} if waiting_stats else {}
        }


# 便捷函数
def get_active_scenario() -> Optional[ScenarioConfig]:
    """获取当前激活的场景配置（便捷函数）"""
    return ConfigManager.get_active_config()


def can_accept_request(charge_mode: ChargeMode) -> tuple[bool, str]:
    """
    检查是否可以接受新请求
    
    检查等待区是否已满
    """
    config = get_active_scenario()
    if not config:
        return False, "没有激活的场景配置"
    
    # 统计当前等待人数
    waiting_count = query_db("""
        SELECT COUNT(*) as cnt 
        FROM charge_request 
        WHERE scenario_id = ? AND status = 'WAITING'
    """, [config.id], one=True)
    
    if waiting_count['cnt'] >= config.waiting_area_capacity:
        return False, f"等待区已满（{waiting_count['cnt']}/{config.waiting_area_capacity}）"
    
    return True, "可以接收请求"
