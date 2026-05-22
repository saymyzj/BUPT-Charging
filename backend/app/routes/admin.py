"""V3 admin routes."""

import json
from datetime import datetime
from io import BytesIO

from flask import Blueprint, current_app, request, send_file

from app.enums import DispatchMode, FaultDispatchMode
from app.services.acceptance_service import acceptance_enabled, acceptance_time, record_manual_event
from app.services.queue_model import (
    fault_queue_candidates,
    handle_station_fault,
    handle_station_recover,
    handle_station_shutdown,
    handle_station_start,
    predict_waiting_area_request,
    run_dispatch_scheduler,
    set_dispatch_mode,
    set_fault_dispatch_mode,
)
from app.utils.auth import require_admin
from app.utils.db import execute_db, query_db
from app.utils.response import error_response, success_response

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover
    Workbook = None

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
    return not bool(current_app.config.get("TESTING")) and not acceptance_enabled()


def _poll_scheduler_time():
    return acceptance_time() if acceptance_enabled() else None


def _advance_runtime_for_read() -> None:
    if acceptance_enabled():
        run_dispatch_scheduler(event_time=acceptance_time())
    elif _should_advance_runtime():
        run_dispatch_scheduler()


def _admin_operation_time(data, key: str):
    if acceptance_enabled():
        return acceptance_time((data or {}).get(key))
    return (data or {}).get(key)


def _record_acceptance_station_event(event_type: str, station_code: str, raw_text: str, result=None) -> None:
    if not acceptance_enabled():
        return
    record_manual_event(
        {
            "at": acceptance_time(),
            "event_type": event_type,
            "station_code": station_code,
            "value": 0,
            "raw_text": raw_text,
        },
        status="EXECUTED",
        result=result or {},
    )


def _iso_string(value):
    if value is None:
        return None
    return str(value).replace(" ", "T")


def _parse_dt(value):
    if value is None:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _route_now():
    if acceptance_enabled():
        return _parse_dt(acceptance_time())
    return datetime.now()


def _seconds_until(value, now_dt=None):
    parsed = _parse_dt(value)
    if not parsed:
        return None
    now_dt = now_dt or _route_now()
    return max(0, int((parsed - now_dt).total_seconds()))


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
        "payment_status": row["payment_status"] if "payment_status" in row.keys() else "UNPAID",
        "paid_at": _iso_string(row["paid_at"]) if "paid_at" in row.keys() else None,
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
    _advance_runtime_for_read()
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
    _advance_runtime_for_read()
    station = query_db(
        """
        SELECT id, station_code, power_kw
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
            source.queue_number AS source_queue_number,
            cr.fault_source_request_id,
            cr.request_status,
            cr.estimated_wait_seconds,
            cr.estimated_start_time,
            cr.estimated_finish_time,
            cr.charge_start_time,
            cr.actual_energy,
            cr.station_queue_position
        FROM charge_request cr
        JOIN user u ON u.id = cr.user_id
        LEFT JOIN charge_request source ON source.id = cr.fault_source_request_id
        WHERE cr.station_id = ?
          AND cr.request_status IN ('QUEUED', 'CHARGING')
        ORDER BY cr.station_queue_position
        """,
        [station["id"]],
    )
    queue = []
    now_dt = _route_now()
    expose_runtime_metrics = not bool(current_app.config.get("TESTING"))
    for row in rows:
        remaining_wait_seconds = None
        remaining_charge_seconds = None
        if row["request_status"] == "CHARGING":
            remaining_charge_seconds = _seconds_until(row["estimated_finish_time"], now_dt)
        else:
            remaining_wait_seconds = _seconds_until(row["estimated_start_time"], now_dt)

        charged_energy = float(row["actual_energy"] or 0)
        if row["request_status"] == "CHARGING" and row["charge_start_time"]:
            start_dt = _parse_dt(row["charge_start_time"])
            if start_dt:
                elapsed_seconds = max(0, int((now_dt - start_dt).total_seconds()))
                charged_energy = min(
                    float(row["request_energy"]),
                    max(charged_energy, round(float(station["power_kw"]) * elapsed_seconds / 3600.0, 2)),
                )
        remaining_energy = max(0.0, round(float(row["request_energy"]) - charged_energy, 2))

        item = {
            "user_id": row["user_id"],
            "battery_capacity": float(row["battery_capacity"]),
            "request_energy": float(row["request_energy"]),
            "queue_number": row["queue_number"],
            "source_queue_number": row["source_queue_number"],
            "effective_queue_number": row["source_queue_number"] or row["queue_number"],
            "is_fault_followup": bool(row["fault_source_request_id"]),
            "queue_wait_seconds": 0
            if row["request_status"] == "CHARGING"
            else int(row["estimated_wait_seconds"] or 0),
        }
        if expose_runtime_metrics:
            item.update(
                {
                    "remaining_energy": remaining_energy,
                    "queue_wait_remaining_seconds": remaining_wait_seconds,
                    "charge_remaining_seconds": remaining_charge_seconds,
                    "estimated_start_time": _iso_string(row["estimated_start_time"]),
                    "estimated_finish_time": _iso_string(row["estimated_finish_time"]),
                }
            )
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


@admin_bp.route("/waiting-area", methods=["GET"])
@require_admin
def get_waiting_area():
    _advance_runtime_for_read()

    capacity = _system_config_int(
        "waiting_area_capacity",
        current_app.config.get("WAITING_AREA_SIZE", 6),
    )
    rows = query_db(
        """
        SELECT
            cr.request_id,
            cr.queue_number,
            source.queue_number AS source_queue_number,
            cr.fault_source_request_id,
            cr.charge_mode,
            cr.request_energy,
            cr.waiting_area_order,
            cr.request_time,
            cr.estimated_wait_seconds,
            cr.estimated_start_time,
            cr.estimated_finish_time,
            u.user_id,
            u.username,
            u.battery_capacity
        FROM charge_request cr
        JOIN user u ON u.id = cr.user_id
        LEFT JOIN charge_request source ON source.id = cr.fault_source_request_id
        WHERE cr.request_status = 'WAITING_AREA'
          AND cr.waiting_area_order > 0
        ORDER BY
            cr.charge_mode,
            cr.waiting_area_order,
            cr.id
        """
    )

    payload_rows = []
    fast_count = 0
    slow_count = 0
    expose_runtime_metrics = not bool(current_app.config.get("TESTING"))
    for row in rows:
        prediction = predict_waiting_area_request(str(row["request_id"])) if expose_runtime_metrics else {}
        prediction = prediction or {}
        estimated_start_time = prediction.get("estimated_start_time") or _iso_string(row["estimated_start_time"])
        estimated_finish_time = prediction.get("estimated_finish_time") or _iso_string(row["estimated_finish_time"])
        estimated_wait_seconds = prediction.get("estimated_wait_seconds", row["estimated_wait_seconds"])
        if row["charge_mode"] == "FAST":
            fast_count += 1
        elif row["charge_mode"] == "SLOW":
            slow_count += 1
        payload_rows.append(
            {
                "request_id": row["request_id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "battery_capacity": float(row["battery_capacity"]),
                "charge_mode": row["charge_mode"],
                "request_energy": float(row["request_energy"]),
                "queue_number": row["queue_number"],
                "source_queue_number": row["source_queue_number"],
                "effective_queue_number": row["source_queue_number"] or row["queue_number"],
                "is_fault_followup": bool(row["fault_source_request_id"]),
                "is_fault_queue": False,
                "queue_context": "WAITING_AREA",
                "waiting_area_order": row["waiting_area_order"],
                "request_time": _iso_string(row["request_time"]),
                "estimated_wait_seconds": estimated_wait_seconds,
                "estimated_start_time": estimated_start_time,
                "estimated_finish_time": estimated_finish_time,
            }
        )
        if expose_runtime_metrics:
            payload_rows[-1]["queue_wait_remaining_seconds"] = _seconds_until(estimated_start_time)

    fault_rows = []
    for row in fault_queue_candidates():
        fault_rows.append(
            {
                "request_id": row["request_id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "battery_capacity": float(row["battery_capacity"]),
                "charge_mode": row["charge_mode"],
                "request_energy": float(row["request_energy"]),
                "queue_number": row["queue_number"],
                "source_queue_number": row["source_queue_number"],
                "effective_queue_number": row["effective_queue_number"],
                "is_fault_followup": bool(row["source_queue_number"]),
                "is_fault_queue": True,
                "queue_context": "FAULT_QUEUE",
                "waiting_area_order": row["waiting_area_order"],
                "request_time": _iso_string(row["request_time"]),
                "estimated_wait_seconds": row["estimated_wait_seconds"],
                "estimated_start_time": _iso_string(row["estimated_start_time"]),
                "estimated_finish_time": _iso_string(row["estimated_finish_time"]),
            }
        )
        if expose_runtime_metrics:
            fault_rows[-1]["queue_wait_remaining_seconds"] = _seconds_until(row["estimated_start_time"])

    return success_response(
        {
            "capacity": capacity,
            "total_waiting": len(payload_rows),
            "fast_queue_count": fast_count,
            "slow_queue_count": slow_count,
            "fault_queue_count": len(fault_rows),
            "fault_queue": fault_rows,
            "rows": payload_rows,
        }
    )


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
    result = handle_station_fault(station_code, _admin_operation_time(data, "fault_time"))
    if result is None:
        return error_response(1002, "charging station not found")
    _record_acceptance_station_event("FAULT", station_code, f"手动故障 {station_code}", result)
    return success_response(result)


@admin_bp.route("/stations/<station_code>/recover", methods=["POST"])
@require_admin
def recover_station(station_code):
    data = request.get_json(silent=True) or {}
    result = handle_station_recover(station_code, _admin_operation_time(data, "recover_time"))
    if result is None:
        return error_response(1002, "charging station not found")
    _record_acceptance_station_event("RECOVER", station_code, f"手动恢复 {station_code}", result)
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
            rd.payment_status,
            rd.paid_at,
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


@admin_bp.route("/users/details/export.xlsx", methods=["GET"])
@require_admin
def export_user_details_xlsx():
    if Workbook is None:
        return error_response(1003, "openpyxl is not installed")

    rows = query_db(
        """
        SELECT
            u.user_id,
            rd.station_code,
            rd.start_time,
            rd.stop_time,
            rd.actual_energy,
            rd.charge_fee,
            rd.service_fee,
            rd.total_fee
        FROM request_detail rd
        JOIN user u ON u.id = rd.user_id
        ORDER BY u.user_id, rd.start_time, rd.id
        """
    )
    wb = Workbook()
    ws = wb.active
    ws.title = "用户详单"
    headers = ["车号(用户ID)", "分配的桩号", "充电开始时间", "充电结束时间", "充电电量", "充电费", "服务费", "总费"]
    ws.append(headers)
    for row in rows:
        ws.append(
            [
                row["user_id"],
                row["station_code"],
                _iso_string(row["start_time"]),
                _iso_string(row["stop_time"]),
                float(row["actual_energy"]),
                float(row["charge_fee"]),
                float(row["service_fee"]),
                float(row["total_fee"]),
            ]
        )
    for column in ws.columns:
        width = max(len(str(cell.value or "")) for cell in column) + 2
        ws.column_dimensions[column[0].column_letter].width = min(max(width, 12), 24)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="all-user-request-details.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


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
