"""
冻结接口结构构造器。

统一生成：
1. 请求状态查询响应
2. 详单 detail
3. 账单 bill
4. 批量模拟 summary

这样后续算法和状态机可以继续演进，但对成员B/C暴露的字段结构保持稳定。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


def _iso_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%S")
    return str(value)


def build_status_response(
    *,
    request_id: str,
    status: str,
    station_id: Optional[str],
    estimated_wait_seconds: int,
    last_called_time: Optional[str],
) -> Dict[str, Any]:
    """构造冻结文档中的状态查询响应结构。"""
    return {
        "request_id": request_id,
        "status": status,
        "station_id": station_id,
        "estimated_wait_seconds": int(estimated_wait_seconds),
        "last_called_time": _iso_string(last_called_time),
    }


def build_detail_record(
    *,
    request_id: str,
    charge_mode: str,
    request_energy: float,
    actual_energy: float,
    request_time: Any,
    queue_enter_time: Any,
    called_time: Any,
    arrival_confirm_time: Any,
    charge_start_time: Any,
    charge_end_time: Any,
    leave_notify_time: Any,
    final_leave_time: Any,
    station_id: Optional[str],
    final_status: str,
    is_no_show: bool,
    is_cancelled: bool,
    is_interrupted: bool,
    is_fault_requeue: bool,
    is_leave_timeout: bool,
) -> Dict[str, Any]:
    """构造冻结文档中的 18 字段详单结构。"""
    return {
        "request_id": request_id,
        "charge_mode": charge_mode,
        "request_energy": round(float(request_energy), 2),
        "actual_energy": round(float(actual_energy), 2),
        "request_time": _iso_string(request_time),
        "queue_enter_time": _iso_string(queue_enter_time),
        "called_time": _iso_string(called_time),
        "arrival_confirm_time": _iso_string(arrival_confirm_time),
        "charge_start_time": _iso_string(charge_start_time),
        "charge_end_time": _iso_string(charge_end_time),
        "leave_notify_time": _iso_string(leave_notify_time),
        "final_leave_time": _iso_string(final_leave_time),
        "station_id": station_id,
        "final_status": final_status,
        "is_no_show": bool(is_no_show),
        "is_cancelled": bool(is_cancelled),
        "is_interrupted": bool(is_interrupted),
        "is_fault_requeue": bool(is_fault_requeue),
        "is_leave_timeout": bool(is_leave_timeout),
    }


def build_bill_record(
    *,
    request_id: str,
    billing_mode: str,
    request_energy: float,
    billing_energy: float,
    energy_fee: float,
    time_fee: float,
    occupancy_fee: float,
    total_fee: float,
    payment_status: str,
) -> Dict[str, Any]:
    """构造冻结文档中的 9 字段账单结构。"""
    return {
        "request_id": request_id,
        "billing_mode": billing_mode,
        "request_energy": round(float(request_energy), 2),
        "billing_energy": round(float(billing_energy), 2),
        "energy_fee": round(float(energy_fee), 2),
        "time_fee": round(float(time_fee), 2),
        "occupancy_fee": round(float(occupancy_fee), 2),
        "total_fee": round(float(total_fee), 2),
        "payment_status": payment_status,
    }


def build_batch_summary(
    *,
    total_users: int,
    completed_users: int,
    avg_wait_seconds: float,
    avg_finish_seconds: float,
    total_finish_seconds: int,
    station_utilization: float,
) -> Dict[str, Any]:
    """构造冻结文档中的批量模拟 summary 结构。"""
    return {
        "total_users": int(total_users),
        "completed_users": int(completed_users),
        "avg_wait_seconds": round(float(avg_wait_seconds), 2),
        "avg_finish_seconds": round(float(avg_finish_seconds), 2),
        "total_finish_seconds": int(total_finish_seconds),
        "station_utilization": round(float(station_utilization), 4),
    }
