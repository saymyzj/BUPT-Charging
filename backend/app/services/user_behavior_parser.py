"""
用户行为模拟参数解析器模块
解析批量模拟中每个用户的行为参数
定义用户行为的时间线和事件序列

作者：成员 B
日期：2026-04-02
"""

from app.enums import ChargeMode
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta


class UserBehaviorConfig:
    """
    用户行为配置数据类
    
    定义单个用户在批量模拟中的完整行为
    """
    
    def __init__(self, data: Dict[str, Any]):
        # 基本信息
        self.user_id = data.get('user_id')
        self.request_time = data.get('request_time')  # ISO 8601 格式
        self.charge_mode = ChargeMode(data.get('charge_mode')) if data.get('charge_mode') else None
        self.request_energy = data.get('request_energy', 20.0)
        
        # 取消行为
        self.cancel_queue = data.get('cancel_queue', False)
        self.cancel_time = data.get('cancel_time')  # 取消时间（绝对时间或相对时间）
        
        # 确认到场行为
        self.confirm_arrival_delay_seconds = data.get('confirm_arrival_delay_seconds', 0)
        # 如果为 None 或负数，表示不会确认（过号）
        self.will_confirm_arrival = self.confirm_arrival_delay_seconds is not None and \
                                     self.confirm_arrival_delay_seconds >= 0
        
        # 中断充电行为
        self.interrupt_charge = data.get('interrupt_charge', False)
        self.interrupt_time = data.get('interrupt_time')  # 中断时间
        
        # 挪车行为
        self.leave_delay_seconds = data.get('leave_delay_seconds', 0)
        # 如果为 None 或负数，表示不会主动挪车（超时）
        self.will_leave = self.leave_delay_seconds is not None and \
                          self.leave_delay_seconds >= 0
    
    def validate(self) -> Tuple[bool, str]:
        """验证用户行为配置"""
        if not self.user_id:
            return False, "user_id 不能为空"
        
        if not self.request_time:
            return False, "request_time 不能为空"
        
        # 验证时间格式
        try:
            datetime.fromisoformat(self.request_time.replace('Z', '+00:00'))
        except ValueError:
            return False, f"无效的 request_time 格式: {self.request_time}"
        
        if not self.charge_mode:
            return False, "charge_mode 不能为空"
        
        if self.request_energy <= 0:
            return False, "request_energy 必须大于0"
        
        # 验证取消时间
        if self.cancel_queue and self.cancel_time:
            try:
                datetime.fromisoformat(self.cancel_time.replace('Z', '+00:00'))
            except ValueError:
                return False, f"无效的 cancel_time 格式: {self.cancel_time}"
        
        # 验证中断时间
        if self.interrupt_charge and self.interrupt_time:
            try:
                datetime.fromisoformat(self.interrupt_time.replace('Z', '+00:00'))
            except ValueError:
                return False, f"无效的 interrupt_time 格式: {self.interrupt_time}"
        
        return True, "验证通过"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'request_time': self.request_time,
            'charge_mode': self.charge_mode.value if self.charge_mode else None,
            'request_energy': self.request_energy,
            'cancel_queue': self.cancel_queue,
            'cancel_time': self.cancel_time,
            'confirm_arrival_delay_seconds': self.confirm_arrival_delay_seconds,
            'will_confirm_arrival': self.will_confirm_arrival,
            'interrupt_charge': self.interrupt_charge,
            'interrupt_time': self.interrupt_time,
            'leave_delay_seconds': self.leave_delay_seconds,
            'will_leave': self.will_leave
        }
    
    def generate_event_timeline(self) -> List[Dict[str, Any]]:
        """
        生成用户事件时间线
        
        返回按时间排序的事件列表
        """
        events = []
        request_dt = datetime.fromisoformat(self.request_time.replace('Z', '+00:00'))
        
        # 1. 请求提交事件
        events.append({
            'time': request_dt,
            'type': 'REQUEST_SUBMIT',
            'data': {
                'user_id': self.user_id,
                'charge_mode': self.charge_mode.value if self.charge_mode else None,
                'request_energy': self.request_energy
            }
        })
        
        # 2. 取消事件（如果配置）
        if self.cancel_queue:
            if self.cancel_time:
                cancel_dt = datetime.fromisoformat(self.cancel_time.replace('Z', '+00:00'))
            else:
                # 默认在提交后5分钟取消
                cancel_dt = request_dt + timedelta(minutes=5)
            
            events.append({
                'time': cancel_dt,
                'type': 'CANCEL_QUEUE',
                'data': {'user_id': self.user_id}
            })
            
            # 取消后不再产生其他事件
            return sorted(events, key=lambda x: x['time'])
        
        # 3. 叫号确认事件（如果被叫号）
        # 注意：实际时间取决于调度，这里只是预期行为
        if self.will_confirm_arrival:
            confirm_dt = request_dt + timedelta(seconds=self.confirm_arrival_delay_seconds)
            events.append({
                'time': confirm_dt,
                'type': 'CONFIRM_ARRIVAL',
                'data': {
                    'user_id': self.user_id,
                    'delay_seconds': self.confirm_arrival_delay_seconds
                }
            })
        else:
            # 过号事件
            no_show_dt = request_dt + timedelta(minutes=10)  # 假设10分钟后过号
            events.append({
                'time': no_show_dt,
                'type': 'NO_SHOW',
                'data': {'user_id': self.user_id}
            })
            return sorted(events, key=lambda x: x['time'])
        
        # 4. 充电中断事件（如果配置）
        if self.interrupt_charge:
            if self.interrupt_time:
                interrupt_dt = datetime.fromisoformat(self.interrupt_time.replace('Z', '+00:00'))
            else:
                # 默认在确认后10分钟中断
                interrupt_dt = confirm_dt + timedelta(minutes=10)
            
            events.append({
                'time': interrupt_dt,
                'type': 'INTERRUPT_CHARGE',
                'data': {'user_id': self.user_id}
            })
            return sorted(events, key=lambda x: x['time'])
        
        # 5. 充电完成和挪车事件
        # 预计充电完成时间（简化计算）
        estimated_charge_minutes = self.request_energy / (30.0 if self.charge_mode == ChargeMode.FAST else 7.0) * 60
        charge_complete_dt = confirm_dt + timedelta(minutes=estimated_charge_minutes)
        
        events.append({
            'time': charge_complete_dt,
            'type': 'CHARGE_COMPLETE',
            'data': {'user_id': self.user_id}
        })
        
        # 挪车事件
        if self.will_leave:
            leave_dt = charge_complete_dt + timedelta(seconds=self.leave_delay_seconds)
            events.append({
                'time': leave_dt,
                'type': 'CONFIRM_LEAVE',
                'data': {
                    'user_id': self.user_id,
                    'delay_seconds': self.leave_delay_seconds
                }
            })
        else:
            # 超时未挪车
            timeout_dt = charge_complete_dt + timedelta(minutes=15)  # 假设15分钟超时
            events.append({
                'time': timeout_dt,
                'type': 'LEAVE_TIMEOUT',
                'data': {'user_id': self.user_id}
            })
        
        return sorted(events, key=lambda x: x['time'])


class UserBehaviorParser:
    """用户行为参数解析器"""
    
    @staticmethod
    def parse_user_config(data: Dict[str, Any]) -> Tuple[bool, str, Optional[UserBehaviorConfig]]:
        """
        解析单个用户配置
        
        Returns:
            (是否成功, 消息, UserBehaviorConfig对象)
        """
        try:
            config = UserBehaviorConfig(data)
            is_valid, message = config.validate()
            
            if not is_valid:
                return False, message, None
            
            return True, "解析成功", config
            
        except Exception as e:
            return False, f"解析失败: {str(e)}", None
    
    @staticmethod
    def parse_users_config(users_data: List[Dict[str, Any]]) -> Tuple[bool, str, List[UserBehaviorConfig]]:
        """
        解析多个用户配置
        
        Returns:
            (是否成功, 消息, UserBehaviorConfig列表)
        """
        if not isinstance(users_data, list):
            return False, "users 必须是数组", []
        
        configs = []
        errors = []
        
        for i, user_data in enumerate(users_data):
            success, message, config = UserBehaviorParser.parse_user_config(user_data)
            
            if not success:
                errors.append(f"用户[{i}] ({user_data.get('user_id', 'unknown')}): {message}")
            else:
                configs.append(config)
        
        if errors:
            return False, "; ".join(errors), configs
        
        return True, f"成功解析 {len(configs)} 个用户配置", configs
    
    @staticmethod
    def generate_batch_timeline(configs: List[UserBehaviorConfig]) -> List[Dict[str, Any]]:
        """
        生成批量测试的完整时间线
        
        合并所有用户的事件，按时间排序
        """
        all_events = []
        
        for config in configs:
            user_events = config.generate_event_timeline()
            all_events.extend(user_events)
        
        # 按时间排序
        return sorted(all_events, key=lambda x: x['time'])
    
    @staticmethod
    def categorize_users_by_behavior(configs: List[UserBehaviorConfig]) -> Dict[str, List[str]]:
        """
        按行为类型分类用户
        
        Returns:
            {
                'normal': [正常完成用户ID列表],
                'cancel': [取消用户ID列表],
                'interrupt': [中断用户ID列表],
                'no_show': [过号用户ID列表],
                'timeout': [超时未挪车用户ID列表]
            }
        """
        categories = {
            'normal': [],
            'cancel': [],
            'interrupt': [],
            'no_show': [],
            'timeout': []
        }
        
        for config in configs:
            user_id = config.user_id
            
            if config.cancel_queue:
                categories['cancel'].append(user_id)
            elif not config.will_confirm_arrival:
                categories['no_show'].append(user_id)
            elif config.interrupt_charge:
                categories['interrupt'].append(user_id)
            elif not config.will_leave:
                categories['timeout'].append(user_id)
            else:
                categories['normal'].append(user_id)
        
        return categories


# 便捷函数
def parse_user(data: Dict[str, Any]) -> Tuple[bool, str, Optional[UserBehaviorConfig]]:
    """解析单个用户的便捷函数"""
    return UserBehaviorParser.parse_user_config(data)


def parse_users(users_data: List[Dict[str, Any]]) -> Tuple[bool, str, List[UserBehaviorConfig]]:
    """解析多个用户的便捷函数"""
    return UserBehaviorParser.parse_users_config(users_data)


def generate_timeline(configs: List[UserBehaviorConfig]) -> List[Dict[str, Any]]:
    """生成时间线的便捷函数"""
    return UserBehaviorParser.generate_batch_timeline(configs)


def categorize_users(configs: List[UserBehaviorConfig]) -> Dict[str, List[str]]:
    """分类用户的便捷函数"""
    return UserBehaviorParser.categorize_users_by_behavior(configs)
