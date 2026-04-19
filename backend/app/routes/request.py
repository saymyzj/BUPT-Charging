"""V3 Day 3 请求最小闭环接口。"""

from datetime import datetime

from flask import Blueprint, current_app, request

from app.enums import ChargeMode, RequestStatus
from app.services.billing_service import ensure_request_detail
from app.services.queue_model import (
    predict_queued_request,
    predict_waiting_area_request,
    refresh_station_after_queue_change,
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
    raw_value = (data or {}).get("stop_time")
    if raw_value:
        return _parse_iso_datetime(raw_value).strftime("%Y-%m-%dT%H:%M:%S")
    return fallback


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


def _front_waiting_count(req_row) -> int:
    if req_row["request_status"] != RequestStatus.WAITING_AREA.value or req_row["waiting_area_order"] is None:
        return 0

    row = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charge_request
        WHERE charge_mode = ?
          AND request_status = ?
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
    payload = {
        "request_id": req_row["request_id"],
        "queue_number": req_row["queue_number"],
        "charge_mode": req_row["charge_mode"],
        "request_energy": float(req_row["request_energy"]),
        "request_status": req_row["request_status"],
        "front_waiting_count": _front_waiting_count(req_row),
        "station_code": req_row["station_code"],
        "station_queue_position": req_row["station_queue_position"],
        "estimated_wait_seconds": req_row["estimated_wait_seconds"],
        "estimated_start_time": _iso_string(req_row["estimated_start_time"]),
        "estimated_finish_time": _iso_string(req_row["estimated_finish_time"]),
    }
    if req_row["request_status"] == RequestStatus.WAITING_AREA.value:
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
        """,
        [charge_mode, RequestStatus.WAITING_AREA.value],
        one=True,
    )

    request_id = _next_request_id()
    queue_number = _next_queue_number(charge_mode)
    waiting_area_order = int(order_row["max_order"]) + 1
    request_time = _parse_iso_datetime(data["request_time"]).strftime("%Y-%m-%dT%H:%M:%S")

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

    run_normal_scheduler(event_time=request_time, charge_mode=charge_mode)

    return success_response(
        {
            "request_id": request_id,
            "queue_number": queue_number,
            "request_status": RequestStatus.WAITING_AREA.value,
            "front_waiting_count": int(front_waiting_count["cnt"]),
        }
    )


@request_bp.route("/status/<request_id>", methods=["GET"])
@require_auth
def get_status(request_id):
    current_user = get_current_user()
    req_row = query_db(
        """
        SELECT
            cr.id,
            cr.request_id,
            cr.user_id,
            cr.charge_mode,
            cr.request_energy,
            cr.request_status,
            cr.queue_number,
            cr.waiting_area_order,
            cr.station_queue_position,
            cr.estimated_wait_seconds,
            cr.estimated_start_time,
            cr.estimated_finish_time,
            cs.station_code
        FROM charge_request cr
        LEFT JOIN charging_station cs ON cs.id = cr.station_id
        WHERE cr.request_id = ?
        """,
        [request_id],
        one=True,
    )
    if not req_row:
        return error_response(1002, "请求不存在")

    if current_user["role"] != "ADMIN" and int(req_row["user_id"]) != int(current_user["id"]):
        return error_response(1002, "请求不存在")

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
    if req_row["request_status"] != RequestStatus.WAITING_AREA.value:
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
    run_normal_scheduler(event_time=req_row["request_time"])
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
    if req_row["request_status"] != RequestStatus.WAITING_AREA.value:
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
    run_normal_scheduler(event_time=req_row["request_time"])
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
    if req_row["request_status"] != RequestStatus.WAITING_AREA.value:
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
    run_normal_scheduler(event_time=req_row["request_time"])
    return success_response(
        {
            "request_id": req_row["request_id"],
            "request_status": RequestStatus.CANCELLED.value,
        }
    )


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
        run_normal_scheduler(stop_dt.strftime("%Y-%m-%dT%H:%M:%S"), req_row["charge_mode"])

    ensure_request_detail(req_row["request_id"])
    return success_response(
        {
            "request_id": req_row["request_id"],
            "request_status": RequestStatus.COMPLETED_EARLY.value,
        }
    )


@request_bp.route("/detail/<request_id>", methods=["GET"])
@require_auth
def get_request_detail(request_id):
    current_user = get_current_user()
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

    return success_response(detail)
