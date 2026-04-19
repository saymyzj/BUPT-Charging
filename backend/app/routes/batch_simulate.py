"""V3 batch simulation and acceptance replay routes."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, request

from app.enums import ChargeMode, DispatchMode, FaultDispatchMode, RequestStatus
from app.services.billing_service import get_request_detail
from app.services.queue_model import (
    handle_station_fault,
    handle_station_recover,
    handle_station_shutdown,
    handle_station_start,
    run_extended_scheduler,
    run_normal_scheduler,
    set_dispatch_mode,
    set_fault_dispatch_mode,
)
from app.utils.db import execute_db, query_db
from app.utils.response import error_response, success_response

batch_bp = Blueprint("batch", __name__)


def _parse_time(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _db_string(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%S")
    return _parse_time(value).strftime("%Y-%m-%dT%H:%M:%S")


def _required_scenario_fields():
    return {
        "fast_station_count",
        "slow_station_count",
        "waiting_area_capacity",
        "charging_queue_len",
        "dispatch_mode",
        "fault_dispatch_mode",
    }


def _normalize_scenario(scenario):
    if not isinstance(scenario, dict):
        return scenario
    normalized = dict(scenario)
    if "charging_queue_len" not in normalized and "station_queue_capacity" in normalized:
        normalized["charging_queue_len"] = normalized["station_queue_capacity"]
    return normalized


def _normalize_batch_payload(data):
    if not isinstance(data, dict):
        return data
    normalized = dict(data)
    normalized["scenario"] = _normalize_scenario(data.get("scenario"))
    return normalized


def _validate_batch_request(data):
    errors = []
    if not isinstance(data, dict):
        return False, ["request body must be an object"]
    if not data.get("test_case_id"):
        errors.append("test_case_id is required")

    scenario = data.get("scenario")
    if not isinstance(scenario, dict):
        errors.append("scenario is required")
    else:
        for field in sorted(_required_scenario_fields()):
            if field not in scenario:
                errors.append(f"scenario.{field} is required")
        if scenario.get("dispatch_mode") not in {mode.value for mode in DispatchMode}:
            errors.append("scenario.dispatch_mode is invalid")
        if scenario.get("fault_dispatch_mode") not in {mode.value for mode in FaultDispatchMode}:
            errors.append("scenario.fault_dispatch_mode is invalid")
        for field in ("fast_station_count", "slow_station_count", "waiting_area_capacity", "charging_queue_len"):
            try:
                if int(scenario.get(field, 0)) < (1 if field == "charging_queue_len" else 0):
                    errors.append(f"scenario.{field} is out of range")
            except (TypeError, ValueError):
                errors.append(f"scenario.{field} must be an integer")

    users = data.get("users")
    if not isinstance(users, list):
        errors.append("users must be an array")
    else:
        seen = set()
        for index, user in enumerate(users):
            prefix = f"users[{index}]"
            if not isinstance(user, dict):
                errors.append(f"{prefix} must be an object")
                continue
            for field in ("user_id", "request_time", "charge_mode", "request_energy"):
                if field not in user:
                    errors.append(f"{prefix}.{field} is required")
            if user.get("user_id") in seen:
                errors.append(f"{prefix}.user_id is duplicated")
            elif user.get("user_id"):
                seen.add(user["user_id"])
            if user.get("charge_mode") not in {ChargeMode.FAST.value, ChargeMode.SLOW.value}:
                errors.append(f"{prefix}.charge_mode is invalid")
            try:
                if float(user.get("request_energy", 0)) <= 0:
                    errors.append(f"{prefix}.request_energy must be positive")
            except (TypeError, ValueError):
                errors.append(f"{prefix}.request_energy must be numeric")
            try:
                _parse_time(user.get("request_time"))
            except (TypeError, ValueError):
                errors.append(f"{prefix}.request_time must be ISO8601")

    events = data.get("events", [])
    if events is not None and not isinstance(events, list):
        errors.append("events must be an array")
    elif events:
        for index, event in enumerate(events):
            prefix = f"events[{index}]"
            if not isinstance(event, dict):
                errors.append(f"{prefix} must be an object")
                continue
            if "at" not in event or "type" not in event:
                errors.append(f"{prefix}.at and {prefix}.type are required")
            try:
                _parse_time(event.get("at"))
            except (TypeError, ValueError):
                errors.append(f"{prefix}.at must be ISO8601")

    return len(errors) == 0, errors


def _reset_runtime_tables():
    for table in (
        "request_detail",
        "charging_session",
        "charge_request",
        "charging_station",
        "notification",
        "scheduler_event_log",
        "user",
    ):
        execute_db(f"DELETE FROM {table}")


def _configure_scenario(scenario):
    set_dispatch_mode(scenario["dispatch_mode"])
    set_fault_dispatch_mode(scenario["fault_dispatch_mode"])

    queue_len = int(scenario["charging_queue_len"])
    for index in range(1, int(scenario["fast_station_count"]) + 1):
        execute_db(
            """
            INSERT INTO charging_station (station_code, charge_mode, power_kw, station_status, queue_capacity)
            VALUES (?, 'FAST', 30.0, 'RUNNING', ?)
            """,
            [f"FAST_{index:02d}", queue_len],
        )
    for index in range(1, int(scenario["slow_station_count"]) + 1):
        execute_db(
            """
            INSERT INTO charging_station (station_code, charge_mode, power_kw, station_status, queue_capacity)
            VALUES (?, 'SLOW', 10.0, 'RUNNING', ?)
            """,
            [f"SLOW_{index:02d}", queue_len],
        )

    for key in (
        "fast_station_count",
        "slow_station_count",
        "waiting_area_capacity",
        "charging_queue_len",
        "dispatch_mode",
        "fault_dispatch_mode",
    ):
        execute_db(
            """
            INSERT INTO scheduler_config (config_key, config_value)
            VALUES (?, ?)
            ON CONFLICT(config_key) DO UPDATE SET
                config_value = excluded.config_value,
                updated_at = CURRENT_TIMESTAMP
            """,
            [key, str(scenario[key])],
        )


def _next_request_id():
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


def _next_queue_number(charge_mode):
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


def _next_waiting_order(charge_mode):
    row = query_db(
        """
        SELECT COALESCE(MAX(waiting_area_order), 0) AS max_order
        FROM charge_request
        WHERE charge_mode = ?
          AND request_status = ?
        """,
        [charge_mode, RequestStatus.WAITING_AREA.value],
        one=True,
    )
    return int(row["max_order"]) + 1


def _insert_batch_user(user):
    execute_db(
        """
        INSERT INTO user (user_id, username, password_hash, battery_capacity, role)
        VALUES (?, ?, 'batch-simulate', ?, 'USER')
        """,
        [
            user["user_id"],
            f"batch_{user['user_id']}",
            float(user.get("battery_capacity", 60.0)),
        ],
    )
    user_row = query_db("SELECT id FROM user WHERE user_id = ?", [user["user_id"]], one=True)
    request_id = _next_request_id()
    queue_number = _next_queue_number(user["charge_mode"])
    execute_db(
        """
        INSERT INTO charge_request (
            request_id,
            user_id,
            charge_mode,
            request_energy,
            request_status,
            queue_number,
            waiting_area_order,
            request_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            request_id,
            user_row["id"],
            user["charge_mode"],
            float(user["request_energy"]),
            RequestStatus.WAITING_AREA.value,
            queue_number,
            _next_waiting_order(user["charge_mode"]),
            _db_string(user["request_time"]),
        ],
    )
    return {"user_id": user["user_id"], "request_id": request_id, "queue_number": queue_number}


def _waiting_count():
    row = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charge_request
        WHERE request_status = ?
        """,
        [RequestStatus.WAITING_AREA.value],
        one=True,
    )
    return int(row["cnt"]) if row else 0


def _waiting_area_has_capacity(waiting_area_capacity: int) -> bool:
    return _waiting_count() < waiting_area_capacity


def _rejected_capacity_result(user):
    return {
        "user_id": user["user_id"],
        "request_id": None,
        "queue_number": None,
        "final_status": "REJECTED_WAITING_AREA_FULL",
        "estimated_wait_seconds": 0,
        "detail": None,
        "accepted": False,
        "reject_reason": "WAITING_AREA_FULL",
    }


def _total_station_slots():
    row = query_db(
        """
        SELECT COALESCE(SUM(queue_capacity), 0) AS slots
        FROM charging_station
        WHERE station_status = 'RUNNING'
        """,
        one=True,
    )
    return int(row["slots"]) if row else 0


def _dispatch_for_mode(dispatch_mode_value, event_time, is_last_arrival_group=False):
    if dispatch_mode_value == DispatchMode.NORMAL.value:
        return run_normal_scheduler(event_time)
    if dispatch_mode_value == DispatchMode.EXT_SINGLE_BATCH.value:
        return run_extended_scheduler(event_time, dispatch_mode_value)
    if _waiting_count() >= _total_station_slots() or is_last_arrival_group:
        return run_extended_scheduler(event_time, dispatch_mode_value)
    return {"dispatch_mode": dispatch_mode_value, "scheduled_count": 0, "scheduled": []}


def _apply_event(event):
    event_type = str(event["type"]).upper()
    event_time = _db_string(event["at"])
    result = {"ignored": True, "type": event_type}
    if event_type == "FAULT":
        result = handle_station_fault(event["station_code"], event_time)
    elif event_type in {"RECOVER", "RESTORE"}:
        result = handle_station_recover(event["station_code"], event_time)
    elif event_type == "START":
        result = handle_station_start(event["station_code"], event_time)
    elif event_type == "SHUTDOWN":
        result = handle_station_shutdown(event["station_code"], event_time)
    elif event_type == "DISPATCH_MODE":
        result = {"dispatch_mode": set_dispatch_mode(event["dispatch_mode"])}
    elif event_type == "FAULT_DISPATCH_MODE":
        result = {"fault_dispatch_mode": set_fault_dispatch_mode(event["fault_dispatch_mode"])}

    return {
        "at": event_time,
        "type": event_type,
        "station_code": event.get("station_code"),
        "result": result,
    }


def _next_active_time():
    row = query_db(
        """
        SELECT MIN(estimated_finish_time) AS next_time
        FROM charge_request
        WHERE request_status = ?
          AND estimated_finish_time IS NOT NULL
        """,
        [RequestStatus.CHARGING.value],
        one=True,
    )
    if row and row["next_time"]:
        return row["next_time"]

    row = query_db(
        """
        SELECT MIN(estimated_start_time) AS next_time
        FROM charge_request
        WHERE request_status = ?
          AND estimated_start_time IS NOT NULL
        """,
        [RequestStatus.QUEUED.value],
        one=True,
    )
    return row["next_time"] if row else None


def _active_count():
    row = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charge_request
        WHERE request_status IN (?, ?, ?)
        """,
        [RequestStatus.WAITING_AREA.value, RequestStatus.QUEUED.value, RequestStatus.CHARGING.value],
        one=True,
    )
    return int(row["cnt"]) if row else 0


def _drain(dispatch_mode_value, start_time):
    current_time = start_time
    for _ in range(1000):
        _dispatch_for_mode(dispatch_mode_value, current_time, is_last_arrival_group=True)
        if _active_count() <= 0:
            break
        next_time = _next_active_time()
        if not next_time or next_time == current_time:
            break
        current_time = next_time


def _serialize_result(original):
    if original.get("rejected"):
        return _rejected_capacity_result(original["user"])

    row = query_db(
        """
        SELECT
            cr.request_id,
            cr.queue_number,
            cr.request_status,
            cr.estimated_wait_seconds,
            cr.request_time,
            cr.charge_stop_time,
            cr.id AS internal_request_id,
            u.user_id
        FROM charge_request cr
        JOIN user u ON u.id = cr.user_id
        WHERE cr.request_id = ?
        """,
        [original["request_id"]],
        one=True,
    )
    detail = get_request_detail(original["request_id"]) if row else None
    followup_rows = (
        query_db(
            """
            SELECT request_id
            FROM charge_request
            WHERE fault_source_request_id = ?
            ORDER BY id
            """,
            [row["internal_request_id"]],
        )
        if row
        else []
    )
    followup_request_ids = [item["request_id"] for item in followup_rows]
    return {
        "user_id": original["user_id"],
        "request_id": original["request_id"],
        "queue_number": original["queue_number"],
        "final_status": row["request_status"] if row else "UNKNOWN",
        "estimated_wait_seconds": int(row["estimated_wait_seconds"] or 0) if row else 0,
        "detail": detail,
        "accepted": True,
        "followup_request_id": followup_request_ids[0] if followup_request_ids else None,
        "followup_request_ids": followup_request_ids,
    }


def _build_summary(results):
    total_users = len(results)
    completed_results = [item for item in results if item["detail"]]
    completed_users = len(completed_results)
    rejected_users = len([item for item in results if not item.get("accepted", True)])
    avg_wait_seconds = (
        round(sum(item["estimated_wait_seconds"] for item in completed_results) / completed_users, 2)
        if completed_users
        else 0.0
    )

    finish_seconds = []
    for item in completed_results:
        detail = item["detail"]
        req = query_db(
            "SELECT request_time FROM charge_request WHERE request_id = ?",
            [item["request_id"]],
            one=True,
        )
        if req:
            finish_seconds.append(
                max(0, int((_parse_time(detail["stop_time"]) - _parse_time(req["request_time"])).total_seconds()))
            )
    total_finish_seconds = sum(finish_seconds)
    avg_finish_seconds = round(total_finish_seconds / completed_users, 2) if completed_users else 0.0

    total_charge_seconds = sum(item["detail"]["charge_duration_seconds"] for item in completed_results)
    station_count_row = query_db("SELECT COUNT(*) AS cnt FROM charging_station", one=True)
    station_count = int(station_count_row["cnt"]) if station_count_row else 0
    span_seconds = max(finish_seconds) if finish_seconds else 0
    station_utilization = (
        round(total_charge_seconds / (station_count * span_seconds), 4)
        if station_count > 0 and span_seconds > 0
        else 0.0
    )

    return {
        "total_users": total_users,
        "completed_users": completed_users,
        "rejected_users": rejected_users,
        "avg_wait_seconds": avg_wait_seconds,
        "avg_finish_seconds": avg_finish_seconds,
        "total_finish_seconds": total_finish_seconds,
        "station_utilization": station_utilization,
    }


def _run_batch_simulation(data):
    scenario = data["scenario"]
    users = sorted(data.get("users", []), key=lambda item: _parse_time(item["request_time"]))
    events = sorted(data.get("events", []), key=lambda item: _parse_time(item["at"]))
    dispatch_mode_value = scenario["dispatch_mode"]
    waiting_area_capacity = int(scenario["waiting_area_capacity"])

    _reset_runtime_tables()
    _configure_scenario(scenario)

    originals = []
    events_result = []
    event_index = 0
    grouped_times = sorted({_db_string(user["request_time"]) for user in users})
    for group_index, at_time in enumerate(grouped_times):
        while event_index < len(events) and _db_string(events[event_index]["at"]) <= at_time:
            event_result = _apply_event(events[event_index])
            dispatch_result = _dispatch_for_mode(dispatch_mode_value, _db_string(events[event_index]["at"]))
            event_result["dispatch_after_event"] = dispatch_result
            events_result.append(event_result)
            event_index += 1

        for user in [item for item in users if _db_string(item["request_time"]) == at_time]:
            if _waiting_area_has_capacity(waiting_area_capacity):
                originals.append(_insert_batch_user(user))
            else:
                originals.append({"user_id": user["user_id"], "rejected": True, "user": user})

        _dispatch_for_mode(
            dispatch_mode_value,
            at_time,
            is_last_arrival_group=group_index == len(grouped_times) - 1,
        )

    while event_index < len(events):
        event_result = _apply_event(events[event_index])
        dispatch_result = _dispatch_for_mode(
            dispatch_mode_value,
            _db_string(events[event_index]["at"]),
            is_last_arrival_group=True,
        )
        event_result["dispatch_after_event"] = dispatch_result
        events_result.append(event_result)
        event_index += 1

    timeline_times = grouped_times + [_db_string(event["at"]) for event in events]
    drain_start = max(timeline_times) if timeline_times else datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    _drain(dispatch_mode_value, drain_start)

    results = [_serialize_result(original) for original in originals]
    return {
        "test_case_id": data["test_case_id"],
        "scenario": {
            "fast_station_count": int(scenario["fast_station_count"]),
            "slow_station_count": int(scenario["slow_station_count"]),
            "waiting_area_capacity": int(scenario["waiting_area_capacity"]),
            "charging_queue_len": int(scenario["charging_queue_len"]),
            "dispatch_mode": scenario["dispatch_mode"],
            "fault_dispatch_mode": scenario["fault_dispatch_mode"],
        },
        "summary": _build_summary(results),
        "events_result": events_result,
        "results": results,
    }


@batch_bp.route("/batch-simulate", methods=["POST"])
@batch_bp.route("/simulate", methods=["POST"])
def batch_simulate():
    data = _normalize_batch_payload(request.get_json(silent=True) or {})
    is_valid, errors = _validate_batch_request(data)
    if not is_valid:
        return error_response(1001, "Invalid parameters", {"errors": errors})
    try:
        return success_response(_run_batch_simulation(data))
    except Exception as exc:
        return error_response(2001, f"batch simulation failed: {exc}")
