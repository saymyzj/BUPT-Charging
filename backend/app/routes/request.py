from flask import Blueprint, request
from app.utils.response import success_response, error_response
from app.utils.validators import (
    validate_create_request,
    validate_cancel_request,
    validate_confirm_arrival_request,
    validate_interrupt_request,
    validate_confirm_leave_request,
    validate_pay_request
)
from app.services.billing_service import generate_detail, generate_bill, save_bill, process_payment
from app.utils.db import query_db, execute_db
from datetime import datetime

request_bp = Blueprint('request', __name__)


@request_bp.route('/create', methods=['POST'])
def create_request():
    """
    提交充电请求
    
    Request Body:
        {
            "request_time": "2026-03-31T10:00:00",
            "charge_mode": "FAST",
            "request_energy": 20.0
        }
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "request_id": "REQ001",
                "status": "WAITING",
                "estimated_wait_seconds": 600,
                "estimated_start_time": "2026-03-31T10:10:00",
                "estimated_finish_time": "2026-03-31T11:10:00"
            }
        }
    """
    data = request.get_json()
    
    # 参数校验
    is_valid, errors = validate_create_request(data)
    if not is_valid:
        return error_response(1001, "Invalid parameters", {"errors": errors})
    
    # 生成 request_id
    count = query_db("SELECT COUNT(*) as cnt FROM charge_request", one=True)
    request_id = f"REQ{count['cnt'] + 1:03d}"
    
    # 准备预测数据（临时模拟值，待调度模块接入后替换）
    estimated_wait_seconds = 600
    estimated_start_time = "2026-03-31T10:10:00"
    estimated_finish_time = "2026-03-31T11:10:00"
    
    # 插入数据库，状态直接设为 WAITING，同时写入预测字段
    execute_db("""
        INSERT INTO charge_request (
            request_id, charge_mode, request_energy, status, submit_time,
            estimated_wait_seconds, estimated_start_time, estimated_finish_time
        )
        VALUES (?, ?, ?, 'WAITING', ?, ?, ?, ?)
    """, [
        request_id,
        data['charge_mode'],
        data['request_energy'],
        data['request_time'],
        estimated_wait_seconds,
        estimated_start_time,
        estimated_finish_time
    ])
    
    # TODO: 调用调度模块获取真实预测结果
    # scheduler_client.get_prediction(request_id, charge_mode, request_energy)
    
    return success_response({
        "request_id": request_id,
        "status": "WAITING",
        "estimated_wait_seconds": estimated_wait_seconds,
        "estimated_start_time": estimated_start_time,
        "estimated_finish_time": estimated_finish_time
    })


@request_bp.route('/status/<request_id>', methods=['GET'])
def get_status(request_id):
    """
    查询请求状态
    
    Args:
        request_id: 请求 ID
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "request_id": "REQ001",
                "status": "WAITING",
                "station_id": "FAST_01",
                "estimated_wait_seconds": 300,
                "last_called_time": "2026-03-31T10:08:00"
            }
        }
    """
    req = query_db(
        "SELECT * FROM charge_request WHERE request_id = ?",
        [request_id],
        one=True
    )
    
    if not req:
        return error_response(1002, "Request not found")
    
    # 获取充电桩编号
    station_id = None
    if req['assigned_station_id']:
        station = query_db(
            "SELECT station_code FROM charging_station WHERE id = ?",
            [req['assigned_station_id']],
            one=True
        )
        if station:
            station_id = station['station_code']
    
    # 计算预计等待时间（简化计算）
    estimated_wait = 0
    if req['status'] in ['WAITING', 'CALLED']:
        estimated_wait = 300  # 默认 5 分钟
    
    return success_response({
        "request_id": request_id,
        "status": req['status'],
        "station_id": station_id,
        "estimated_wait_seconds": estimated_wait,
        "last_called_time": req['last_called_at']
    })


@request_bp.route('/cancel_queue', methods=['POST'])
def cancel_queue():
    """
    取消排队
    
    Request Body:
        {
            "request_id": "REQ001",
            "cancel_time": "2026-03-31T10:05:00"
        }
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "request_id": "REQ001",
                "status": "CANCELLED"
            }
        }
    """
    data = request.get_json()
    
    # 参数校验
    is_valid, errors = validate_cancel_request(data)
    if not is_valid:
        return error_response(1001, "Invalid parameters", {"errors": errors})
    
    request_id = data['request_id']
    cancel_time = data['cancel_time']
    
    # 查询请求
    req = query_db(
        "SELECT * FROM charge_request WHERE request_id = ?",
        [request_id],
        one=True
    )
    
    if not req:
        return error_response(1002, "Request not found")
    
    # 状态校验：只能取消 PENDING、WAITING 或 CALLED 状态的请求
    # 注：PENDING 是初始状态，WAITING 是入池后的状态
    if req['status'] not in ['PENDING', 'WAITING', 'CALLED']:
        return error_response(1003, "Current status does not allow cancel")
    
    # 如果已分配充电桩，释放预留
    if req['assigned_station_id']:
        execute_db("""
            UPDATE charging_station 
            SET status = 'IDLE', current_request_id = NULL 
            WHERE id = ?
        """, [req['assigned_station_id']])
    
    # 更新请求状态为 CANCELLED
    execute_db("""
        UPDATE charge_request 
        SET status = 'CANCELLED', updated_at = ? 
        WHERE request_id = ?
    """, [cancel_time, request_id])
    
    # TODO: 调用调度模块从等待池移除
    # scheduler_client.remove_from_pool(request_id, req['charge_mode'])
    
    # TODO: 触发重调度
    # scheduler_client.trigger_reschedule('CANCEL', request_id)
    
    return success_response({
        "request_id": request_id,
        "status": "CANCELLED"
    })


@request_bp.route('/confirm_arrival', methods=['POST'])
def confirm_arrival():
    """
    确认到场
    
    Request Body:
        {
            "request_id": "REQ001",
            "confirm_time": "2026-03-31T10:09:00"
        }
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "request_id": "REQ001",
                "status": "CONFIRMED",
                "station_id": "FAST_01"
            }
        }
    """
    data = request.get_json()
    
    # 参数校验
    is_valid, errors = validate_confirm_arrival_request(data)
    if not is_valid:
        return error_response(1001, "Invalid parameters", {"errors": errors})
    
    request_id = data['request_id']
    confirm_time = data['confirm_time']
    
    # 查询请求
    req = query_db(
        "SELECT * FROM charge_request WHERE request_id = ?",
        [request_id],
        one=True
    )
    
    if not req:
        return error_response(1002, "Request not found")
    
    # 状态校验：必须是 CALLED 状态才能确认到场
    if req['status'] != 'CALLED':
        return error_response(1003, "Request is not in CALLED status")
    
    # 检查是否过号（超时）
    if req['last_called_at']:
        called_time = datetime.fromisoformat(req['last_called_at'])
        confirm_dt = datetime.fromisoformat(confirm_time.replace('Z', '+00:00'))
        
        # 获取确认超时配置
        config = query_db(
            "SELECT config_value FROM scheduler_config WHERE config_key = 'CONFIRM_TIMEOUT_MINUTES'",
            one=True
        )
        timeout_minutes = int(config['config_value']) if config else 3
        
        # 检查是否超时
        if (confirm_dt - called_time).total_seconds() > timeout_minutes * 60:
            return error_response(1004, "Call number expired")
    
    # 获取充电桩编号
    station_id = None
    if req['assigned_station_id']:
        station = query_db(
            "SELECT station_code FROM charging_station WHERE id = ?",
            [req['assigned_station_id']],
            one=True
        )
        if station:
            station_id = station['station_code']
    
    # 更新请求状态为 CONFIRMED
    execute_db("""
        UPDATE charge_request 
        SET status = 'CONFIRMED', confirmed_at = ?, updated_at = ? 
        WHERE request_id = ?
    """, [confirm_time, confirm_time, request_id])
    
    return success_response({
        "request_id": request_id,
        "status": "CONFIRMED",
        "station_id": station_id
    })


@request_bp.route('/interrupt_charge', methods=['POST'])
def interrupt_charge():
    """
    中断充电
    
    Request Body:
        {
            "request_id": "REQ001",
            "interrupt_time": "2026-03-31T10:40:00"
        }
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "request_id": "REQ001",
                "status": "INTERRUPTED",
                "actual_energy": 12.5,
                "actual_service_seconds": 1800
            }
        }
    """
    data = request.get_json()
    
    # 参数校验
    is_valid, errors = validate_interrupt_request(data)
    if not is_valid:
        return error_response(1001, "Invalid parameters", {"errors": errors})
    
    request_id = data['request_id']
    interrupt_time = data['interrupt_time']
    
    # 查询请求
    req = query_db(
        "SELECT * FROM charge_request WHERE request_id = ?",
        [request_id],
        one=True
    )
    
    if not req:
        return error_response(1002, "Request not found")
    
    # 状态校验：必须是 CHARGING 状态才能中断
    if req['status'] != 'CHARGING':
        return error_response(1003, "Request is not in CHARGING status")
    
    # 查询充电会话
    session = query_db(
        """SELECT * FROM charging_session 
           WHERE request_id = ? AND status = 'CHARGING'""",
        [req['id']],
        one=True
    )
    
    if not session:
        return error_response(1003, "No active charging session found")
    
    # 计算实际充电时长和电量
    start_time = datetime.fromisoformat(session['start_time'])
    interrupt_dt = datetime.fromisoformat(interrupt_time.replace('Z', '+00:00'))
    actual_service_seconds = int((interrupt_dt - start_time).total_seconds())
    
    # 查询充电桩功率
    station = query_db(
        "SELECT * FROM charging_station WHERE id = ?",
        [session['station_id']],
        one=True
    )
    
    # 计算实际充电电量（功率 kW * 时间 h）
    actual_energy = round(station['power_kw'] * actual_service_seconds / 3600, 2)
    # 不能超过请求的电量和电池上限
    actual_energy = min(actual_energy, req['request_energy'], req['battery_limit_energy'])
    
    # 更新充电会话
    execute_db("""
        UPDATE charging_session 
        SET end_time = ?, actual_energy = ?, status = 'INTERRUPTED', 
            interrupt_reason = 'USER_INTERRUPT'
        WHERE id = ?
    """, [interrupt_time, actual_energy, session['id']])
    
    # 更新请求状态
    execute_db("""
        UPDATE charge_request 
        SET status = 'INTERRUPTED', actual_energy = ?, 
            actual_service_seconds = ?, updated_at = ?
        WHERE request_id = ?
    """, [actual_energy, actual_service_seconds, interrupt_time, request_id])
    
    # 释放充电桩
    execute_db("""
        UPDATE charging_station 
        SET status = 'IDLE', current_request_id = NULL, available_time = ?
        WHERE id = ?
    """, [interrupt_time, session['station_id']])
    
    # TODO: 触发重调度
    # scheduler_client.trigger_reschedule('CHARGE_INTERRUPT', request_id)
    
    return success_response({
        "request_id": request_id,
        "status": "INTERRUPTED",
        "actual_energy": actual_energy,
        "actual_service_seconds": actual_service_seconds
    })


@request_bp.route('/confirm_leave', methods=['POST'])
def confirm_leave():
    """
    确认挪车
    
    Request Body:
        {
            "request_id": "REQ001",
            "leave_time": "2026-03-31T11:15:00"
        }
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "request_id": "REQ001",
                "status": "COMPLETED"
            }
        }
    """
    data = request.get_json()
    
    # 参数校验
    is_valid, errors = validate_confirm_leave_request(data)
    if not is_valid:
        return error_response(1001, "Invalid parameters", {"errors": errors})
    
    request_id = data['request_id']
    leave_time = data['leave_time']
    
    # 查询请求
    req = query_db(
        "SELECT * FROM charge_request WHERE request_id = ?",
        [request_id],
        one=True
    )
    
    if not req:
        return error_response(1002, "Request not found")
    
    # 状态校验：请求必须是已完成状态（COMPLETED 或 COMPLETED_EARLY）
    if req['status'] not in ['COMPLETED', 'COMPLETED_EARLY']:
        return error_response(1003, "Request is not in completed status")
    
    # 查询充电会话和充电桩状态
    session = query_db(
        """SELECT cs.*, station.status as station_status 
           FROM charging_session cs
           JOIN charging_station station ON cs.station_id = station.id
           WHERE cs.request_id = ?""",
        [req['id']],
        one=True
    )
    
    if not session:
        return error_response(1003, "No charging session found")
    
    # 检查充电桩是否处于 WAITING_TO_LEAVE 状态
    if session['station_status'] != 'WAITING_TO_LEAVE':
        return error_response(1003, "Charging station is not in WAITING_TO_LEAVE status")
    
    # 更新会话的挪车时间
    execute_db("""
        UPDATE charging_session 
        SET left_at = ?
        WHERE id = ?
    """, [leave_time, session['id']])
    
    # 释放充电桩
    execute_db("""
        UPDATE charging_station 
        SET status = 'IDLE', current_request_id = NULL, available_time = ?
        WHERE id = ?
    """, [leave_time, session['station_id']])
    
    # TODO: 触发重调度
    # scheduler_client.trigger_reschedule('LEAVE', request_id)
    
    return success_response({
        "request_id": request_id,
        "status": "COMPLETED"
    })


@request_bp.route('/result/<request_id>', methods=['GET'])
def get_result(request_id):
    """
    获取详单与账单
    
    Args:
        request_id: 请求 ID
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "request_id": "REQ001",
                "detail": {...},  // 详单（18 个字段）
                "bill": {...}     // 账单（9 个字段）
            }
        }
    """
    # 查询请求
    req = query_db(
        "SELECT * FROM charge_request WHERE request_id = ?",
        [request_id],
        one=True
    )
    
    if not req:
        return error_response(1002, "Request not found")
    
    # 检查请求是否已结束（终态）
    final_statuses = ['COMPLETED', 'COMPLETED_EARLY', 'INTERRUPTED', 
                      'CANCELLED', 'NO_SHOW']
    if req['status'] not in final_statuses:
        return error_response(1003, "Request has not completed yet")
    
    # 生成详单
    detail = generate_detail(request_id)
    if not detail:
        return error_response(1002, "Failed to generate detail")
    
    # 生成账单
    bill = generate_bill(request_id)
    if not bill:
        return error_response(1002, "Failed to generate bill")
    
    # 如果账单未保存，保存到数据库
    existing_bill = query_db(
        """SELECT id FROM billing_record 
           WHERE request_id = (SELECT id FROM charge_request WHERE request_id = ?)""",
        [request_id],
        one=True
    )
    if not existing_bill:
        save_bill(request_id, bill)
    
    return success_response({
        "request_id": request_id,
        "detail": detail,
        "bill": bill
    })


@request_bp.route('/pay', methods=['POST'])
def pay():
    """
    支付确认
    
    Request Body:
        {
            "request_id": "REQ001",
            "pay_time": "2026-03-31T11:20:00",
            "pay_amount": 27.75
        }
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "request_id": "REQ001",
                "payment_status": "PAID"
            }
        }
    """
    data = request.get_json()
    
    # 参数校验
    is_valid, errors = validate_pay_request(data)
    if not is_valid:
        return error_response(1001, "Invalid parameters", {"errors": errors})
    
    request_id = data['request_id']
    pay_time = data['pay_time']
    pay_amount = float(data['pay_amount'])
    
    # 处理支付
    success, error_code, error_message = process_payment(request_id, pay_amount, pay_time)
    
    if not success:
        return error_response(error_code, error_message)
    
    return success_response({
        "request_id": request_id,
        "payment_status": "PAID"
    })
