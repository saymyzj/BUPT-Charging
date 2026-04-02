"""
场景适配器模块
将外部验收输入转换为内部中央等待池状态

兼容两种队列长度解释：
1. 统一容量模式 (UNIFORM_CAPACITY): 每个桩有相同的排队容量上限
2. 桩级快照模式 (STATION_SNAPSHOT): 每个桩有独立的初始状态

作者：成员 B
日期：2026-04-02
版本：V1.0
"""

from app.utils.db import query_db, execute_db
from app.enums import (
    StationQueueMode, StationStatus, ChargeMode,
    WaitingPoolType, RequestStatus
)
from app.services.config_manager import ConfigManager
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


class StationSnapshot:
    """充电桩状态快照数据类"""
    
    def __init__(self, data: Dict[str, Any]):
        self.station_code = data.get('station_code')
        self.station_type = data.get('station_type')  # FAST / SLOW
        self.status = data.get('status', 'IDLE')  # IDLE / CHARGING / WAITING_TO_LEAVE / FAULT
        self.current_user_remaining_seconds = data.get('current_user_remaining_seconds')
        self.queue_length = data.get('queue_length', 0)
    
    def validate(self) -> Tuple[bool, str]:
        """验证快照数据有效性"""
        if not self.station_code:
            return False, "桩编号不能为空"
        
        if self.station_type not in [ChargeMode.FAST.value, ChargeMode.SLOW.value]:
            return False, f"无效的桩类型: {self.station_type}"
        
        if self.status not in [s.value for s in StationStatus]:
            return False, f"无效的桩状态: {self.status}"
        
        if self.queue_length < 0:
            return False, "排队人数不能为负数"
        
        return True, "验证通过"


class ScenarioAdapter:
    """
    场景适配器
    
    将外部验收输入转换为内部状态：
    - 充电桩初始状态 status(s)
    - 各桩的初始最早可用时间 available_time(s)
    - 初始待服务请求集合
    """
    
    def __init__(self):
        """初始化场景适配器"""
        pass
    
    def adapt_scenario(self, scenario_config: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        适配场景配置
        
        根据 scenario_config 中的 station_queue_mode
        自动选择适配方式
        
        Args:
            scenario_config: 场景配置字典
                {
                    'config_name': str,
                    'fast_station_count': int,
                    'slow_station_count': int,
                    'waiting_area_capacity': int,
                    'station_queue_mode': 'UNIFORM_CAPACITY' | 'STATION_SNAPSHOT',
                    'station_queue_capacity': int,  # 统一容量模式用
                    'station_snapshots': List[dict]  # 快照模式用
                }
        
        Returns:
            (是否成功, 消息, 场景配置ID)
        """
        mode = scenario_config.get('station_queue_mode', 'UNIFORM_CAPACITY')
        
        if mode == StationQueueMode.UNIFORM_CAPACITY.value:
            return self._adapt_uniform_capacity(scenario_config)
        elif mode == StationQueueMode.STATION_SNAPSHOT.value:
            return self._adapt_station_snapshot(scenario_config)
        else:
            return False, f"无效的队列模式: {mode}", -1
    
    def _adapt_uniform_capacity(self, config: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        统一容量模式适配
        
        将统一容量参数转换为内部状态：
        - 每个桩都有相同的排队容量上限
        - 初始状态：所有桩为 IDLE
        - 初始可用时间：当前时间
        
        Args:
            config: 场景配置
        
        Returns:
            (是否成功, 消息, 场景配置ID)
        """
        try:
            # 1. 创建场景配置记录
            success, config_id, message = ConfigManager.create_config(
                config_name=config.get('config_name', '统一容量场景'),
                fast_station_count=config['fast_station_count'],
                slow_station_count=config['slow_station_count'],
                waiting_area_capacity=config['waiting_area_capacity'],
                station_queue_mode=StationQueueMode.UNIFORM_CAPACITY.value,
                station_queue_capacity=config.get('station_queue_capacity', 3),
                description=f"统一容量模式：每桩容量上限{config.get('station_queue_capacity', 3)}"
            )
            
            if not success:
                return False, message, -1
            
            # 2. 初始化充电桩
            success, message = ConfigManager.initialize_stations_for_scenario(config_id)
            if not success:
                # 回滚：删除配置
                ConfigManager.delete_config(config_id)
                return False, message, -1
            
            # 3. 设置统一容量参数到每个桩
            queue_capacity = config.get('station_queue_capacity', 3)
            execute_db("""
                UPDATE charging_station
                SET initial_queue_length = 0,
                    initial_status = ?,
                    available_time = ?
                WHERE scenario_id = ?
            """, [
                StationStatus.IDLE.value,
                datetime.now().isoformat(),
                config_id
            ])
            
            # 4. 激活该场景
            ConfigManager.activate_config(config_id)
            
            return True, f"统一容量场景适配成功（ID: {config_id}）", config_id
            
        except Exception as e:
            return False, f"统一容量适配失败: {str(e)}", -1
    
    def _adapt_station_snapshot(self, config: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        桩级快照模式适配
        
        将桩级初始状态快照转换为内部状态：
        - 解析每个桩的初始状态
        - 计算初始最早可用时间
        - 生成初始待服务请求
        
        Args:
            config: 场景配置，包含 station_snapshots
        
        Returns:
            (是否成功, 消息, 场景配置ID)
        """
        try:
            snapshots = config.get('station_snapshots', [])
            
            # 1. 验证快照数据
            validated_snapshots = []
            for snapshot_data in snapshots:
                snapshot = StationSnapshot(snapshot_data)
                is_valid, message = snapshot.validate()
                if not is_valid:
                    return False, f"快照验证失败: {message}", -1
                validated_snapshots.append(snapshot)
            
            # 2. 统计桩数量
            fast_count = sum(1 for s in validated_snapshots if s.station_type == ChargeMode.FAST.value)
            slow_count = sum(1 for s in validated_snapshots if s.station_type == ChargeMode.SLOW.value)
            
            # 3. 创建场景配置
            success, config_id, message = ConfigManager.create_config(
                config_name=config.get('config_name', '桩级快照场景'),
                fast_station_count=fast_count,
                slow_station_count=slow_count,
                waiting_area_capacity=config['waiting_area_capacity'],
                station_queue_mode=StationQueueMode.STATION_SNAPSHOT.value,
                station_queue_capacity=0,  # 快照模式不使用
                description=f"桩级快照模式：共{len(validated_snapshots)}个桩"
            )
            
            if not success:
                return False, message, -1
            
            # 4. 根据快照创建充电桩
            now = datetime.now()
            
            for snapshot in validated_snapshots:
                # 计算可用时间
                available_time = now
                if snapshot.status == StationStatus.CHARGING.value and snapshot.current_user_remaining_seconds:
                    available_time = now + timedelta(seconds=snapshot.current_user_remaining_seconds)
                
                # 插入充电桩记录
                execute_db("""
                    INSERT INTO charging_station (
                        station_code, station_type, power_kw, status,
                        initial_queue_length, initial_status, initial_remaining_seconds,
                        available_time, scenario_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    snapshot.station_code,
                    snapshot.station_type,
                    30.0 if snapshot.station_type == ChargeMode.FAST.value else 7.0,
                    snapshot.status,
                    snapshot.queue_length,
                    snapshot.status,
                    snapshot.current_user_remaining_seconds,
                    available_time.isoformat(),
                    config_id
                ])
            
            # 5. 为排队的用户创建虚拟请求（进入等待池）
            for snapshot in validated_snapshots:
                if snapshot.queue_length > 0:
                    self._create_virtual_requests(
                        config_id, 
                        snapshot.station_code,
                        snapshot.station_type,
                        snapshot.queue_length
                    )
            
            # 6. 激活该场景
            ConfigManager.activate_config(config_id)
            
            return True, f"桩级快照场景适配成功（ID: {config_id}）", config_id
            
        except Exception as e:
            return False, f"桩级快照适配失败: {str(e)}", -1
    
    def _create_virtual_requests(self, scenario_id: int, station_code: str, 
                                 station_type: str, queue_length: int):
        """
        为快照模式中的排队用户创建虚拟请求
        
        这些请求用于占满等待池，模拟初始排队状态
        """
        now = datetime.now()
        pool_type = (
            WaitingPoolType.FAST_POOL if station_type == ChargeMode.FAST.value 
            else WaitingPoolType.SLOW_POOL
        )
        
        for i in range(queue_length):
            # 生成虚拟请求ID
            virtual_request_id = f"VIRTUAL_{station_code}_{i+1:02d}"
            
            execute_db("""
                INSERT INTO charge_request (
                    request_id, charge_mode, request_energy, status,
                    submit_time, waiting_pool_type, scenario_id,
                    estimated_wait_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                virtual_request_id,
                station_type,
                20.0,  # 默认电量
                RequestStatus.WAITING.value,
                (now - timedelta(minutes=i+1)).isoformat(),  # 模拟之前提交
                pool_type.value,
                scenario_id,
                i * 600  # 预计等待时间递增
            ])
    
    def initialize_waiting_pools(self, scenario_id: int) -> Tuple[bool, str]:
        """
        初始化等待池
        
        根据场景配置初始化中央等待池状态
        
        Args:
            scenario_id: 场景配置ID
        
        Returns:
            (是否成功, 消息)
        """
        try:
            config = ConfigManager.get_config(scenario_id)
            if not config:
                return False, "场景配置不存在"
            
            # 清空现有等待池（如果有）
            from app.services.waiting_pool import WaitingPoolManager
            manager = WaitingPoolManager()
            manager.clear_pool()
            
            # 根据模式进行特定初始化
            if config.station_queue_mode == StationQueueMode.UNIFORM_CAPACITY.value:
                return self._init_uniform_capacity_pools(config)
            else:
                return self._init_snapshot_pools(config)
                
        except Exception as e:
            return False, f"初始化等待池失败: {str(e)}"
    
    def _init_uniform_capacity_pools(self, config) -> Tuple[bool, str]:
        """初始化统一容量模式的等待池"""
        # 统一容量模式下，等待池为空，等待新请求进入
        return True, "统一容量模式等待池已初始化（空池）"
    
    def _init_snapshot_pools(self, config) -> Tuple[bool, str]:
        """初始化快照模式的等待池"""
        # 快照模式下，虚拟请求已在适配时创建
        # 这里只需要验证等待池状态
        from app.services.waiting_pool import WaitingPoolManager
        manager = WaitingPoolManager()
        status = manager.get_pool_status()
        
        return True, f"快照模式等待池已初始化（当前等待: {status['total_waiting']}人）"
    
    def convert_to_internal_state(self, scenario_id: int) -> Optional[Dict[str, Any]]:
        """
        将场景配置转换为内部状态表示
        
        供调度器使用
        
        Returns:
            {
                'scenario_id': int,
                'stations': [{
                    'id': int,
                    'code': str,
                    'type': str,
                    'status': str,
                    'available_time': str,
                    'power_kw': float
                }],
                'waiting_pools': {
                    'fast_pool': [请求列表],
                    'slow_pool': [请求列表]
                },
                'capacity': {
                    'total': int,
                    'used': int,
                    'available': int
                }
            }
        """
        try:
            config = ConfigManager.get_config(scenario_id)
            if not config:
                return None
            
            # 获取充电桩状态
            stations = query_db("""
                SELECT id, station_code, station_type, status, 
                       available_time, power_kw
                FROM charging_station
                WHERE scenario_id = ?
            """, [scenario_id])
            
            # 获取等待池状态
            from app.services.waiting_pool import WaitingPoolManager
            manager = WaitingPoolManager()
            pool_status = manager.get_pool_status()
            
            return {
                'scenario_id': scenario_id,
                'scenario_config': config.to_dict(),
                'stations': [dict(s) for s in stations] if stations else [],
                'waiting_pools': {
                    'fast_pool': pool_status['fast_pool'],
                    'slow_pool': pool_status['slow_pool']
                },
                'capacity': {
                    'total': config.waiting_area_capacity,
                    'used': pool_status['total_waiting'],
                    'available': max(0, config.waiting_area_capacity - pool_status['total_waiting'])
                }
            }
            
        except Exception as e:
            print(f"转换内部状态失败: {e}")
            return None
    
    def reset_scenario(self, scenario_id: int) -> Tuple[bool, str]:
        """
        重置场景到初始状态
        
        用于批量测试中的场景重置
        """
        try:
            config = ConfigManager.get_config(scenario_id)
            if not config:
                return False, "场景配置不存在"
            
            # 1. 清空等待池
            from app.services.waiting_pool import WaitingPoolManager
            manager = WaitingPoolManager()
            manager.clear_pool()
            
            # 2. 重置充电桩状态
            if config.station_queue_mode == StationQueueMode.UNIFORM_CAPACITY.value:
                # 统一容量模式：所有桩重置为IDLE
                execute_db("""
                    UPDATE charging_station
                    SET status = ?, current_request_id = NULL, available_time = ?
                    WHERE scenario_id = ?
                """, [StationStatus.IDLE.value, datetime.now().isoformat(), scenario_id])
            else:
                # 快照模式：恢复到初始快照状态
                execute_db("""
                    UPDATE charging_station
                    SET status = initial_status,
                        available_time = CASE 
                            WHEN initial_remaining_seconds IS NOT NULL 
                            THEN datetime('now', '+' || initial_remaining_seconds || ' seconds')
                            ELSE ?
                        END
                    WHERE scenario_id = ?
                """, [datetime.now().isoformat(), scenario_id])
                
                # 重新创建虚拟请求
                snapshots = query_db("""
                    SELECT station_code, station_type, initial_queue_length
                    FROM charging_station
                    WHERE scenario_id = ? AND initial_queue_length > 0
                """, [scenario_id])
                
                for snapshot in snapshots:
                    self._create_virtual_requests(
                        scenario_id,
                        snapshot['station_code'],
                        snapshot['station_type'],
                        snapshot['initial_queue_length']
                    )
            
            # 3. 清理所有非WAITING状态的请求
            execute_db("""
                DELETE FROM charge_request
                WHERE scenario_id = ? AND status != ?
            """, [scenario_id, RequestStatus.WAITING.value])
            
            return True, "场景已重置"
            
        except Exception as e:
            return False, f"重置失败: {str(e)}"


# 便捷函数
def get_scenario_adapter() -> ScenarioAdapter:
    """获取场景适配器实例"""
    return ScenarioAdapter()


def adapt_and_initialize(scenario_config: Dict[str, Any]) -> Tuple[bool, str, int]:
    """
    适配并初始化场景（便捷函数）
    
    Args:
        scenario_config: 场景配置
    
    Returns:
        (是否成功, 消息, 场景配置ID)
    """
    adapter = get_scenario_adapter()
    success, message, config_id = adapter.adapt_scenario(scenario_config)
    
    if success:
        # 初始化等待池
        init_success, init_message = adapter.initialize_waiting_pools(config_id)
        if not init_success:
            return False, f"适配成功但初始化失败: {init_message}", config_id
        
        return True, f"{message}; {init_message}", config_id
    
    return False, message, config_id
