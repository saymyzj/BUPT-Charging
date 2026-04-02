"""
等待池管理模块
管理快充和慢充两个中央等待池
支持共享容量限制和动态分配

作者：成员 B
日期：2026-04-02
"""

from app.utils.db import query_db, execute_db
from app.enums import WaitingPoolType, ChargeMode, RequestStatus
from app.utils.helpers import get_active_scenario
from typing import List, Dict, Any, Optional
from datetime import datetime


class WaitingPoolManager:
    """
    等待池管理器
    
    管理两个中央等待池：
    - FAST_POOL: 快充等待池
    - SLOW_POOL: 慢充等待池
    
    特点：
    1. 两个池共享总容量（waiting_area_capacity）
    2. 请求按 charge_mode 进入对应池
    3. 支持动态优先级计算
    4. 支持容量限制检查
    """
    
    def __init__(self):
        """初始化等待池管理器"""
        pass
    
    def get_pool_status(self) -> Dict[str, Any]:
        """
        获取当前等待池状态
        
        Returns:
            {
                'fast_pool': {
                    'count': 人数,
                    'requests': [请求列表]
                },
                'slow_pool': {
                    'count': 人数,
                    'requests': [请求列表]
                },
                'total_waiting': 总等待人数,
                'capacity': 总容量,
                'available_slots': 剩余可用位置
            }
        """
        config = get_active_scenario()
        if not config:
            return None
        
        # 查询快充池
        fast_requests = query_db("""
            SELECT 
                cr.id, cr.request_id, cr.user_id, cr.charge_mode,
                cr.request_energy, cr.submit_time, cr.priority_score,
                cr.estimated_wait_seconds, cr.estimated_start_time
            FROM charge_request cr
            WHERE cr.scenario_id = ? 
              AND cr.waiting_pool_type = ?
              AND cr.status = ?
            ORDER BY cr.priority_score DESC, cr.submit_time ASC
        """, [config.id, WaitingPoolType.FAST_POOL.value, RequestStatus.WAITING.value])
        
        # 查询慢充池
        slow_requests = query_db("""
            SELECT 
                cr.id, cr.request_id, cr.user_id, cr.charge_mode,
                cr.request_energy, cr.submit_time, cr.priority_score,
                cr.estimated_wait_seconds, cr.estimated_start_time
            FROM charge_request cr
            WHERE cr.scenario_id = ? 
              AND cr.waiting_pool_type = ?
              AND cr.status = ?
            ORDER BY cr.priority_score DESC, cr.submit_time ASC
        """, [config.id, WaitingPoolType.SLOW_POOL.value, RequestStatus.WAITING.value])
        
        fast_count = len(fast_requests) if fast_requests else 0
        slow_count = len(slow_requests) if slow_requests else 0
        total = fast_count + slow_count
        
        return {
            'fast_pool': {
                'count': fast_count,
                'requests': [dict(r) for r in fast_requests] if fast_requests else []
            },
            'slow_pool': {
                'count': slow_count,
                'requests': [dict(r) for r in slow_requests] if slow_requests else []
            },
            'total_waiting': total,
            'capacity': config.waiting_area_capacity,
            'available_slots': max(0, config.waiting_area_capacity - total)
        }
    
    def can_accept_request(self, charge_mode: ChargeMode) -> tuple[bool, str]:
        """
        检查是否可以接受新请求
        
        Args:
            charge_mode: 充电模式
        
        Returns:
            (是否可以接收, 原因说明)
        """
        config = get_active_scenario()
        if not config:
            return False, "没有激活的场景配置"
        
        status = self.get_pool_status()
        if not status:
            return False, "无法获取等待池状态"
        
        # 检查总容量
        if status['total_waiting'] >= config.waiting_area_capacity:
            return False, f"等待区已满（{status['total_waiting']}/{config.waiting_area_capacity}）"
        
        return True, f"可以接收请求（当前等待: {status['total_waiting']}/{config.waiting_area_capacity}）"
    
    def add_to_pool(self, request_id: int, charge_mode: ChargeMode) -> tuple[bool, str]:
        """
        将请求添加到等待池
        
        Args:
            request_id: 请求ID（数据库ID）
            charge_mode: 充电模式
        
        Returns:
            (是否成功, 消息)
        """
        # 检查容量
        can_accept, message = self.can_accept_request(charge_mode)
        if not can_accept:
            return False, message
        
        # 确定池类型
        pool_type = (
            WaitingPoolType.FAST_POOL if charge_mode == ChargeMode.FAST 
            else WaitingPoolType.SLOW_POOL
        )
        
        config = get_active_scenario()
        
        try:
            # 更新请求状态
            execute_db("""
                UPDATE charge_request
                SET 
                    status = ?,
                    waiting_pool_type = ?,
                    scenario_id = ?,
                    updated_at = ?
                WHERE id = ?
            """, [
                RequestStatus.WAITING.value,
                pool_type.value,
                config.id if config else None,
                datetime.now().isoformat(),
                request_id
            ])
            
            return True, f"请求已加入 {pool_type.value}"
            
        except Exception as e:
            return False, f"加入等待池失败: {str(e)}"
    
    def remove_from_pool(self, request_id: int) -> tuple[bool, str]:
        """
        从等待池中移除请求
        
        Args:
            request_id: 请求ID
        
        Returns:
            (是否成功, 消息)
        """
        try:
            execute_db("""
                UPDATE charge_request
                SET 
                    waiting_pool_type = NULL,
                    updated_at = ?
                WHERE id = ? AND status = ?
            """, [
                datetime.now().isoformat(),
                request_id,
                RequestStatus.WAITING.value
            ])
            
            return True, "请求已从等待池移除"
            
        except Exception as e:
            return False, f"移除失败: {str(e)}"
    
    def get_next_request(self, pool_type: WaitingPoolType) -> Optional[Dict[str, Any]]:
        """
        获取指定池中优先级最高的请求
        
        用于调度器选择下一个服务的用户
        
        Args:
            pool_type: 等待池类型
        
        Returns:
            请求信息或None
        """
        config = get_active_scenario()
        if not config:
            return None
        
        request = query_db("""
            SELECT 
                cr.id, cr.request_id, cr.user_id, cr.charge_mode,
                cr.request_energy, cr.submit_time, cr.priority_score,
                cr.estimated_wait_seconds, cr.estimated_start_time,
                cr.estimated_finish_time
            FROM charge_request cr
            WHERE cr.scenario_id = ? 
              AND cr.waiting_pool_type = ?
              AND cr.status = ?
            ORDER BY cr.priority_score DESC, cr.submit_time ASC
            LIMIT 1
        """, [config.id, pool_type.value, RequestStatus.WAITING.value], one=True)
        
        return dict(request) if request else None
    
    def update_priority(self, request_id: int, priority_score: float) -> bool:
        """
        更新请求的优先级分数
        
        Args:
            request_id: 请求ID
            priority_score: 新的优先级分数
        
        Returns:
            是否成功
        """
        try:
            execute_db("""
                UPDATE charge_request
                SET priority_score = ?, updated_at = ?
                WHERE id = ? AND status = ?
            """, [
                priority_score,
                datetime.now().isoformat(),
                request_id,
                RequestStatus.WAITING.value
            ])
            return True
        except Exception:
            return False
    
    def get_request_position(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        获取请求在队列中的位置
        
        Args:
            request_id: 请求ID
        
        Returns:
            位置信息或None
        """
        config = get_active_scenario()
        if not config:
            return None
        
        # 获取请求信息
        request = query_db("""
            SELECT waiting_pool_type, priority_score, submit_time
            FROM charge_request
            WHERE id = ? AND scenario_id = ? AND status = ?
        """, [request_id, config.id, RequestStatus.WAITING.value], one=True)
        
        if not request:
            return None
        
        # 计算前面有多少人
        ahead = query_db("""
            SELECT COUNT(*) as cnt
            FROM charge_request
            WHERE scenario_id = ? 
              AND waiting_pool_type = ?
              AND status = ?
              AND (
                  priority_score > ?
                  OR (priority_score = ? AND submit_time < ?)
              )
        """, [
            config.id,
            request['waiting_pool_type'],
            RequestStatus.WAITING.value,
            request['priority_score'],
            request['priority_score'],
            request['submit_time']
        ], one=True)
        
        # 计算总人数
        total = query_db("""
            SELECT COUNT(*) as cnt
            FROM charge_request
            WHERE scenario_id = ? 
              AND waiting_pool_type = ?
              AND status = ?
        """, [config.id, request['waiting_pool_type'], RequestStatus.WAITING.value], one=True)
        
        return {
            'pool_type': request['waiting_pool_type'],
            'position': ahead['cnt'] + 1,
            'total_in_pool': total['cnt'],
            'priority_score': request['priority_score']
        }
    
    def clear_pool(self) -> tuple[bool, str]:
        """
        清空等待池（用于场景重置）
        
        注意：只清空状态为 WAITING 的请求
        """
        config = get_active_scenario()
        if not config:
            return False, "没有激活的场景配置"
        
        try:
            # 将所有 WAITING 状态的请求标记为 CANCELLED
            execute_db("""
                UPDATE charge_request
                SET 
                    status = ?,
                    waiting_pool_type = NULL,
                    updated_at = ?
                WHERE scenario_id = ? AND status = ?
            """, [
                RequestStatus.CANCELLED.value,
                datetime.now().isoformat(),
                config.id,
                RequestStatus.WAITING.value
            ])
            
            return True, "等待池已清空"
            
        except Exception as e:
            return False, f"清空失败: {str(e)}"
    
    def get_pool_statistics(self) -> Dict[str, Any]:
        """
        获取等待池统计信息
        
        Returns:
            统计信息字典
        """
        config = get_active_scenario()
        if not config:
            return None
        
        # 基础统计
        status = self.get_pool_status()
        
        # 平均等待时间
        avg_wait = query_db("""
            SELECT AVG(estimated_wait_seconds) as avg_wait
            FROM charge_request
            WHERE scenario_id = ? AND status = ?
        """, [config.id, RequestStatus.WAITING.value], one=True)
        
        # 最长等待时间
        max_wait = query_db("""
            SELECT MAX(
                CAST((julianday('now') - julianday(submit_time)) * 24 * 60 * 60 AS INTEGER)
            ) as max_wait
            FROM charge_request
            WHERE scenario_id = ? AND status = ?
        """, [config.id, RequestStatus.WAITING.value], one=True)
        
        return {
            'fast_pool_count': status['fast_pool']['count'],
            'slow_pool_count': status['slow_pool']['count'],
            'total_waiting': status['total_waiting'],
            'capacity': status['capacity'],
            'utilization_rate': status['total_waiting'] / status['capacity'] if status['capacity'] > 0 else 0,
            'avg_estimated_wait': avg_wait['avg_wait'] if avg_wait['avg_wait'] else 0,
            'max_actual_wait_seconds': max_wait['max_wait'] if max_wait['max_wait'] else 0
        }


# 便捷函数
def get_waiting_pool_manager() -> WaitingPoolManager:
    """获取等待池管理器实例（便捷函数）"""
    return WaitingPoolManager()


def check_can_accept(charge_mode: ChargeMode) -> tuple[bool, str]:
    """检查是否可以接受请求（便捷函数）"""
    manager = get_waiting_pool_manager()
    return manager.can_accept_request(charge_mode)
