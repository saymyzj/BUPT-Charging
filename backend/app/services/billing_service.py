"""
计费服务模块
处理详单生成、账单计算、支付等业务逻辑
"""

from app.utils.db import query_db, execute_db
from datetime import datetime


def get_billing_config():
    """
    获取计费配置
    
    Returns:
        dict: 计费配置参数
    """
    configs = query_db("SELECT config_key, config_value FROM scheduler_config")
    config_dict = {row['config_key']: row['config_value'] for row in configs}
    
    return {
        'billing_mode': config_dict.get('BILLING_MODE', 'ENERGY'),
        'energy_price': float(config_dict.get('ENERGY_PRICE', 1.5)),
        'time_price': float(config_dict.get('TIME_PRICE', 0.0)),
        'occupancy_price': float(config_dict.get('OCCUPANCY_PRICE', 0.5)),
        'occupancy_start_after_minutes': int(config_dict.get('OCCUPANCY_START_AFTER_MINUTES', 10))
    }


def generate_detail(request_id):
    """
    生成详单
    
    详单包含18个字段，记录用户充电全流程的时间节点和状态
    
    Args:
        request_id: 请求ID
    
    Returns:
        dict: 详单数据
    """
    # 查询请求信息
    req = query_db(
        """SELECT cr.*, cs.station_id, cs.start_time, cs.end_time, 
                  cs.left_at, cs.leave_deadline, cs.interrupt_reason
           FROM charge_request cr
           LEFT JOIN charging_session cs ON cs.request_id = cr.id
           WHERE cr.request_id = ?""",
        [request_id],
        one=True
    )
    
    if not req:
        return None
    
    # 获取充电桩编号
    station_code = None
    if req['station_id']:
        station = query_db(
            "SELECT station_code FROM charging_station WHERE id = ?",
            [req['station_id']],
            one=True
        )
        if station:
            station_code = station['station_code']
    
    # 计算挪车是否超时
    is_leave_timeout = False
    if req['left_at'] and req['leave_deadline']:
        left_time = datetime.fromisoformat(req['left_at'])
        deadline = datetime.fromisoformat(req['leave_deadline'])
        is_leave_timeout = left_time > deadline
    
    # 构建详单（18个字段）
    detail = {
        "request_id": request_id,
        "charge_mode": req['charge_mode'],
        "request_energy": float(req['request_energy']),
        "actual_energy": float(req['actual_energy']),
        "request_time": req['submit_time'],
        "queue_enter_time": req['submit_time'],  # 简化：入队时间等于提交时间
        "called_time": req['last_called_at'],
        "arrival_confirm_time": req['confirmed_at'],
        "charge_start_time": req['start_time'],
        "charge_end_time": req['end_time'],
        "leave_notify_time": req['end_time'],  # 充电结束即提醒挪车
        "final_leave_time": req['left_at'],
        "station_id": station_code,
        "final_status": req['status'],
        "is_no_show": req['status'] == 'NO_SHOW',
        "is_cancelled": req['status'] == 'CANCELLED',
        "is_interrupted": req['status'] == 'INTERRUPTED',
        "is_fault_requeue": bool(req['fault_requeue_flag']),
        "is_leave_timeout": is_leave_timeout
    }
    
    return detail


def generate_bill(request_id):
    """
    生成账单
    
    账单包含9个字段，记录费用计算结果
    
    Args:
        request_id: 请求ID
    
    Returns:
        dict: 账单数据
    """
    # 查询请求信息
    req = query_db(
        """SELECT cr.*, cs.end_time, cs.left_at, cs.leave_deadline
           FROM charge_request cr
           LEFT JOIN charging_session cs ON cs.request_id = cr.id
           WHERE cr.request_id = ?""",
        [request_id],
        one=True
    )
    
    if not req:
        return None
    
    # 查询已有计费记录
    billing_record = query_db(
        """SELECT * FROM billing_record 
           WHERE request_id = (SELECT id FROM charge_request WHERE request_id = ?)""",
        [request_id],
        one=True
    )
    
    if billing_record:
        # 返回已存在的账单
        return {
            "request_id": request_id,
            "billing_mode": billing_record['billing_mode'],
            "request_energy": float(req['request_energy']),
            "billing_energy": float(billing_record['billing_energy']),
            "energy_fee": float(billing_record['energy_fee']),
            "time_fee": float(billing_record['time_fee']),
            "occupancy_fee": float(billing_record['occupancy_fee']),
            "total_fee": float(billing_record['total_fee']),
            "payment_status": billing_record['payment_status']
        }
    
    # 获取计费配置
    config = get_billing_config()
    
    # 获取实际充电电量
    actual_energy = float(req['actual_energy'])
    
    # 计算电量费用
    energy_fee = round(actual_energy * config['energy_price'], 2)
    
    # 计算时长费用（如按时间计费）
    time_fee = 0.0
    if config['billing_mode'] == 'TIME' and req['actual_service_seconds']:
        actual_minutes = req['actual_service_seconds'] / 60
        time_fee = round(actual_minutes * config['time_price'], 2)
    
    # 计算占位费
    occupancy_fee = 0.0
    if req['left_at'] and req['leave_deadline']:
        left_time = datetime.fromisoformat(req['left_at'])
        deadline = datetime.fromisoformat(req['leave_deadline'])
        if left_time > deadline:
            overtime_minutes = (left_time - deadline).total_seconds() / 60
            occupancy_fee = round(overtime_minutes * config['occupancy_price'], 2)
    
    # 计算总费用
    total_fee = round(energy_fee + time_fee + occupancy_fee, 2)
    
    # 确定计费电量
    billing_energy = actual_energy if config['billing_mode'] == 'ENERGY' else 0.0
    
    return {
        "request_id": request_id,
        "billing_mode": config['billing_mode'],
        "request_energy": float(req['request_energy']),
        "billing_energy": billing_energy,
        "energy_fee": energy_fee,
        "time_fee": time_fee,
        "occupancy_fee": occupancy_fee,
        "total_fee": total_fee,
        "payment_status": "UNPAID"
    }


def save_bill(request_id, bill_data):
    """
    保存账单到数据库
    
    Args:
        request_id: 请求ID
        bill_data: 账单数据
    
    Returns:
        bool: 是否保存成功
    """
    req = query_db(
        "SELECT id FROM charge_request WHERE request_id = ?",
        [request_id],
        one=True
    )
    
    if not req:
        return False
    
    execute_db("""
        INSERT INTO billing_record 
        (request_id, billing_mode, billing_energy, energy_fee, time_fee, 
         occupancy_fee, total_fee, payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        req['id'],
        bill_data['billing_mode'],
        bill_data['billing_energy'],
        bill_data['energy_fee'],
        bill_data['time_fee'],
        bill_data['occupancy_fee'],
        bill_data['total_fee'],
        bill_data['payment_status']
    ])
    
    return True


def process_payment(request_id, pay_amount, pay_time):
    """
    处理支付
    
    Args:
        request_id: 请求ID
        pay_amount: 支付金额
        pay_time: 支付时间
    
    Returns:
        tuple: (success: bool, error_code: int, error_message: str)
    """
    # 查询请求
    req = query_db(
        "SELECT id, status FROM charge_request WHERE request_id = ?",
        [request_id],
        one=True
    )
    
    if not req:
        return False, 1002, "Request not found"
    
    # 查询账单
    bill = query_db(
        "SELECT * FROM billing_record WHERE request_id = ?",
        [req['id']],
        one=True
    )
    
    if not bill:
        return False, 1003, "Bill not found"
    
    # 检查是否已支付
    if bill['payment_status'] == 'PAID':
        return False, 1003, "Already paid"
    
    # 检查金额是否匹配
    if abs(float(pay_amount) - float(bill['total_fee'])) > 0.01:
        return False, 1001, "Payment amount does not match bill"
    
    # 更新支付状态
    execute_db("""
        UPDATE billing_record 
        SET payment_status = 'PAID', paid_at = ?
        WHERE request_id = ?
    """, [pay_time, req['id']])
    
    return True, 0, "success"
