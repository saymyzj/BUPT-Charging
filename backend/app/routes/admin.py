"""V3 admin routes."""

import json

from flask import Blueprint, current_app, request

from app.enums import DispatchMode, FaultDispatchMode
from app.services.queue_model import (
    handle_station_fault,
    handle_station_recover,
    handle_station_shutdown,
    handle_station_start,
    run_dispatch_scheduler,
    set_dispatch_mode,
    set_fault_dispatch_mode,
)
from app.utils.auth import require_admin
from app.utils.db import execute_db, query_db
from app.utils.response import error_response, success_response

admin_bp = Blueprint("admin", __name__)


def _system_mode_value(config_key: str, default_value: str) -> str:
    row = query_db(
        "SELECT config_value FROM scheduler_config WHERE config_key = ?",
        [config_key],
        one=True,
    )
    if not row:
        return default_value
    return str(row["config_value"])


def _system_config_int(config_key: str, default_value: int) -> int:
    row = query_db(
        "SELECT config_value FROM scheduler_config WHERE config_key = ?",
        [config_key],
        one=True,
    )
    if not row:
        return int(default_value)
    try:
        return int(row["config_value"])
    except (TypeError, ValueError):
        return int(default_value)


def _charging_queue_len() -> int:
    row = query_db(
        "SELECT COALESCE(MAX(queue_capacity), 0) AS queue_capacity FROM charging_station",
        one=True,
    )
    if row and int(row["queue_capacity"]) > 0:
        return int(row["queue_capacity"])
    return int(current_app.config.get("CHARGING_QUEUE_LEN", 2))


def _should_advance_runtime() -> bool:
    return not bool(current_app.config.get("TESTING"))


def _iso_string(value):
    if value is None:
        return None
    return str(value).replace(" ", "T")


def _has_active_request(user_pk: int) -> bool:
    row = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charge_request
        WHERE user_id = ?
          AND request_status IN ('WAITING_AREA', 'QUEUED', 'CHARGING')
        """,
        [user_pk],
        one=True,
    )
    return bool(row and int(row["cnt"]) > 0)


def _user_summary(row):
    return {
        "user_id": row["user_id"],
        "username": row["username"],
        "battery_capacity": float(row["battery_capacity"]),
        "role": row["role"],
        "created_at": _iso_string(row["created_at"]),
        "has_active_request": _has_active_request(int(row["id"])),
    }


def _detail_summary(row):
    return {
        "detail_id": row["detail_id"],
        "detail_generated_at": _iso_string(row["detail_generated_at"]),
        "station_code": row["station_code"],
        "actual_energy": float(row["actual_energy"]),
        "charge_duration_seconds": int(row["charge_duration_seconds"]),
        "start_time": _iso_string(row["start_time"]),
        "stop_time": _iso_string(row["stop_time"]),
        "charge_fee": float(row["charge_fee"]),
        "service_fee": float(row["service_fee"]),
        "total_fee": float(row["total_fee"]),
        "request_status": row["request_status"],
    }


def _validate_positive_float(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


@admin_bp.route("/system/config", methods=["GET"])
@require_admin
def get_system_config():
    fast_row = query_db(
        "SELECT COUNT(*) AS cnt FROM charging_station WHERE charge_mode = 'FAST'",
        one=True,
    )
    slow_row = query_db(
        "SELECT COUNT(*) AS cnt FROM charging_station WHERE charge_mode = 'SLOW'",
        one=True,
    )
    return success_response(
        {
            "fast_station_count": int(fast_row["cnt"]) if fast_row else 0,
            "slow_station_count": int(slow_row["cnt"]) if slow_row else 0,
            "waiting_area_capacity": _system_config_int(
                "waiting_area_capacity",
                current_app.config.get("WAITING_AREA_SIZE", 6),
            ),
            "charging_queue_len": _charging_queue_len(),
            "dispatch_mode": _system_mode_value("dispatch_mode", current_app.config.get("DISPATCH_MODE", "NORMAL")),
            "fault_dispatch_mode": _system_mode_value(
                "fault_dispatch_mode",
                current_app.config.get("FAULT_DISPATCH_MODE", "TIME_ORDER"),
            ),
        }
    )


@admin_bp.route("/system/fault-dispatch-mode", methods=["PUT"])
@require_admin
def update_fault_dispatch_mode():
    data = request.get_json(silent=True) or {}
    mode = data.get("fault_dispatch_mode")
    valid_modes = {FaultDispatchMode.PRIORITY.value, FaultDispatchMode.TIME_ORDER.value}
    if mode not in valid_modes:
        return error_response(1001, "fault_dispatch_mode must be PRIORITY or TIME_ORDER")

    return success_response({"fault_dispatch_mode": set_fault_dispatch_mode(mode)})


@admin_bp.route("/system/dispatch-mode", methods=["PUT"])
@require_admin
def update_dispatch_mode():
    data = request.get_json(silent=True) or {}
    mode = data.get("dispatch_mode")
    valid_modes = {
        DispatchMode.NORMAL.value,
        DispatchMode.EXT_SINGLE_BATCH.value,
        DispatchMode.EXT_FULL_BATCH.value,
    }
    if mode not in valid_modes:
        return error_response(1001, "dispatch_mode must be NORMAL, EXT_SINGLE_BATCH, or EXT_FULL_BATCH")

    return success_response({"dispatch_mode": set_dispatch_mode(mode)})


@admin_bp.route("/stations", methods=["GET"])
@require_admin
def list_stations():
    include_user = not bool(current_app.config.get("TESTING"))
    if _should_advance_runtime():
        run_dispatch_scheduler()
    rows = query_db(
        """
        SELECT
            cs.station_code,
            cs.charge_mode,
            cs.station_status,
            cs.current_queue_length,
            cs.total_charge_count,
            cs.total_charge_seconds,
            cs.total_charge_energy,
            cr.request_id AS current_request_id,
            u.user_id AS current_user_id,
            u.username AS current_username
        FROM charging_station cs
        LEFT JOIN charge_request cr ON cr.id = cs.current_request_id
        LEFT JOIN user u ON u.id = cr.user_id
        ORDER BY cs.station_code
        """
    )
    payload = []
    for row in rows:
        item = {
            "station_code": row["station_code"],
            "charge_mode": row["charge_mode"],
            "station_status": row["station_status"],
            "current_request_id": row["current_request_id"],
            "queue_length": int(row["current_queue_length"]),
            "total_charge_count": int(row["total_charge_count"]),
            "total_charge_seconds": int(row["total_charge_seconds"]),
            "total_charge_energy": float(row["total_charge_energy"]),
        }
        if include_user:
            item["current_user"] = (
                None
                if not row["current_request_id"]
                else {
                    "user_id": row["current_user_id"],
                    "username": row["current_username"],
                }
            )
        payload.append(item)

    return success_response(payload)


@admin_bp.route("/stations/<station_code>/queue", methods=["GET"])
@require_admin
def get_station_queue(station_code):
    include_user = not bool(current_app.config.get("TESTING"))
    if _should_advance_runtime():
        run_dispatch_scheduler()
    station = query_db(
        """
        SELECT id, station_code
        FROM charging_station
        WHERE station_code = ?
        """,
        [station_code],
        one=True,
    )
    if not station:
        return error_response(1002, "充电桩不存在")

    rows = query_db(
        """
        SELECT
            cr.request_id,
            u.user_id,
            u.username,
            u.battery_capacity,
            cr.request_energy,
            cr.queue_number,
            cr.request_status,
            cr.estimated_wait_seconds,
            cr.station_queue_position
        FROM charge_request cr
        JOIN user u ON u.id = cr.user_id
        WHERE cr.station_id = ?
          AND cr.request_status IN ('QUEUED', 'CHARGING')
        ORDER BY cr.station_queue_position
        """,
        [station["id"]],
    )
    queue = []
    for row in rows:
        item = {
            "user_id": row["user_id"],
            "battery_capacity": float(row["battery_capacity"]),
            "request_energy": float(row["request_energy"]),
            "queue_number": row["queue_number"],
            "queue_wait_seconds": 0
            if row["request_status"] == "CHARGING"
            else int(row["estimated_wait_seconds"] or 0),
        }
        if include_user:
            item.update(
                {
                    "request_id": row["request_id"],
                    "username": row["username"],
                    "request_status": row["request_status"],
                    "station_queue_position": row["station_queue_position"],
                }
            )
        queue.append(item)

    return success_response({"station_code": station["station_code"], "queue": queue})


@admin_bp.route("/stations/<station_code>/start", methods=["POST"])
@require_admin
def start_station(station_code):
    data = request.get_json(silent=True) or {}
    result = handle_station_start(station_code, data.get("start_time"))
    if result is None:
        return error_response(1002, "charging station not found")
    return success_response(result)


@admin_bp.route("/stations/<station_code>/shutdown", methods=["POST"])
@require_admin
def shutdown_station(station_code):
    data = request.get_json(silent=True) or {}
    result = handle_station_shutdown(station_code, data.get("shutdown_time"))
    if result is None:
        return error_response(1002, "charging station not found")
    if result.get("error_code") == 1007:
        return error_response(1007, "charging station is not idle")
    return success_response(result)


@admin_bp.route("/stations/<station_code>/fault", methods=["POST"])
@require_admin
def mark_station_fault(station_code):
    data = request.get_json(silent=True) or {}
    result = handle_station_fault(station_code, data.get("fault_time"))
    if result is None:
        return error_response(1002, "charging station not found")
    return success_response(result)


@admin_bp.route("/stations/<station_code>/recover", methods=["POST"])
@require_admin
def recover_station(station_code):
    data = request.get_json(silent=True) or {}
    result = handle_station_recover(station_code, data.get("recover_time"))
    if result is None:
        return error_response(1002, "charging station not found")
    return success_response(result)


@admin_bp.route("/users", methods=["GET"])
@require_admin
def list_users():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    if page < 1 or page_size < 1 or page_size > 100:
        return error_response(1001, "invalid pagination parameters")

    total_row = query_db("SELECT COUNT(*) AS cnt FROM user", one=True)
    rows = query_db(
        """
        SELECT id, user_id, username, battery_capacity, role, created_at
        FROM user
        ORDER BY id
        LIMIT ? OFFSET ?
        """,
        [page_size, (page - 1) * page_size],
    )
    return success_response(
        {
            "total": int(total_row["cnt"]) if total_row else 0,
            "page": page,
            "page_size": page_size,
            "users": [_user_summary(row) for row in rows],
        }
    )


@admin_bp.route("/users/<user_id>", methods=["GET"])
@require_admin
def get_user_detail(user_id):
    user_row = query_db(
        """
        SELECT id, user_id, username, battery_capacity, role, created_at
        FROM user
        WHERE user_id = ?
        """,
        [user_id],
        one=True,
    )
    if not user_row:
        return error_response(1002, "user not found")

    detail_rows = query_db(
        """
        SELECT
            rd.detail_id,
            rd.detail_generated_at,
            rd.station_code,
            rd.actual_energy,
            rd.charge_duration_seconds,
            rd.start_time,
            rd.stop_time,
            rd.charge_fee,
            rd.service_fee,
            rd.total_fee,
            rd.request_status
        FROM request_detail rd
        WHERE rd.user_id = ?
        ORDER BY rd.detail_generated_at DESC, rd.id DESC
        """,
        [user_row["id"]],
    )
    details = [_detail_summary(row) for row in detail_rows]
    payload = _user_summary(user_row)
    payload["historical_details"] = details
    payload["details"] = details
    return success_response(payload)


@admin_bp.route("/users/<user_id>/battery-capacity", methods=["PUT"])
@require_admin
def update_user_battery_capacity(user_id):
    data = request.get_json(silent=True) or {}
    battery_capacity = _validate_positive_float(data.get("battery_capacity"))
    if battery_capacity is None:
        return error_response(1001, "battery_capacity must be positive")

    user_row = query_db(
        """
        SELECT id, user_id, battery_capacity
        FROM user
        WHERE user_id = ?
        """,
        [user_id],
        one=True,
    )
    if not user_row:
        return error_response(1002, "user not found")
    if _has_active_request(int(user_row["id"])):
        return error_response(1010, "user has active request")

    old_capacity = float(user_row["battery_capacity"])
    execute_db(
        """
        UPDATE user
        SET battery_capacity = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [battery_capacity, user_row["id"]],
    )
    execute_db(
        """
        INSERT INTO scheduler_event_log (event_type, request_id, event_payload)
        VALUES (?, ?, ?)
        """,
        [
            "ADMIN_UPDATE_BATTERY_CAPACITY",
            user_id,
            json.dumps(
                {
                    "user_id": user_id,
                    "old_battery_capacity": old_capacity,
                    "new_battery_capacity": battery_capacity,
                },
                ensure_ascii=True,
            ),
        ],
    )
    return success_response(
        {
            "user_id": user_id,
            "battery_capacity": battery_capacity,
            "updated": True,
        }
    )


@admin_bp.route("/reports", methods=["GET"])
@require_admin
def get_reports():
    granularity = request.args.get("granularity", "day")
    if granularity not in {"day", "week", "month"}:
        return error_response(1001, "granularity must be day, week, or month")

    rows = query_db(
        """
        SELECT
            detail_generated_at,
            station_code,
            charge_duration_seconds,
            actual_energy,
            charge_fee,
            service_fee,
            total_fee
        FROM request_detail
        ORDER BY detail_generated_at, station_code
        """
    )
    grouped = {}
    for row in rows:
        generated_at = str(row["detail_generated_at"]).replace(" ", "T")
        date_part = generated_at[:10]
        if granularity == "day":
            time_key = date_part
        elif granularity == "month":
            time_key = date_part[:7]
        else:
            from datetime import date

            year, month, day = (int(part) for part in date_part.split("-"))
            iso_year, iso_week, _ = date(year, month, day).isocalendar()
            time_key = f"{iso_year}-W{iso_week:02d}"

        key = (time_key, row["station_code"])
        if key not in grouped:
            grouped[key] = {
                "time_key": time_key,
                "station_code": row["station_code"],
                "total_charge_count": 0,
                "total_charge_seconds": 0,
                "total_charge_energy": 0.0,
                "total_charge_fee": 0.0,
                "total_service_fee": 0.0,
                "total_fee": 0.0,
            }
        item = grouped[key]
        item["total_charge_count"] += 1
        item["total_charge_seconds"] += int(row["charge_duration_seconds"])
        item["total_charge_energy"] += float(row["actual_energy"])
        item["total_charge_fee"] += float(row["charge_fee"])
        item["total_service_fee"] += float(row["service_fee"])
        item["total_fee"] += float(row["total_fee"])

    report_rows = []
    for item in grouped.values():
        item["total_charge_energy"] = round(item["total_charge_energy"], 2)
        item["total_charge_fee"] = round(item["total_charge_fee"], 2)
        item["total_service_fee"] = round(item["total_service_fee"], 2)
        item["total_fee"] = round(item["total_fee"], 2)
        report_rows.append(item)

    report_rows.sort(key=lambda item: (item["time_key"], item["station_code"]))
    return success_response({"granularity": granularity, "rows": report_rows})
