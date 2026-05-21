"""V3 Day 3 请求最小闭环接口。"""

from datetime import datetime

from flask import Blueprint, current_app, request

from app.enums import ChargeMode, RequestStatus
from app.services.billing_service import ensure_request_detail
from app.services.acceptance_service import acceptance_enabled, acceptance_time, record_manual_event
from app.services.queue_model import (
    log_request_lifecycle,
    predict_queued_request,
    predict_waiting_area_request,
    refresh_station_after_queue_change,
    request_lifecycle,
    run_dispatch_scheduler,
    run_normal_scheduler,
    settle_station_until_time,
)
from app.utils.auth import get_current_user, require_auth
from app.utils.db import execute_db, query_db
from app.utils.response import error_response, success_response
from app.utils.validators import validate_create_request

request_bp = Blueprint("request", __name__)

ACTIVE_REQUEST_STATUSES = (
    RequestStatus.WAITING_AREA.value,
    RequestStatus.QUEUED.value,
    RequestStatus.CHARGING.value,
)


def _should_advance_runtime() -> bool:
    return not bool(current_app.config.get("TESTING")) and not acceptance_enabled()


def _parse_iso_datetime(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _iso_string(value):
    if value is None:
        return None
    return str(value).replace(" ", "T")


def _next_request_id() -> str:
    row = query_db(
        """
        SELECT request_id
        FROM charge_request
        WHERE request_id LIKE 'REQ%'
        ORDER BY CAST(SUBSTR(request_id, 4) AS INTEGER) DESC
        LIMIT 1
        """,
        one=True,
    )
    next_number = 1 if not row else int(str(row["request_id"])[3:]) + 1
    return f"REQ{next_number:04d}"


def _next_queue_number(charge_mode: str) -> str:
    prefix = "F" if charge_mode == ChargeMode.FAST.value else "T"
    row = query_db(
        """
        SELECT queue_number
        FROM charge_request
        WHERE queue_number LIKE ?
        ORDER BY CAST(SUBSTR(queue_number, 2) AS INTEGER) DESC
        LIMIT 1
        """,
        [f"{prefix}%"],
        one=True,
    )
    next_number = 1 if not row else int(str(row["queue_number"])[1:]) + 1
    return f"{prefix}{next_number}"


def _validate_request_energy(value):
    try:
        energy = float(value)
    except (TypeError, ValueError):
        return None
    if energy <= 0 or energy > 300:
        return None
    return energy


def _operation_time(data, fallback):
    if acceptance_enabled():
        return acceptance_time(fallback)
    raw_value = (data or {}).get("stop_time") or (data or {}).get("operation_time")
    if raw_value:
        return _parse_iso_datetime(raw_value).strftime("%Y-%m-%dT%H:%M:%S")
    return fallback


def _request_time(data):
    if acceptance_enabled():
        return acceptance_time(data.get("request_time"))
    return data.get("request_time")


def _run_request_scheduler(event_time, charge_mode=None):
    if acceptance_enabled():
        return run_dispatch_scheduler(event_time=event_time, charge_mode=charge_mode)
    return run_normal_scheduler(event_time=event_time, charge_mode=charge_mode)


def _poll_scheduler_time():
    return acceptance_time() if acceptance_enabled() else None


def _advance_runtime_for_read() -> None:
    if acceptance_enabled():
        run_dispatch_scheduler(event_time=acceptance_time())
    elif _should_advance_runtime():
        run_dispatch_scheduler()


def _record_acceptance_action(payload, result=None) -> None:
    if not acceptance_enabled():
        return
    record_manual_event(
        {
            "at": acceptance_time(),
            **payload,
        },
        status="EXECUTED",
        result=result or {},
    )


def _get_request_for_operation(request_id, current_user):
    req_row = query_db(
        """
        SELECT
            cr.id,
            cr.request_id,
            cr.user_id,
            cr.charge_mode,
            cr.request_energy,
            cr.actual_energy,
            cr.request_status,
            cr.queue_number,
            source.queue_number AS source_queue_number,
            cr.fault_source_request_id,
            cr.waiting_area_order,
            cr.request_time,
            cr.station_id,
            cr.station_queue_position,
            cr.estimated_start_time,
            cr.estimated_finish_time,
            cr.charge_start_time,
            cs.station_code,
            cs.power_kw
        FROM charge_request cr
        LEFT JOIN charging_station cs ON cs.id = cr.station_id
        LEFT JOIN charge_request source ON source.id = cr.fault_source_request_id
        WHERE cr.request_id = ?
        """,
        [request_id],
        one=True,
    )
    if not req_row:
        return None
    if current_user["role"] != "ADMIN" and int(req_row["user_id"]) != int(current_user["id"]):
        return None
    return req_row


def _get_status_row(request_id):
    return query_db(
        """
        SELECT
            cr.id,
            cr.request_id,
            cr.user_id,
            cr.charge_mode,
            cr.request_energy,
            cr.actual_energy,
            cr.request_status,
            cr.queue_number,
            source.queue_number AS source_queue_number,
            cr.fault_source_request_id,
            cr.waiting_area_order,
            cr.station_id,
            cr.station_queue_position,
            cr.estimated_wait_seconds,
            cr.estimated_start_time,
            cr.estimated_finish_time,
            cr.charge_start_time,
            cr.charge_stop_time,
            cr.charge_duration_seconds,
            cs.station_code,
            cs.power_kw
        FROM charge_request cr
        LEFT JOIN charging_station cs ON cs.id = cr.station_id
        LEFT JOIN charge_request source ON source.id = cr.fault_source_request_id
        WHERE cr.request_id = ?
        """,
        [request_id],
        one=True,
    )


def _active_status_row_for_user(user_pk):
    return query_db(
        """
        SELECT request_id
        FROM charge_request
        WHERE user_id = ?
          AND request_status IN (?, ?, ?)
        ORDER BY id DESC
        LIMIT 1
        """,
        [user_pk, *ACTIVE_REQUEST_STATUSES],
        one=True,
    )


def _front_waiting_count(req_row) -> int:
    if req_row["request_status"] != RequestStatus.WAITING_AREA.value or req_row["waiting_area_order"] is None:
        return 0

    if int(req_row["waiting_area_order"] or 0) == 0:
        row = query_db(
            """
            SELECT COUNT(*) AS cnt
            FROM charge_request cr
            LEFT JOIN charge_request source ON source.id = cr.fault_source_request_id
            WHERE cr.charge_mode = ?
              AND cr.request_status = ?
              AND cr.waiting_area_order = 0
              AND CAST(SUBSTR(COALESCE(source.queue_number, cr.queue_number), 2) AS INTEGER) <
                  CAST(SUBSTR(?, 2) AS INTEGER)
            """,
            [
                req_row["charge_mode"],
                RequestStatus.WAITING_AREA.value,
                req_row["source_queue_number"] or req_row["queue_number"],
            ],
            one=True,
        )
        return int(row["cnt"])

    row = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charge_request
        WHERE charge_mode = ?
          AND request_status = ?
          AND waiting_area_order > 0
          AND waiting_area_order < ?
        """,
        [
            req_row["charge_mode"],
            RequestStatus.WAITING_AREA.value,
            req_row["waiting_area_order"],
        ],
        one=True,
    )
    return int(row["cnt"])


def _serialize_status(req_row):
    actual_energy = float(req_row["actual_energy"] or 0)
    charged_energy = actual_energy
    if req_row["request_status"] == RequestStatus.CHARGING.value and req_row["charge_start_time"] and req_row["power_kw"]:
        start_dt = _parse_iso_datetime(req_row["charge_start_time"])
        if acceptance_enabled():
            now = _parse_iso_datetime(acceptance_time())
        else:
            now = datetime.now(start_dt.tzinfo) if start_dt.tzinfo else datetime.now()
        duration_seconds = max(0, int((now - start_dt).total_seconds()))
        live_energy = round(float(req_row["power_kw"]) * duration_seconds / 3600.0, 2)
        charged_energy = min(float(req_row["request_energy"]), max(actual_energy, live_energy))

    payload = {
        "request_id": req_row["request_id"],
        "queue_number": req_row["queue_number"],
        "source_queue_number": req_row["source_queue_number"],
        "effective_queue_number": req_row["source_queue_number"] or req_row["queue_number"],
        "is_fault_followup": bool(req_row["fault_source_request_id"]),
        "is_fault_queue": req_row["request_status"] == RequestStatus.WAITING_AREA.value and int(req_row["waiting_area_order"] or -1) == 0,
        "queue_context": (
            "FAULT_QUEUE"
            if req_row["request_status"] == RequestStatus.WAITING_AREA.value and int(req_row["waiting_area_order"] or -1) == 0
            else "WAITING_AREA"
            if req_row["request_status"] == RequestStatus.WAITING_AREA.value
            else "STATION_QUEUE"
            if req_row["request_status"] in {RequestStatus.QUEUED.value, RequestStatus.CHARGING.value}
            else "TERMINAL"
        ),
        "charge_mode": req_row["charge_mode"],
        "request_energy": float(req_row["request_energy"]),
        "request_status": req_row["request_status"],
        "front_waiting_count": _front_waiting_count(req_row),
        "station_code": req_row["station_code"],
        "station_queue_position": req_row["station_queue_position"],
        "estimated_wait_seconds": req_row["estimated_wait_seconds"],
        "estimated_start_time": _iso_string(req_row["estimated_start_time"]),
        "estimated_finish_time": _iso_string(req_row["estimated_finish_time"]),
        "timeline": request_lifecycle(str(req_row["request_id"])),
    }
    if not current_app.config.get("TESTING"):
        payload.update(
            {
                "actual_energy": actual_energy,
                "charged_energy": charged_energy,
                "charge_start_time": _iso_string(req_row["charge_start_time"]),
                "charge_stop_time": _iso_string(req_row["charge_stop_time"]),
                "charge_duration_seconds": int(req_row["charge_duration_seconds"] or 0),
            }
        )
    if req_row["request_status"] == RequestStatus.WAITING_AREA.value and int(req_row["waiting_area_order"] or -1) > 0:
        prediction = predict_waiting_area_request(req_row["request_id"])
        if prediction:
            payload.update(prediction)
    elif req_row["request_status"] in {
        RequestStatus.QUEUED.value,
        RequestStatus.CHARGING.value,
    }:
        prediction = predict_queued_request(req_row["request_id"])
        if prediction:
            payload.update(prediction)
    return payload


@request_bp.route("/create", methods=["POST"])
@require_auth
def create_request():
    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    if acceptance_enabled():
        data = {**data, "request_time": _request_time(data)}

    is_valid, errors = validate_create_request(data)
    if not is_valid:
        return error_response(1001, "参数错误", {"errors": errors})

    charge_mode = data["charge_mode"]
    if charge_mode not in {ChargeMode.FAST.value, ChargeMode.SLOW.value}:
        return error_response(1001, "charge_mode 必须是 FAST 或 SLOW")

    active_request = query_db(
        """
        SELECT request_id
        FROM charge_request
        WHERE user_id = ?
          AND request_status IN (?, ?, ?)
        LIMIT 1
        """,
        [current_user["id"], *ACTIVE_REQUEST_STATUSES],
        one=True,
    )
    if active_request:
        return error_response(1003, "当前用户已有活跃请求")

    waiting_area_count = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charge_request
        WHERE request_status = ?
          AND waiting_area_order > 0
        """,
        [RequestStatus.WAITING_AREA.value],
        one=True,
    )
    if int(waiting_area_count["cnt"]) >= int(current_app.config.get("WAITING_AREA_SIZE", 6)):
        return error_response(1004, "等候区容量已满")

    available_station = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charging_station
        WHERE charge_mode = ?
          AND station_status = 'RUNNING'
        """,
        [charge_mode],
        one=True,
    )
    if int(available_station["cnt"]) <= 0:
        return error_response(1005, "当前模式无可用充电桩")

    front_waiting_count = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charge_request
        WHERE charge_mode = ?
          AND request_status = ?
          AND waiting_area_order > 0
        """,
        [charge_mode, RequestStatus.WAITING_AREA.value],
        one=True,
    )
    order_row = query_db(
        """
        SELECT COALESCE(MAX(waiting_area_order), 0) AS max_order
        FROM charge_request
        WHERE charge_mode = ?
          AND request_status = ?
          AND waiting_area_order > 0
        """,
        [charge_mode, RequestStatus.WAITING_AREA.value],
        one=True,
    )

    request_id = _next_request_id()
    queue_number = _next_queue_number(charge_mode)
    waiting_area_order = int(order_row["max_order"]) + 1
    request_time = _parse_iso_datetime(_request_time(data)).strftime("%Y-%m-%dT%H:%M:%S")

    execute_db(
        """
        INSERT INTO charge_request (
            request_id, user_id, charge_mode, request_energy, request_status,
            queue_number, waiting_area_order, request_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            request_id,
            current_user["id"],
            charge_mode,
            float(data["request_energy"]),
            RequestStatus.WAITING_AREA.value,
            queue_number,
            waiting_area_order,
            request_time,
        ],
    )
    log_request_lifecycle(
        request_id,
        "REQUEST_SUBMITTED",
        event_time=request_time,
        queue_number=queue_number,
        charge_mode=charge_mode,
        request_energy=float(data["request_energy"]),
    )
    log_request_lifecycle(
        request_id,
        "WAITING_AREA_ENTERED",
        event_time=request_time,
        queue_number=queue_number,
        charge_mode=charge_mode,
        request_energy=float(data["request_energy"]),
        description=f"公共等候区第 {waiting_area_order} 位",
    )

    dispatch_result = _run_request_scheduler(event_time=request_time, charge_mode=charge_mode)
    response_data = {
        "request_id": request_id,
        "queue_number": queue_number,
        "request_status": RequestStatus.WAITING_AREA.value,
        "front_waiting_count": int(front_waiting_count["cnt"]),
    }
    _record_acceptance_action(
        {
            "event_type": "APPLY",
            "vehicle_code": current_user["user_id"],
            "charge_mode": charge_mode,
            "value": float(data["request_energy"]),
            "raw_text": f"手动提交 {current_user['user_id']} {charge_mode} {float(data['request_energy']):g}kWh",
        },
        {"request_id": request_id, "queue_number": queue_number, "dispatch": dispatch_result},
    )

    return success_response(response_data)


@request_bp.route("/status/<request_id>", methods=["GET"])
@require_auth
def get_status(request_id):
    current_user = get_current_user()
    _advance_runtime_for_read()
    req_row = _get_status_row(request_id)
    if not req_row:
        return error_response(1002, "请求不存在")

    if current_user["role"] != "ADMIN" and int(req_row["user_id"]) != int(current_user["id"]):
        return error_response(1002, "请求不存在")

    return success_response(_serialize_status(req_row))


@request_bp.route("/active", methods=["GET"])
@require_auth
def get_active_request():
    current_user = get_current_user()
    _advance_runtime_for_read()
    active_row = _active_status_row_for_user(current_user["id"])
    if not active_row:
        return success_response({})

    req_row = _get_status_row(active_row["request_id"])
    if not req_row:
        return success_response({})
    return success_response(_serialize_status(req_row))


@request_bp.route("/mode", methods=["PUT"])
@require_auth
def update_request_mode():
    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    request_id = (data.get("request_id") or "").strip()
    charge_mode = data.get("charge_mode")

    if not request_id or charge_mode not in {ChargeMode.FAST.value, ChargeMode.SLOW.value}:
        return error_response(1001, "参数错误")

    req_row = _get_request_for_operation(request_id, current_user)
    if not req_row:
        return error_response(1002, "请求不存在")
    if req_row["request_status"] != RequestStatus.WAITING_AREA.value or int(req_row["waiting_area_order"] or 0) <= 0:
        return error_response(1003, "当前状态不允许该操作")

    if charge_mode == req_row["charge_mode"]:
        return success_response(
            {
                "request_id": req_row["request_id"],
                "queue_number": req_row["queue_number"],
                "request_status": RequestStatus.WAITING_AREA.value,
                "front_waiting_count": _front_waiting_count(req_row),
            }
        )

    available_station = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charging_station
        WHERE charge_mode = ?
          AND station_status = 'RUNNING'
        """,
        [charge_mode],
        one=True,
    )
    if int(available_station["cnt"]) <= 0:
        return error_response(1005, "当前模式无可用充电桩")

    front_row = query_db(
        """
        SELECT COUNT(*) AS cnt, COALESCE(MAX(waiting_area_order), 0) AS max_order
        FROM charge_request
        WHERE charge_mode = ?
          AND request_status = ?
          AND waiting_area_order > 0
        """,
        [charge_mode, RequestStatus.WAITING_AREA.value],
        one=True,
    )
    new_queue_number = _next_queue_number(charge_mode)
    new_order = int(front_row["max_order"]) + 1
    response_data = {
        "request_id": req_row["request_id"],
        "queue_number": new_queue_number,
        "request_status": RequestStatus.WAITING_AREA.value,
        "front_waiting_count": int(front_row["cnt"]),
    }

    execute_db(
        """
        UPDATE charge_request
        SET charge_mode = ?,
            queue_number = ?,
            waiting_area_order = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [charge_mode, new_queue_number, new_order, req_row["id"]],
    )
    dispatch_result = _run_request_scheduler(event_time=_operation_time(data, req_row["request_time"]))
    _record_acceptance_action(
        {
            "event_type": "CHANGE",
            "vehicle_code": current_user["user_id"],
            "charge_mode": charge_mode,
            "value": -1,
            "raw_text": f"手动修改 {current_user['user_id']} 为 {charge_mode}",
        },
        {"request_id": req_row["request_id"], "queue_number": new_queue_number, "dispatch": dispatch_result},
    )
    return success_response(response_data)


@request_bp.route("/energy", methods=["PUT"])
@require_auth
def update_request_energy():
    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    request_id = (data.get("request_id") or "").strip()
    request_energy = _validate_request_energy(data.get("request_energy"))

    if not request_id:
        return error_response(1001, "参数错误")
    if request_energy is None:
        return error_response(1008, "request_energy 不合法")

    req_row = _get_request_for_operation(request_id, current_user)
    if not req_row:
        return error_response(1002, "请求不存在")
    if req_row["request_status"] != RequestStatus.WAITING_AREA.value or int(req_row["waiting_area_order"] or 0) <= 0:
        return error_response(1003, "当前状态不允许该操作")

    execute_db(
        """
        UPDATE charge_request
        SET request_energy = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [request_energy, req_row["id"]],
    )
    response_data = {
        "request_id": req_row["request_id"],
        "queue_number": req_row["queue_number"],
        "request_energy": request_energy,
        "request_status": RequestStatus.WAITING_AREA.value,
        "front_waiting_count": _front_waiting_count(req_row),
    }
    dispatch_result = _run_request_scheduler(event_time=_operation_time(data, req_row["request_time"]))
    _record_acceptance_action(
        {
            "event_type": "CHANGE",
            "vehicle_code": current_user["user_id"],
            "charge_mode": req_row["charge_mode"],
            "value": request_energy,
            "raw_text": f"手动修改 {current_user['user_id']} 电量 {request_energy:g}kWh",
        },
        {"request_id": req_row["request_id"], "dispatch": dispatch_result},
    )
    return success_response(response_data)


@request_bp.route("/cancel", methods=["POST"])
@require_auth
def cancel_request():
    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    request_id = (data.get("request_id") or "").strip()

    if not request_id:
        return error_response(1001, "参数错误")

    req_row = _get_request_for_operation(request_id, current_user)
    if not req_row:
        return error_response(1002, "请求不存在")
    if req_row["request_status"] != RequestStatus.WAITING_AREA.value or int(req_row["waiting_area_order"] or 0) <= 0:
        return error_response(1003, "当前状态不允许该操作")

    execute_db(
        """
        UPDATE charge_request
        SET request_status = ?,
            waiting_area_order = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [RequestStatus.CANCELLED.value, req_row["id"]],
    )
    operation_time = _operation_time(data, req_row["request_time"])
    log_request_lifecycle(
        str(req_row["request_id"]),
        "REQUEST_CANCELLED",
        event_time=operation_time,
        description="用户取消请求",
    )
    dispatch_result = _run_request_scheduler(event_time=operation_time)
    response_data = {
        "request_id": req_row["request_id"],
        "request_status": RequestStatus.CANCELLED.value,
    }
    _record_acceptance_action(
        {
            "event_type": "CANCEL_OR_STOP",
            "vehicle_code": current_user["user_id"],
            "value": 0,
            "raw_text": f"手动取消 {current_user['user_id']}",
        },
        {"request_id": req_row["request_id"], "dispatch": dispatch_result},
    )
    return success_response(response_data)


@request_bp.route("/stop", methods=["POST"])
@require_auth
def stop_request():
    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    request_id = (data.get("request_id") or "").strip()

    if not request_id:
        return error_response(1001, "参数错误")

    req_row = _get_request_for_operation(request_id, current_user)
    if not req_row:
        return error_response(1002, "请求不存在")
    if req_row["request_status"] not in {
        RequestStatus.QUEUED.value,
        RequestStatus.CHARGING.value,
    }:
        return error_response(1003, "当前状态不允许该操作")

    stop_time = _operation_time(data, req_row["estimated_start_time"] or req_row["request_time"])
    if req_row["station_id"]:
        settle_station_until_time(int(req_row["station_id"]), stop_time)
        req_row = _get_request_for_operation(request_id, current_user)
        if not req_row:
            return error_response(1002, "请求不存在")
        if req_row["request_status"] not in {
            RequestStatus.QUEUED.value,
            RequestStatus.CHARGING.value,
        }:
            return error_response(1003, "当前状态不允许该操作")

    stop_dt = _parse_iso_datetime(stop_time)
    charge_start_dt = _parse_iso_datetime(req_row["charge_start_time"] or stop_time)

    if req_row["request_status"] == RequestStatus.CHARGING.value:
        if stop_dt < charge_start_dt:
            stop_dt = charge_start_dt
        duration_seconds = max(0, int((stop_dt - charge_start_dt).total_seconds()))
        actual_energy = round(float(req_row["power_kw"]) * duration_seconds / 3600.0, 2)
        if actual_energy > float(req_row["request_energy"]):
            actual_energy = float(req_row["request_energy"])
        start_time_value = charge_start_dt.strftime("%Y-%m-%dT%H:%M:%S")
        should_count_station = duration_seconds > 0 or actual_energy > 0
    else:
        duration_seconds = 0
        actual_energy = 0.0
        start_time_value = stop_dt.strftime("%Y-%m-%dT%H:%M:%S")
        should_count_station = False

    execute_db(
        """
        UPDATE charge_request
        SET request_status = ?,
            actual_energy = ?,
            charge_start_time = ?,
            charge_stop_time = ?,
            charge_duration_seconds = ?,
            station_queue_position = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [
            RequestStatus.COMPLETED_EARLY.value,
            actual_energy,
            start_time_value,
            stop_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            duration_seconds,
            req_row["id"],
        ],
    )
    if req_row["station_id"]:
        execute_db(
            """
            UPDATE charging_session
            SET end_time = ?,
                actual_energy = ?,
                status = ?
            WHERE request_id = ?
            """,
            [
                stop_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                actual_energy,
                RequestStatus.COMPLETED_EARLY.value,
                req_row["id"],
            ],
        )
        if should_count_station:
            execute_db(
                """
                UPDATE charging_station
                SET total_charge_count = total_charge_count + 1,
                    total_charge_seconds = total_charge_seconds + ?,
                    total_charge_energy = total_charge_energy + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                [duration_seconds, actual_energy, req_row["station_id"]],
            )
        refresh_station_after_queue_change(int(req_row["station_id"]), stop_dt.strftime("%Y-%m-%dT%H:%M:%S"))
        dispatch_result = _run_request_scheduler(stop_dt.strftime("%Y-%m-%dT%H:%M:%S"), req_row["charge_mode"])
    else:
        dispatch_result = {}

    ensure_request_detail(req_row["request_id"])
    log_request_lifecycle(
        str(req_row["request_id"]),
        "CHARGING_COMPLETED_EARLY",
        event_time=stop_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        station_code=req_row["station_code"],
        description="用户提前结束充电",
    )
    response_data = {
        "request_id": req_row["request_id"],
        "request_status": RequestStatus.COMPLETED_EARLY.value,
    }
    _record_acceptance_action(
        {
            "event_type": "CANCEL_OR_STOP",
            "vehicle_code": current_user["user_id"],
            "value": 0,
            "raw_text": f"手动提前结束 {current_user['user_id']}",
        },
        {"request_id": req_row["request_id"], "dispatch": dispatch_result},
    )
    return success_response(response_data)


@request_bp.route("/detail/<request_id>", methods=["GET"])
@require_auth
def get_request_detail(request_id):
    current_user = get_current_user()
    _advance_runtime_for_read()
    req_row = query_db(
        """
        SELECT request_id, user_id
        FROM charge_request
        WHERE request_id = ?
        """,
        [request_id],
        one=True,
    )
    if not req_row:
        return error_response(1002, "请求不存在")

    if current_user["role"] != "ADMIN" and int(req_row["user_id"]) != int(current_user["id"]):
        return error_response(1002, "请求不存在")

    detail = ensure_request_detail(request_id)
    if not detail:
        return error_response(1003, "详单尚未生成")

    return success_response({**detail, "timeline": request_lifecycle(request_id)})


@request_bp.route("/details", methods=["GET"])
@require_auth
def list_request_details():
    current_user = get_current_user()
    _advance_runtime_for_read()
    rows = query_db(
        """
        SELECT
            rd.detail_id,
            cr.request_id,
            rd.station_code,
            rd.actual_energy,
            rd.charge_duration_seconds,
            rd.start_time,
            rd.stop_time,
            rd.detail_generated_at,
            rd.charge_fee,
            rd.service_fee,
            rd.total_fee,
            rd.payment_status,
            rd.paid_at,
            rd.request_status
        FROM request_detail rd
        JOIN charge_request cr ON cr.id = rd.request_id
        WHERE rd.user_id = ?
        ORDER BY rd.detail_generated_at DESC, rd.id DESC
        """,
        [current_user["id"]],
    )
    return success_response(
        [
            {
                "detail_id": row["detail_id"],
                "request_id": row["request_id"],
                "station_code": row["station_code"],
                "actual_energy": float(row["actual_energy"]),
                "charge_duration_seconds": int(row["charge_duration_seconds"]),
                "start_time": _iso_string(row["start_time"]),
                "stop_time": _iso_string(row["stop_time"]),
                "detail_generated_at": _iso_string(row["detail_generated_at"]),
                "charge_fee": float(row["charge_fee"]),
                "service_fee": float(row["service_fee"]),
                "total_fee": float(row["total_fee"]),
                "payment_status": row["payment_status"],
                "paid_at": _iso_string(row["paid_at"]),
                "request_status": row["request_status"],
                "timeline": request_lifecycle(str(row["request_id"])),
            }
            for row in rows
        ]
    )


@request_bp.route("/detail/<request_id>/pay", methods=["POST"])
@require_auth
def pay_request_detail(request_id):
    current_user = get_current_user()
    row = query_db(
        """
        SELECT rd.id
        FROM request_detail rd
        JOIN charge_request cr ON cr.id = rd.request_id
        WHERE cr.request_id = ?
          AND rd.user_id = ?
        """,
        [request_id, current_user["id"]],
        one=True,
    )
    if not row:
        return error_response(1002, "request detail not found")

    execute_db(
        """
        UPDATE request_detail
        SET payment_status = 'PAID',
            paid_at = ?
        WHERE id = ?
        """,
        [datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), row["id"]],
    )
    detail = ensure_request_detail(request_id)
    return success_response({**detail, "request_id": request_id, "timeline": request_lifecycle(request_id)})
