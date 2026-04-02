"""
场景参数解析器模块
解析批量模拟请求中的场景参数
支持从自然语言描述映射到结构化输入

作者：成员 B
日期：2026-04-02
"""

from app.enums import StationQueueMode, ChargeMode, StationStatus
from typing import Dict, Any, List, Optional, Tuple
import re


class ScenarioParser:
    """
    场景参数解析器
    
    将各种输入格式解析为标准场景配置
    """
    
    # 默认场景参数
    DEFAULT_FAST_COUNT = 2
    DEFAULT_SLOW_COUNT = 3
    DEFAULT_WAITING_CAPACITY = 6
    DEFAULT_QUEUE_CAPACITY = 3
    
    @staticmethod
    def parse_scenario_config(data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        解析场景配置
        
        Args:
            data: 原始场景配置数据
        
        Returns:
            (是否成功, 消息, 解析后的配置)
        """
        if not data:
            return False, "场景配置不能为空", {}
        
        try:
            # 提取基本参数
            config = {
                'config_name': data.get('config_name', '批量测试场景'),
                'fast_station_count': data.get('fast_station_count', ScenarioParser.DEFAULT_FAST_COUNT),
                'slow_station_count': data.get('slow_station_count', ScenarioParser.DEFAULT_SLOW_COUNT),
                'waiting_area_capacity': data.get('waiting_area_capacity', ScenarioParser.DEFAULT_WAITING_CAPACITY),
                'station_queue_mode': data.get('station_queue_mode', 'UNIFORM_CAPACITY'),
                'station_queue_capacity': data.get('station_queue_capacity', ScenarioParser.DEFAULT_QUEUE_CAPACITY),
                'station_snapshots': data.get('station_snapshots', [])
            }
            
            # 验证基本参数
            if config['fast_station_count'] < 0 or config['slow_station_count'] < 0:
                return False, "充电桩数量不能为负数", {}
            
            if config['waiting_area_capacity'] < 0:
                return False, "等待区容量不能为负数", {}
            
            # 验证队列模式
            if config['station_queue_mode'] not in [m.value for m in StationQueueMode]:
                return False, f"无效的队列模式: {config['station_queue_mode']}", {}
            
            # 根据模式解析特定参数
            if config['station_queue_mode'] == StationQueueMode.STATION_SNAPSHOT.value:
                success, message, snapshots = ScenarioParser._parse_station_snapshots(
                    config['station_snapshots']
                )
                if not success:
                    return False, message, {}
                config['station_snapshots'] = snapshots
            
            return True, "解析成功", config
            
        except Exception as e:
            return False, f"解析失败: {str(e)}", {}
    
    @staticmethod
    def _parse_station_snapshots(snapshots_data: List[Dict[str, Any]]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        解析桩级快照数据
        
        Args:
            snapshots_data: 快照数据列表
        
        Returns:
            (是否成功, 消息, 解析后的快照列表)
        """
        if not snapshots_data:
            return False, "STATION_SNAPSHOT 模式下需要提供 station_snapshots", []
        
        parsed_snapshots = []
        
        for i, snapshot in enumerate(snapshots_data):
            # 验证必填字段
            if 'station_code' not in snapshot:
                return False, f"快照[{i}]: station_code 不能为空", []
            
            if 'station_type' not in snapshot:
                return False, f"快照[{i}]: station_type 不能为空", []
            
            # 解析并验证
            parsed = {
                'station_code': snapshot['station_code'],
                'station_type': snapshot['station_type'],
                'status': snapshot.get('status', 'IDLE'),
                'current_user_remaining_seconds': snapshot.get('current_user_remaining_seconds'),
                'queue_length': snapshot.get('queue_length', 0)
            }
            
            # 验证桩类型
            if parsed['station_type'] not in [ChargeMode.FAST.value, ChargeMode.SLOW.value]:
                return False, f"快照[{i}]: 无效的桩类型 {parsed['station_type']}", []
            
            # 验证状态
            if parsed['status'] not in [s.value for s in StationStatus]:
                return False, f"快照[{i}]: 无效的桩状态 {parsed['status']}", []
            
            # 验证排队人数
            if parsed['queue_length'] < 0:
                return False, f"快照[{i}]: 排队人数不能为负数", []
            
            parsed_snapshots.append(parsed)
        
        return True, "解析成功", parsed_snapshots
    
    @staticmethod
    def parse_from_natural_language(text: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        从自然语言描述解析场景配置
        
        示例输入：
        "系统有2个快充桩和3个慢充桩，等待区容量为6，每桩最多排3人"
        "FAST_01正在充电，剩余600秒，有2人排队；FAST_02空闲"
        
        Args:
            text: 自然语言描述
        
        Returns:
            (是否成功, 消息, 解析后的配置)
        """
        try:
            config = {
                'config_name': '从自然语言解析的场景',
                'station_queue_mode': 'UNIFORM_CAPACITY'
            }
            
            # 解析充电桩数量
            fast_match = re.search(r'(\d+)\s*个?\s*快', text)
            slow_match = re.search(r'(\d+)\s*个?\s*慢', text)
            
            if fast_match:
                config['fast_station_count'] = int(fast_match.group(1))
            else:
                config['fast_station_count'] = ScenarioParser.DEFAULT_FAST_COUNT
            
            if slow_match:
                config['slow_station_count'] = int(slow_match.group(1))
            else:
                config['slow_station_count'] = ScenarioParser.DEFAULT_SLOW_COUNT
            
            # 解析等待区容量
            capacity_match = re.search(r'等待区容量\s*为?\s*(\d+)', text)
            if capacity_match:
                config['waiting_area_capacity'] = int(capacity_match.group(1))
            else:
                config['waiting_area_capacity'] = ScenarioParser.DEFAULT_WAITING_CAPACITY
            
            # 解析每桩容量
            queue_capacity_match = re.search(r'每桩最多排\s*(\d+)\s*人', text)
            if queue_capacity_match:
                config['station_queue_capacity'] = int(queue_capacity_match.group(1))
            else:
                config['station_queue_capacity'] = ScenarioParser.DEFAULT_QUEUE_CAPACITY
            
            # 检查是否包含桩级状态描述（判断是否为快照模式）
            if any(keyword in text for keyword in ['正在充电', '空闲', '故障', '排队']):
                # 尝试解析快照模式
                success, message, snapshots = ScenarioParser._parse_snapshots_from_text(text)
                if success and snapshots:
                    config['station_queue_mode'] = 'STATION_SNAPSHOT'
                    config['station_snapshots'] = snapshots
            
            return True, "解析成功", config
            
        except Exception as e:
            return False, f"自然语言解析失败: {str(e)}", {}
    
    @staticmethod
    def _parse_snapshots_from_text(text: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """从文本中解析桩级快照"""
        snapshots = []
        
        # 匹配模式：桩编号 + 状态 + 可选参数
        # 示例："FAST_01正在充电，剩余600秒，有2人排队"
        pattern = r'(FAST_\d+|SLOW_\d+)\s*(正在充电|空闲|故障|待挪车)' \
                  r'(?:，?\s*剩余\s*(\d+)\s*秒)?' \
                  r'(?:，?\s*有\s*(\d+)\s*人排队)?'
        
        matches = re.finditer(pattern, text)
        
        for match in matches:
            station_code = match.group(1)
            status_text = match.group(2)
            remaining_seconds = match.group(3)
            queue_length = match.group(4)
            
            # 状态映射
            status_map = {
                '正在充电': 'CHARGING',
                '空闲': 'IDLE',
                '故障': 'FAULT',
                '待挪车': 'WAITING_TO_LEAVE'
            }
            
            # 确定桩类型
            station_type = 'FAST' if station_code.startswith('FAST') else 'SLOW'
            
            snapshot = {
                'station_code': station_code,
                'station_type': station_type,
                'status': status_map.get(status_text, 'IDLE'),
                'current_user_remaining_seconds': int(remaining_seconds) if remaining_seconds else None,
                'queue_length': int(queue_length) if queue_length else 0
            }
            
            snapshots.append(snapshot)
        
        if snapshots:
            return True, f"解析到 {len(snapshots)} 个桩快照", snapshots
        else:
            return False, "未找到桩级状态描述", []
    
    @staticmethod
    def generate_scenario_description(config: Dict[str, Any]) -> str:
        """
        生成场景配置的自然语言描述
        
        Args:
            config: 场景配置
        
        Returns:
            自然语言描述
        """
        mode = config.get('station_queue_mode', 'UNIFORM_CAPACITY')
        
        if mode == 'UNIFORM_CAPACITY':
            return (
                f"系统有{config.get('fast_station_count', 2)}个快充桩和"
                f"{config.get('slow_station_count', 3)}个慢充桩，"
                f"等待区容量为{config.get('waiting_area_capacity', 6)}，"
                f"每桩最多排{config.get('station_queue_capacity', 3)}人"
            )
        else:
            snapshots = config.get('station_snapshots', [])
            if not snapshots:
                return "桩级快照模式，但未提供具体快照数据"
            
            descriptions = []
            for snapshot in snapshots:
                status_desc = {
                    'IDLE': '空闲',
                    'CHARGING': f"正在充电（剩余{snapshot.get('current_user_remaining_seconds', 0)}秒）",
                    'FAULT': '故障',
                    'WAITING_TO_LEAVE': '待挪车'
                }.get(snapshot['status'], snapshot['status'])
                
                queue_desc = f"，有{snapshot.get('queue_length', 0)}人排队" if snapshot.get('queue_length', 0) > 0 else ""
                
                descriptions.append(f"{snapshot['station_code']}{status_desc}{queue_desc}")
            
            return "；".join(descriptions)


# 便捷函数
def parse_scenario(data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """解析场景配置的便捷函数"""
    return ScenarioParser.parse_scenario_config(data)


def parse_from_text(text: str) -> Tuple[bool, str, Dict[str, Any]]:
    """从自然语言解析的便捷函数"""
    return ScenarioParser.parse_from_natural_language(text)


def generate_description(config: Dict[str, Any]) -> str:
    """生成场景描述的便捷函数"""
    return ScenarioParser.generate_scenario_description(config)
