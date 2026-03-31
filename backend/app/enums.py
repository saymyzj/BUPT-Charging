"""
枚举定义模块
定义系统中使用的所有状态枚举值
"""

from enum import Enum


class RequestStatus(Enum):
    """充电请求状态枚举"""
    PENDING = "PENDING"                 # 待处理（初始状态）
    WAITING = "WAITING"                 # 等待中（已入池）
    CALLED = "CALLED"                   # 已叫号
    CONFIRMED = "CONFIRMED"             # 已确认到场
    CHARGING = "CHARGING"               # 充电中
    COMPLETED = "COMPLETED"             # 已完成
    COMPLETED_EARLY = "COMPLETED_EARLY" # 提前完成
    INTERRUPTED = "INTERRUPTED"         # 已中断
    CANCELLED = "CANCELLED"             # 已取消
    NO_SHOW = "NO_SHOW"                 # 过号
    FAULT_REQUEUE = "FAULT_REQUEUE"     # 故障重排


class StationStatus(Enum):
    """充电桩状态枚举"""
    IDLE = "IDLE"                          # 空闲
    RESERVED = "RESERVED"                  # 已预留
    CHARGING = "CHARGING"                  # 充电中
    WAITING_TO_LEAVE = "WAITING_TO_LEAVE"  # 等待挪车
    FAULT = "FAULT"                        # 故障


class ChargeMode(Enum):
    """充电模式枚举"""
    FAST = "FAST"                          # 快充
    SLOW = "SLOW"                          # 慢充


class BillingMode(Enum):
    """计费模式枚举"""
    ENERGY = "ENERGY"                      # 按电量计费
    TIME = "TIME"                          # 按时间计费


class PaymentStatus(Enum):
    """支付状态枚举"""
    UNPAID = "UNPAID"                      # 未支付
    PAID = "PAID"                          # 已支付
    FAILED = "FAILED"                      # 支付失败


class SessionStatus(Enum):
    """充电会话状态枚举"""
    PENDING = "PENDING"                    # 待开始
    CHARGING = "CHARGING"                  # 充电中
    COMPLETED = "COMPLETED"                # 已完成
    INTERRUPTED = "INTERRUPTED"            # 已中断


class UserRole(Enum):
    """用户角色枚举"""
    USER = "USER"                          # 普通用户
    ADMIN = "ADMIN"                        # 管理员


class EventType(Enum):
    """调度事件类型枚举"""
    NEW_REQUEST = "NEW_REQUEST"            # 新请求
    CANCEL = "CANCEL"                      # 取消
    CONFIRM_ARRIVAL = "CONFIRM_ARRIVAL"    # 确认到场
    NO_SHOW = "NO_SHOW"                    # 过号
    CHARGE_START = "CHARGE_START"          # 开始充电
    CHARGE_END = "CHARGE_END"              # 充电结束
    CHARGE_INTERRUPT = "CHARGE_INTERRUPT"  # 充电中断
    LEAVE = "LEAVE"                        # 挪车离开
    STATION_FAULT = "STATION_FAULT"        # 桩故障
