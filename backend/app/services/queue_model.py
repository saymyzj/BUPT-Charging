"""V3 waiting-area, fixed-queue, and NORMAL scheduling services."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from app.enums import RequestStatus
from app.services.billing_service import ensure_request_detail
from app.utils.db import execute_db, query_db

QUEUE_ACTIVE_STATUSES = (RequestStatus.QUEUED.value, RequestStatus.CHARGING.value)


LIFECYCLE_LABELS = {
    "REQUEST_SUBMITTED": "请求已提交",
    "WAITING_AREA_ENTERED": "等候区排队",
    "ASSIGNED_TO_STATION": "分配到桩队列",
    "CHARGING_STARTED": "充电中",
    "FAULT_INTERRUPTED": "故障中断",
    "FAULT_REQUEUED": "重新排队",
    "CHARGING_COMPLETED": "充电完成",
    "CHARGING_COMPLETED_EARLY": "提前结束充电",
    "REQUEST_CANCELLED": "请求已取消",
}


def parse_iso_datetime(value):
    if value is None:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def iso_string(value):
    if value is None:
        return None
    return str(value).replace(" ", "T")


def _db_string(value):
    if value is None:
        return None
    return parse_iso_datetime(value).strftime("%Y-%m-%dT%H:%M:%S") if not isinstance(value, datetime) else value.strftime("%Y-%m-%dT%H:%M:%S")


def _event_datetime(event_time=None):
    if event_time is None:
        return datetime.now()
    return parse_iso_datetime(event_time)


def log_request_lifecycle(request_id: str, event_type: str, event_time=None, **payload) -> None:
    if not request_id:
        return
    occurred_at = _db_string(_event_datetime(event_time)) if event_time is not None else _db_string(datetime.now())
    data = {
        "at": occurred_at,
        "label": payload.pop("label", LIFECYCLE_LABELS.get(event_type, event_type)),
        **payload,
    }
    execute_db(
        """
        INSERT INTO scheduler_event_log (event_type, request_id, station_id, event_payload)
        VALUES (?, ?, ?, ?)
        """,
        [
            event_type,
            str(request_id),
            data.get("station_code") or data.get("station_id"),
            json.dumps(data, ensure_ascii=False),
        ],
    )


def _request_chain_ids(request_id: str) -> list[str]:
    chain: list[str] = []
    current = request_id
    seen: set[str] = set()
    while current and current not in seen:
        seen.add(current)
        row = query_db(
            """
            SELECT cr.request_id, source.request_id AS source_request_id
            FROM charge_request cr
            LEFT JOIN charge_request source ON source.id = cr.fault_source_request_id
            WHERE cr.request_id = ?
            """,
            [current],
            one=True,
        )
        if not row:
            break
        chain.append(str(row["request_id"]))
        current = row["source_request_id"]
    return list(reversed(chain))


def request_lifecycle(request_id: str) -> list[dict]:
    request_ids = _request_chain_ids(request_id) or [request_id]
    placeholders = ",".join("?" for _ in request_ids)
    rows = query_db(
        f"""
        SELECT id, event_type, request_id, event_payload, created_at
        FROM scheduler_event_log
        WHERE request_id IN ({placeholders})
          AND event_type IN ({",".join("?" for _ in LIFECYCLE_LABELS)})
        ORDER BY id
        """,
        [*request_ids, *LIFECYCLE_LABELS.keys()],
    )
    events = []
    for row in rows:
        try:
            payload = json.loads(row["event_payload"] or "{}")
        except (TypeError, json.JSONDecodeError):
            payload = {}
        label = payload.get("label") or LIFECYCLE_LABELS.get(row["event_type"], row["event_type"])
        events.append(
            {
                "id": int(row["id"]),
                "request_id": row["request_id"],
                "event_type": row["event_type"],
                "label": label,
                "at": payload.get("at") or row["created_at"],
                "station_code": payload.get("station_code"),
                "queue_position": payload.get("queue_position"),
                "description": payload.get("description"),
                "state": payload.get("state") or _lifecycle_state(row["event_type"]),
            }
        )
    if events:
        return sorted(events, key=lambda item: (str(item.get("at") or ""), int(item["id"])))
    return _fallback_lifecycle(request_id)


def _lifecycle_state(event_type: str) -> str:
    if event_type == "FAULT_INTERRUPTED":
        return "danger"
    if event_type == "FAULT_REQUEUED":
        return "warning"
    if event_type in {"CHARGING_COMPLETED", "CHARGING_COMPLETED_EARLY", "REQUEST_CANCELLED"}:
        return "done"
    return "done"


def _fallback_lifecycle(request_id: str) -> list[dict]:
    row = query_db(
        """
        SELECT request_id, request_status, request_time, charge_start_time, charge_stop_time, station_queue_position, station_id
        FROM charge_request
        WHERE request_id = ?
        """,
        [request_id],
        one=True,
    )
    if not row:
        return []
    events = [
        {
            "id": -2,
            "request_id": request_id,
            "event_type": "REQUEST_SUBMITTED",
            "label": "请求已提交",
            "at": _db_string(row["request_time"]),
            "station_code": None,
            "queue_position": None,
            "description": None,
            "state": "done",
        }
    ]
    if row["request_status"] in QUEUE_ACTIVE_STATUSES or row["request_status"] in {
        RequestStatus.COMPLETED.value,
        RequestStatus.COMPLETED_EARLY.value,
        RequestStatus.FAULT_INTERRUPTED.value,
    }:
        station = query_db("SELECT station_code FROM charging_station WHERE id = ?", [row["station_id"]], one=True)
        events.append(
            {
                "id": -1,
                "request_id": request_id,
                "event_type": "ASSIGNED_TO_STATION",
                "label": "分配到桩队列",
                "at": _db_string(row["request_time"]),
                "station_code": station["station_code"] if station else None,
                "queue_position": row["station_queue_position"],
                "description": None,
                "state": "done",
            }
        )
    return events


def service_seconds_for_request(request_energy: float, power_kw: float) -> int:
    if power_kw <= 0:
        return 0
    return max(0, int(round(float(request_energy) / float(power_kw) * 3600)))


def _request_service_seconds(req_row, power_kw: float) -> int:
    return service_seconds_for_request(float(req_row["request_energy"]), float(power_kw))


def _dispatch_mode():
    row = query_db(
        "SELECT config_value FROM scheduler_config WHERE config_key = 'dispatch_mode'",
        one=True,
    )
    return (row["config_value"] if row else "NORMAL") or "NORMAL"


def dispatch_mode():
    return _dispatch_mode()


def set_dispatch_mode(mode: str) -> str:
    execute_db(
        """
        UPDATE scheduler_config
        SET config_value = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE config_key = 'dispatch_mode'
        """,
        [mode],
    )
    execute_db(
        """
        INSERT INTO scheduler_event_log (event_type, event_payload)
        VALUES (?, ?)
        """,
        ["ADMIN_UPDATE_DISPATCH_MODE", f'{{"dispatch_mode":"{mode}"}}'],
    )
    return mode


def fault_dispatch_mode():
    row = query_db(
        "SELECT config_value FROM scheduler_config WHERE config_key = 'fault_dispatch_mode'",
        one=True,
    )
    return (row["config_value"] if row else "TIME_ORDER") or "TIME_ORDER"


def set_fault_dispatch_mode(mode: str) -> str:
    execute_db(
        """
        UPDATE scheduler_config
        SET config_value = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE config_key = 'fault_dispatch_mode'
        """,
        [mode],
    )
    return mode


def _load_station(station_code: str):
    return query_db(
        """
        SELECT id, station_code, charge_mode, station_status, queue_capacity, power_kw
        FROM charging_station
        WHERE station_code = ?
        """,
        [station_code],
        one=True,
    )


def _active_station_rows(station_id: int):
    return query_db(
        """
        SELECT
            id,
            request_id,
            request_time,
            request_energy,
            request_status,
            station_queue_position,
            estimated_wait_seconds,
            estimated_start_time,
            estimated_finish_time,
            charge_start_time
        FROM charge_request
        WHERE station_id = ?
          AND request_status IN (?, ?)
        ORDER BY station_queue_position, id
        """,
        [station_id, *QUEUE_ACTIVE_STATUSES],
    )


def _running_stations(charge_mode: str | None = None):
    sql = """
        SELECT id, station_code, charge_mode, power_kw, queue_capacity
        FROM charging_station
        WHERE station_status = 'RUNNING'
    """
    args = []
    if charge_mode:
        sql += " AND charge_mode = ?"
        args.append(charge_mode)
    sql += " ORDER BY charge_mode, station_code"
    return query_db(sql, args)


def _queue_number_index(queue_number: str) -> int:
    try:
        return int(str(queue_number)[1:])
    except (TypeError, ValueError):
        return 0


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
    prefix = "F" if charge_mode == "FAST" else "T"
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


def _next_waiting_area_order(charge_mode: str) -> int:
    row = query_db(
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
    return int(row["max_order"]) + 1


def _active_count(station_id: int) -> int:
    row = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM charge_request
        WHERE station_id = ?
          AND request_status IN (?, ?)
        """,
        [station_id, *QUEUE_ACTIVE_STATUSES],
        one=True,
    )
    return int(row["cnt"]) if row else 0


def _fault_waiting_candidates(charge_mode: str):
    return query_db(
        """
        SELECT
            cr.id,
            cr.request_id,
            cr.charge_mode,
            cr.request_energy,
            cr.queue_number,
            COALESCE(source.queue_number, cr.queue_number) AS fault_order_queue_number
        FROM charge_request cr
        LEFT JOIN charge_request source ON source.id = cr.fault_source_request_id
        WHERE cr.charge_mode = ?
          AND cr.request_status = ?
          AND cr.waiting_area_order = 0
        ORDER BY CAST(SUBSTR(COALESCE(source.queue_number, cr.queue_number), 2) AS INTEGER), cr.id
        """,
        [charge_mode, RequestStatus.WAITING_AREA.value],
    )


def fault_queue_candidates(charge_mode: str | None = None):
    sql = """
        SELECT
            cr.id,
            cr.request_id,
            cr.charge_mode,
            cr.request_energy,
            cr.queue_number,
            cr.waiting_area_order,
            cr.request_time,
            cr.estimated_wait_seconds,
            cr.estimated_start_time,
            cr.estimated_finish_time,
            source.queue_number AS source_queue_number,
            COALESCE(source.queue_number, cr.queue_number) AS effective_queue_number,
            u.user_id,
            u.username,
            u.battery_capacity
        FROM charge_request cr
        JOIN user u ON u.id = cr.user_id
        LEFT JOIN charge_request source ON source.id = cr.fault_source_request_id
        WHERE cr.request_status = ?
          AND cr.waiting_area_order = 0
    """
    args = [RequestStatus.WAITING_AREA.value]
    if charge_mode:
        sql += " AND cr.charge_mode = ?"
        args.append(charge_mode)
    sql += """
        ORDER BY
            cr.charge_mode,
            CAST(SUBSTR(COALESCE(source.queue_number, cr.queue_number), 2) AS INTEGER),
            cr.id
    """
    return query_db(sql, args)


def _station_workload_seconds(station_id: int, as_of: datetime, power_kw: float) -> int:
    workload = 0
    for row in _active_station_rows(station_id):
        if row["request_status"] == RequestStatus.CHARGING.value and row["estimated_finish_time"]:
            workload += max(0, int((parse_iso_datetime(row["estimated_finish_time"]) - as_of).total_seconds()))
        else:
            workload += _request_service_seconds(row, power_kw)
    return workload


def _resequence_station_queue(station_id: int) -> None:
    rows = _active_station_rows(station_id)
    for index, row in enumerate(rows, start=1):
        if int(row["station_queue_position"]) != index:
            execute_db(
                """
                UPDATE charge_request
                SET station_queue_position = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                [index, row["id"]],
            )


def _refresh_station_runtime(station_id: int, anchor_time: datetime) -> None:
    station = query_db(
        """
        SELECT id, power_kw
        FROM charging_station
        WHERE id = ?
        """,
        [station_id],
        one=True,
    )
    if not station:
        return

    rows = _active_station_rows(station_id)
    current_request_id = None
    cursor = anchor_time
    charging_seen = False

    for row in rows:
        request_time = parse_iso_datetime(row["request_time"])
        service_seconds = _request_service_seconds(row, float(station["power_kw"]))

        if row["request_status"] == RequestStatus.CHARGING.value and not charging_seen:
            charging_seen = True
            current_request_id = row["id"]
            start_time = parse_iso_datetime(row["charge_start_time"] or row["estimated_start_time"]) or max(request_time, anchor_time)
            finish_time = parse_iso_datetime(row["estimated_finish_time"]) or (start_time + timedelta(seconds=service_seconds))
        else:
            start_time = max(cursor, request_time)
            finish_time = start_time + timedelta(seconds=service_seconds)

        wait_seconds = max(0, int((start_time - request_time).total_seconds()))
        execute_db(
            """
            UPDATE charge_request
            SET estimated_wait_seconds = ?,
                estimated_start_time = ?,
                estimated_finish_time = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [
                wait_seconds,
                _db_string(start_time),
                _db_string(finish_time),
                row["id"],
            ],
        )
        cursor = finish_time

    execute_db(
        """
        UPDATE charging_station
        SET current_queue_length = ?,
            current_request_id = ?,
            available_time = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [
            len(rows),
            current_request_id,
            _db_string(cursor if rows else anchor_time),
            station_id,
        ],
    )


def sync_station_queue_lengths(anchor_time=None) -> None:
    anchor_dt = _event_datetime(anchor_time)
    for station in _running_stations():
        _refresh_station_runtime(int(station["id"]), anchor_dt)


def _reset_station_after_fault(station_id: int, event_dt: datetime) -> None:
    execute_db(
        """
        UPDATE charging_station
        SET station_status = 'FAULT',
            current_queue_length = 0,
            current_request_id = NULL,
            available_time = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [_db_string(event_dt), station_id],
    )


def _mark_requests_for_fault_requeue(request_rows, event_time=None) -> list[str]:
    request_ids = []
    for row in request_rows:
        request_ids.append(str(row["request_id"]))
        from_station_code = row["station_code"] if "station_code" in row.keys() else None
        execute_db(
            """
            UPDATE charge_request
            SET request_status = ?,
                station_id = NULL,
                station_queue_position = NULL,
                waiting_area_order = 0,
                estimated_wait_seconds = NULL,
                estimated_start_time = NULL,
                estimated_finish_time = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [RequestStatus.WAITING_AREA.value, row["id"]],
        )
        log_request_lifecycle(
            str(row["request_id"]),
            "FAULT_REQUEUED",
            event_time=event_time or datetime.now(),
            station_code=from_station_code,
            description=f"原 {from_station_code} 队列因故障重新进入调度" if from_station_code else "因充电桩故障重新进入调度",
        )
    return request_ids


def _fault_requeue_rows_for_priority(station_id: int):
    return query_db(
        """
        SELECT cr.id, cr.request_id, cr.queue_number, cs.station_code
        FROM charge_request cr
        JOIN charging_station cs ON cs.id = cr.station_id
        WHERE cr.station_id = ?
          AND cr.request_status = ?
        ORDER BY cr.station_queue_position, cr.id
        """,
        [station_id, RequestStatus.QUEUED.value],
    )


def _same_mode_waiting_rows_outside_station(station_id: int, charge_mode: str):
    return query_db(
        """
        SELECT cr.id, cr.request_id, cr.queue_number, cs.station_code
        FROM charge_request cr
        JOIN charging_station cs ON cs.id = cr.station_id
        WHERE cr.station_id != ?
          AND cs.charge_mode = ?
          AND cr.request_status = ?
        ORDER BY CAST(SUBSTR(cr.queue_number, 2) AS INTEGER), cr.id
        """,
        [station_id, charge_mode, RequestStatus.QUEUED.value],
    )


def _fault_requeue_rows_for_time_order(charge_mode: str):
    return query_db(
        """
        SELECT cr.id, cr.request_id, cr.queue_number, cs.station_code
        FROM charge_request cr
        JOIN charging_station cs ON cs.id = cr.station_id
        WHERE cs.charge_mode = ?
          AND cr.request_status = ?
        ORDER BY CAST(SUBSTR(cr.queue_number, 2) AS INTEGER), cr.id
        """,
        [charge_mode, RequestStatus.QUEUED.value],
    )


def _create_remaining_fault_request(
    interrupted_row,
    remaining_energy: float,
    event_dt: datetime,
    include_in_fault_requeue: bool = False,
    from_station_code: str | None = None,
) -> str | None:
    if remaining_energy <= 0:
        return None

    request_id = _next_request_id()
    queue_number = str(interrupted_row["queue_number"])
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
            request_time,
            fault_source_request_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            request_id,
            interrupted_row["user_id"],
            interrupted_row["charge_mode"],
            round(remaining_energy, 2),
            RequestStatus.WAITING_AREA.value,
            queue_number,
            0 if include_in_fault_requeue else _next_waiting_area_order(str(interrupted_row["charge_mode"])),
            _db_string(event_dt),
            interrupted_row["id"],
        ],
    )
    log_request_lifecycle(
        request_id,
        "FAULT_REQUEUED",
        event_time=event_dt,
        station_code=from_station_code,
        source_request_id=interrupted_row["request_id"],
        source_queue_number=interrupted_row["queue_number"],
        description=f"{interrupted_row['request_id']} 在 {from_station_code or '原充电桩'} 被中断后，剩余电量重新进入调度",
    )
    return request_id


def _interrupt_charging_request(
    req_row,
    station,
    event_dt: datetime,
    include_remaining_in_fault_requeue: bool = False,
) -> tuple[str | None, str | None]:
    start_dt = parse_iso_datetime(req_row["charge_start_time"] or event_dt)
    if event_dt < start_dt:
        event_dt = start_dt

    duration_seconds = max(0, int((event_dt - start_dt).total_seconds()))
    actual_energy = round(float(station["power_kw"]) * duration_seconds / 3600.0, 2)
    actual_energy = min(actual_energy, float(req_row["request_energy"]))

    if actual_energy <= 0:
        _mark_requests_for_fault_requeue([req_row], event_dt)
        return None, str(req_row["request_id"])

    remaining_energy = round(float(req_row["request_energy"]) - actual_energy, 2)
    execute_db(
        """
        UPDATE charge_request
        SET request_status = ?,
            actual_energy = ?,
            charge_stop_time = ?,
            charge_duration_seconds = ?,
            station_queue_position = NULL,
            waiting_area_order = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [
            RequestStatus.FAULT_INTERRUPTED.value,
            actual_energy,
            _db_string(event_dt),
            duration_seconds,
            req_row["id"],
        ],
    )
    execute_db(
        """
        UPDATE charging_session
        SET end_time = ?,
            actual_energy = ?,
            status = ?
        WHERE request_id = ?
        """,
        [
            _db_string(event_dt),
            actual_energy,
            RequestStatus.FAULT_INTERRUPTED.value,
            req_row["id"],
        ],
    )
    execute_db(
        """
        UPDATE charging_station
        SET total_charge_count = total_charge_count + 1,
            total_charge_seconds = total_charge_seconds + ?,
            total_charge_energy = total_charge_energy + ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [duration_seconds, actual_energy, station["id"]],
    )
    ensure_request_detail(str(req_row["request_id"]))
    log_request_lifecycle(
        str(req_row["request_id"]),
        "FAULT_INTERRUPTED",
        event_time=event_dt,
        station_code=str(station["station_code"]),
        description=f"{req_row['request_id']} 在 {station['station_code']} 被中断",
    )
    remaining_request_id = _create_remaining_fault_request(
        req_row,
        remaining_energy,
        event_dt,
        include_in_fault_requeue=include_remaining_in_fault_requeue,
        from_station_code=str(station["station_code"]),
    )
    return str(req_row["request_id"]), remaining_request_id


def run_fault_requeue_scheduler(charge_mode: str, event_time=None):
    event_dt = _event_datetime(event_time)
    for station in _running_stations(charge_mode):
        _settle_station_until(int(station["id"]), event_dt)

    scheduled = []
    while True:
        candidates = _fault_waiting_candidates(charge_mode)
        if not candidates:
            break
        candidate = candidates[0]
        target_station = _best_station_for_waiting_request(candidate, event_dt)
        if not target_station:
            break
        ok, _ = enqueue_request(
            str(target_station["station_code"]),
            str(candidate["request_id"]),
            event_dt,
        )
        if not ok:
            break
        scheduled.append(
            {
                "request_id": str(candidate["request_id"]),
                "target_station_code": str(target_station["station_code"]),
            }
        )

    for station in _running_stations(charge_mode):
        _settle_station_until(int(station["id"]), event_dt)
    return scheduled


def _move_fault_requeue_to_public_waiting(request_ids: list[str], charge_mode: str) -> None:
    active_ids = []
    for request_id in request_ids:
        row = query_db(
            """
            SELECT id
            FROM charge_request
            WHERE request_id = ?
              AND request_status = ?
              AND waiting_area_order = 0
            """,
            [request_id, RequestStatus.WAITING_AREA.value],
            one=True,
        )
        if not row:
            continue
        active_ids.append((request_id, row["id"]))
    if not active_ids:
        return
    execute_db(
        """
        UPDATE charge_request
        SET waiting_area_order = waiting_area_order + ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE charge_mode = ?
          AND request_status = ?
          AND waiting_area_order > 0
        """,
        [len(active_ids), charge_mode, RequestStatus.WAITING_AREA.value],
    )
    for index, (_, row_id) in enumerate(active_ids, start=1):
        execute_db(
            """
            UPDATE charge_request
            SET waiting_area_order = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [index, row_id],
        )


def run_priority_fault_requeue_scheduler(
    charge_mode: str,
    priority_request_ids: list[str],
    displaced_request_ids: list[str] | None = None,
    event_time=None,
):
    event_dt = _event_datetime(event_time)
    for station in _running_stations(charge_mode):
        _settle_station_until(int(station["id"]), event_dt)

    scheduled = []
    remaining_priority = set(priority_request_ids)
    displaced_ids = list(displaced_request_ids or [])

    while True:
        candidates = _fault_waiting_candidates(charge_mode)
        if not candidates:
            break
        priority_candidates = [row for row in candidates if str(row["request_id"]) in remaining_priority]
        if remaining_priority and not priority_candidates:
            break
        candidate = priority_candidates[0] if priority_candidates else candidates[0]
        target_station = _best_station_for_waiting_request(candidate, event_dt)
        if not target_station:
            break
        ok, _ = enqueue_request(
            str(target_station["station_code"]),
            str(candidate["request_id"]),
            event_dt,
        )
        if not ok:
            break
        scheduled.append(
            {
                "request_id": str(candidate["request_id"]),
                "target_station_code": str(target_station["station_code"]),
            }
        )
        remaining_priority.discard(str(candidate["request_id"]))

    if not remaining_priority and displaced_ids:
        _move_fault_requeue_to_public_waiting(displaced_ids, charge_mode)
        normal_result = run_normal_scheduler(event_dt, charge_mode, ignore_fault_queue=True)
        scheduled.extend(normal_result["scheduled"])

    for station in _running_stations(charge_mode):
        _settle_station_until(int(station["id"]), event_dt)
    return scheduled


def handle_station_fault(station_code: str, fault_time=None):
    event_dt = _event_datetime(fault_time)
    station = _load_station(station_code)
    if not station:
        return None
    if station["station_status"] == "FAULT":
        return {
            "station_code": station["station_code"],
            "station_status": "FAULT",
            "fault_dispatch_mode": fault_dispatch_mode(),
            "interrupted_request_id": None,
            "remaining_request_id": None,
            "requeued_request_ids": [],
            "scheduled": [],
        }

    _settle_station_until(int(station["id"]), event_dt)
    station = _load_station(station_code)

    mode = fault_dispatch_mode()
    current_req = query_db(
        """
        SELECT
            id,
            request_id,
            user_id,
            charge_mode,
            request_energy,
            request_status,
            queue_number,
            charge_start_time
        FROM charge_request
        WHERE station_id = ?
          AND request_status = ?
        ORDER BY station_queue_position
        LIMIT 1
        """,
        [station["id"], RequestStatus.CHARGING.value],
        one=True,
    )
    interrupted_request_id = None
    remaining_request_id = None
    if current_req:
        interrupted_request_id, remaining_request_id = _interrupt_charging_request(
            current_req,
            station,
            event_dt,
            include_remaining_in_fault_requeue=True,
        )

    if mode == "PRIORITY":
        requeue_rows = _fault_requeue_rows_for_priority(int(station["id"]))
        displaced_rows = _same_mode_waiting_rows_outside_station(int(station["id"]), str(station["charge_mode"]))
    else:
        requeue_rows = _fault_requeue_rows_for_time_order(str(station["charge_mode"]))
        displaced_rows = []

    requeued_request_ids = _mark_requests_for_fault_requeue(requeue_rows, event_dt)
    displaced_request_ids = []
    if mode == "PRIORITY":
        displaced_request_ids = _mark_requests_for_fault_requeue(displaced_rows, event_dt)
    if current_req and interrupted_request_id is None and str(current_req["request_id"]) not in requeued_request_ids:
        requeued_request_ids.append(str(current_req["request_id"]))

    _reset_station_after_fault(int(station["id"]), event_dt)
    if mode == "PRIORITY":
        priority_request_ids = []
        if remaining_request_id:
            priority_request_ids.append(str(remaining_request_id))
        priority_request_ids.extend(requeued_request_ids)
        scheduled = run_priority_fault_requeue_scheduler(
            str(station["charge_mode"]),
            priority_request_ids,
            displaced_request_ids,
            event_dt,
        )
    else:
        scheduled = run_fault_requeue_scheduler(str(station["charge_mode"]), event_dt)

    return {
        "station_code": station["station_code"],
        "station_status": "FAULT",
        "fault_dispatch_mode": mode,
        "interrupted_request_id": interrupted_request_id,
        "remaining_request_id": remaining_request_id,
        "requeued_request_ids": requeued_request_ids,
        "scheduled": scheduled,
    }


def handle_station_recover(station_code: str, recover_time=None):
    event_dt = _event_datetime(recover_time)
    station = _load_station(station_code)
    if not station:
        return None

    execute_db(
        """
        UPDATE charging_station
        SET station_status = 'RUNNING',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [station["id"]],
    )
    station = _load_station(station_code)

    for running_station in _running_stations(str(station["charge_mode"])):
        _settle_station_until(int(running_station["id"]), event_dt)

    requeue_rows = _fault_requeue_rows_for_time_order(str(station["charge_mode"]))
    requeued_request_ids = _mark_requests_for_fault_requeue(requeue_rows, event_dt)
    scheduled = run_fault_requeue_scheduler(str(station["charge_mode"]), event_dt)
    normal_result = run_normal_scheduler(event_dt, str(station["charge_mode"]))

    return {
        "station_code": station["station_code"],
        "station_status": "RUNNING",
        "requeued_request_ids": requeued_request_ids,
        "scheduled": scheduled + normal_result["scheduled"],
    }


def handle_station_start(station_code: str, start_time=None):
    event_dt = _event_datetime(start_time)
    station = _load_station(station_code)
    if not station:
        return None

    if station["station_status"] == "FAULT":
        return handle_station_recover(station_code, event_dt)

    execute_db(
        """
        UPDATE charging_station
        SET station_status = 'RUNNING',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [station["id"]],
    )
    station = _load_station(station_code)
    scheduled = run_fault_requeue_scheduler(str(station["charge_mode"]), event_dt)
    normal_result = run_normal_scheduler(event_dt, str(station["charge_mode"]))

    return {
        "station_code": station["station_code"],
        "station_status": "RUNNING",
        "scheduled": scheduled + normal_result["scheduled"],
    }


def handle_station_shutdown(station_code: str, shutdown_time=None):
    event_dt = _event_datetime(shutdown_time)
    station = _load_station(station_code)
    if not station:
        return None

    if station["station_status"] == "RUNNING":
        _settle_station_until(int(station["id"]), event_dt)

    if _active_count(int(station["id"])) > 0:
        return {
            "error_code": 1007,
            "station_code": station["station_code"],
            "station_status": station["station_status"],
        }

    execute_db(
        """
        UPDATE charging_station
        SET station_status = 'SHUTDOWN',
            current_queue_length = 0,
            current_request_id = NULL,
            available_time = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [_db_string(event_dt), station["id"]],
    )
    return {
        "station_code": station["station_code"],
        "station_status": "SHUTDOWN",
    }


def settle_station_until_time(station_id: int, event_time=None) -> None:
    _settle_station_until(station_id, _event_datetime(event_time))


def refresh_station_after_queue_change(station_id: int, event_time=None) -> None:
    event_dt = _event_datetime(event_time)
    _resequence_station_queue(station_id)
    _refresh_station_runtime(station_id, event_dt)


def _complete_charging_request(station_id: int, event_dt: datetime) -> bool:
    station = query_db(
        """
        SELECT id, power_kw
        FROM charging_station
        WHERE id = ?
        """,
        [station_id],
        one=True,
    )
    if not station:
        return False

    current_req = query_db(
        """
        SELECT id, request_id, request_energy, charge_start_time, estimated_finish_time
        FROM charge_request
        WHERE station_id = ?
          AND request_status = ?
        ORDER BY station_queue_position
        LIMIT 1
        """,
        [station_id, RequestStatus.CHARGING.value],
        one=True,
    )
    if not current_req:
        return False

    start_time = parse_iso_datetime(current_req["charge_start_time"])
    finish_time = parse_iso_datetime(current_req["estimated_finish_time"])
    if not start_time or not finish_time or finish_time > event_dt:
        return False

    duration_seconds = max(0, int((finish_time - start_time).total_seconds()))
    actual_energy = float(current_req["request_energy"])
    execute_db(
        """
        UPDATE charge_request
        SET request_status = ?,
            actual_energy = ?,
            charge_stop_time = ?,
            charge_duration_seconds = ?,
            station_queue_position = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [
            RequestStatus.COMPLETED.value,
            actual_energy,
            _db_string(finish_time),
            duration_seconds,
            current_req["id"],
        ],
    )
    execute_db(
        """
        UPDATE charging_session
        SET end_time = ?,
            actual_energy = ?,
            status = ?
        WHERE request_id = ?
        """,
        [
            _db_string(finish_time),
            actual_energy,
            RequestStatus.COMPLETED.value,
            current_req["id"],
        ],
    )
    execute_db(
        """
        UPDATE charging_station
        SET total_charge_count = total_charge_count + 1,
            total_charge_seconds = total_charge_seconds + ?,
            total_charge_energy = total_charge_energy + ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [duration_seconds, actual_energy, station_id],
    )
    _resequence_station_queue(station_id)
    _refresh_station_runtime(station_id, finish_time)
    ensure_request_detail(str(current_req["request_id"]))
    station_row = query_db("SELECT station_code FROM charging_station WHERE id = ?", [station_id], one=True)
    log_request_lifecycle(
        str(current_req["request_id"]),
        "CHARGING_COMPLETED",
        event_time=finish_time,
        station_code=station_row["station_code"] if station_row else None,
        description="充电已正常完成",
    )
    return True


def _start_head_request_if_ready(station_id: int, event_dt: datetime) -> bool:
    head_req = query_db(
        """
        SELECT id, request_id, request_time, estimated_start_time
        FROM charge_request
        WHERE station_id = ?
          AND request_status = ?
        ORDER BY station_queue_position
        LIMIT 1
        """,
        [station_id, RequestStatus.QUEUED.value],
        one=True,
    )
    if not head_req:
        return False

    start_time = parse_iso_datetime(head_req["estimated_start_time"]) or parse_iso_datetime(head_req["request_time"])
    if not start_time or start_time > event_dt:
        return False

    execute_db(
        """
        UPDATE charge_request
        SET request_status = ?,
            charge_start_time = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [
            RequestStatus.CHARGING.value,
            _db_string(start_time),
            head_req["id"],
        ],
    )
    session_row = query_db(
        """
        SELECT id
        FROM charging_session
        WHERE request_id = ?
        LIMIT 1
        """,
        [head_req["id"]],
        one=True,
    )
    if session_row:
        execute_db(
            """
            UPDATE charging_session
            SET station_id = ?,
                start_time = ?,
                status = ?
            WHERE id = ?
            """,
            [
                station_id,
                _db_string(start_time),
                RequestStatus.CHARGING.value,
                session_row["id"],
            ],
        )
    else:
        execute_db(
            """
            INSERT INTO charging_session (request_id, station_id, start_time, status)
            VALUES (?, ?, ?, ?)
            """,
            [
                head_req["id"],
                station_id,
                _db_string(start_time),
                RequestStatus.CHARGING.value,
            ],
        )
    _refresh_station_runtime(station_id, start_time)
    station_row = query_db("SELECT station_code FROM charging_station WHERE id = ?", [station_id], one=True)
    log_request_lifecycle(
        str(head_req["request_id"]),
        "CHARGING_STARTED",
        event_time=start_time,
        station_code=station_row["station_code"] if station_row else None,
        description=f"{station_row['station_code']} 开始充电" if station_row else "开始充电",
    )
    return True


def _settle_station_until(station_id: int, event_dt: datetime) -> None:
    while True:
        if _complete_charging_request(station_id, event_dt):
            continue
        if _start_head_request_if_ready(station_id, event_dt):
            continue
        break
    _refresh_station_runtime(station_id, event_dt)


def enqueue_request(station_code: str, request_id: str, event_time=None, allow_cross_mode: bool = False) -> tuple[bool, str]:
    event_dt = _event_datetime(event_time)
    station = _load_station(station_code)
    if not station:
        return False, "station not found"
    if station["station_status"] != "RUNNING":
        return False, "station unavailable"

    _settle_station_until(int(station["id"]), event_dt)

    req_row = query_db(
        """
        SELECT id, charge_mode, request_status, waiting_area_order
        FROM charge_request
        WHERE request_id = ?
        """,
        [request_id],
        one=True,
    )
    if not req_row:
        return False, "request not found"
    if not allow_cross_mode and req_row["charge_mode"] != station["charge_mode"]:
        return False, "charge mode mismatch"
    if req_row["request_status"] != RequestStatus.WAITING_AREA.value:
        return False, "request is not in waiting area"

    active_count = _active_count(int(station["id"]))
    if active_count >= int(station["queue_capacity"]):
        return False, "station queue is full"

    execute_db(
        """
        UPDATE charge_request
        SET request_status = ?,
            waiting_area_order = NULL,
            station_id = ?,
            station_queue_position = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE request_id = ?
        """,
        [
            RequestStatus.QUEUED.value,
            station["id"],
            active_count + 1,
            request_id,
        ],
    )
    _refresh_station_runtime(int(station["id"]), event_dt)
    from_fault_queue = int(req_row["waiting_area_order"] or -1) == 0
    log_request_lifecycle(
        request_id,
        "ASSIGNED_TO_STATION",
        event_time=event_dt,
        station_code=str(station["station_code"]),
        queue_position=active_count + 1,
        label="分配到新的桩" if from_fault_queue else "分配到桩队列",
        description=f"{station['station_code']} · 队列第 {active_count + 1} 位",
    )
    return True, "success"


def _waiting_candidates(charge_mode: str | None = None):
    sql = """
        SELECT request_id, charge_mode, request_energy, queue_number, waiting_area_order
        FROM charge_request
        WHERE request_status = ?
          AND waiting_area_order > 0
    """
    args = [RequestStatus.WAITING_AREA.value]
    if charge_mode:
        sql += " AND charge_mode = ?"
        args.append(charge_mode)
    sql += " ORDER BY waiting_area_order, id"
    return query_db(sql, args)


def _extended_station_states(event_dt: datetime, charge_mode: str | None = None):
    states = []
    for station in _running_stations(charge_mode):
        active_count = _active_count(int(station["id"]))
        remaining_slots = int(station["queue_capacity"]) - active_count
        if remaining_slots <= 0:
            continue
        states.append(
            {
                "station": dict(station),
                "remaining_slots": remaining_slots,
                "workload_seconds": _station_workload_seconds(
                    int(station["id"]),
                    event_dt,
                    float(station["power_kw"]),
                ),
            }
        )
    return states


def _dispatch_extended_candidates(event_dt: datetime, charge_mode: str | None = None, allow_cross_mode: bool = False):
    states = _extended_station_states(event_dt, charge_mode)
    scheduled = []
    while states:
        candidates = _waiting_candidates(None if allow_cross_mode else charge_mode)
        if not candidates:
            break

        best = None
        for req in candidates:
            for state in states:
                if not allow_cross_mode and req["charge_mode"] != state["station"]["charge_mode"]:
                    continue
                service_seconds = service_seconds_for_request(
                    float(req["request_energy"]),
                    float(state["station"]["power_kw"]),
                )
                finish_cost = int(state["workload_seconds"]) + service_seconds
                candidate = (
                    finish_cost,
                    service_seconds,
                    _queue_number_index(str(req["queue_number"])),
                    str(state["station"]["station_code"]),
                    req,
                    state,
                )
                if best is None or candidate[:4] < best[:4]:
                    best = candidate
        if best is None:
            break

        _, service_seconds, _, _, req, state = best
        ok, _ = enqueue_request(
            str(state["station"]["station_code"]),
            str(req["request_id"]),
            event_dt,
            allow_cross_mode=allow_cross_mode,
        )
        if not ok:
            break

        scheduled.append(
            {
                "request_id": str(req["request_id"]),
                "target_station_code": str(state["station"]["station_code"]),
            }
        )
        state["remaining_slots"] -= 1
        state["workload_seconds"] += service_seconds
        states = [item for item in states if item["remaining_slots"] > 0]

    return scheduled


def run_extended_scheduler(event_time=None, dispatch_mode_value: str | None = None):
    event_dt = _event_datetime(event_time)
    mode = dispatch_mode_value or _dispatch_mode()
    for station in _running_stations():
        _settle_station_until(int(station["id"]), event_dt)

    if mode == "EXT_SINGLE_BATCH":
        scheduled = []
        for charge_mode in ("FAST", "SLOW"):
            scheduled.extend(_dispatch_extended_candidates(event_dt, charge_mode, allow_cross_mode=False))
    elif mode == "EXT_FULL_BATCH":
        scheduled = _dispatch_extended_candidates(event_dt, None, allow_cross_mode=True)
    else:
        return run_normal_scheduler(event_dt)

    for station in _running_stations():
        _settle_station_until(int(station["id"]), event_dt)
    return {
        "dispatch_mode": mode,
        "scheduled_count": len(scheduled),
        "scheduled": scheduled,
    }


def run_dispatch_scheduler(event_time=None, charge_mode: str | None = None):
    mode = _dispatch_mode()
    if mode == "NORMAL":
        return run_normal_scheduler(event_time, charge_mode)
    event_dt = _event_datetime(event_time)
    scheduled = []
    modes = [charge_mode] if charge_mode else ["FAST", "SLOW"]
    for item_mode in modes:
        scheduled.extend(run_fault_requeue_scheduler(item_mode, event_dt))
        if _fault_waiting_candidates(item_mode):
            return {"dispatch_mode": mode, "scheduled_count": len(scheduled), "scheduled": scheduled}
    if charge_mode and mode == "EXT_SINGLE_BATCH":
        scheduled.extend(_dispatch_extended_candidates(event_dt, charge_mode, allow_cross_mode=False))
        return {"dispatch_mode": mode, "scheduled_count": len(scheduled), "scheduled": scheduled}
    result = run_extended_scheduler(event_time, mode)
    result["scheduled"] = scheduled + result["scheduled"]
    result["scheduled_count"] = len(result["scheduled"])
    return result


def _best_station_for_waiting_request(req_row, event_dt: datetime):
    stations = _running_stations(req_row["charge_mode"])
    candidates = []
    for station in stations:
        active_count = _active_count(int(station["id"]))
        if active_count >= int(station["queue_capacity"]):
            continue
        own_service = service_seconds_for_request(float(req_row["request_energy"]), float(station["power_kw"]))
        workload = _station_workload_seconds(int(station["id"]), event_dt, float(station["power_kw"]))
        candidates.append((workload + own_service, station["station_code"], station))
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def run_normal_scheduler(event_time=None, charge_mode: str | None = None, ignore_fault_queue: bool = False):
    event_dt = _event_datetime(event_time)
    if _dispatch_mode() != "NORMAL":
        return {"dispatch_mode": _dispatch_mode(), "scheduled_count": 0, "scheduled": []}

    stations = _running_stations(charge_mode)
    for station in stations:
        _settle_station_until(int(station["id"]), event_dt)

    modes = [charge_mode] if charge_mode else ["FAST", "SLOW"]
    scheduled = []
    for mode in modes:
        scheduled.extend(run_fault_requeue_scheduler(mode, event_dt))
        if not ignore_fault_queue and _fault_waiting_candidates(mode):
            return {
                "dispatch_mode": "NORMAL",
                "scheduled_count": len(scheduled),
                "scheduled": scheduled,
            }

    for mode in modes:
        while True:
            waiting_head = query_db(
                """
                SELECT request_id, charge_mode, request_energy
                FROM charge_request
                WHERE charge_mode = ?
                  AND request_status = ?
                  AND waiting_area_order > 0
                ORDER BY waiting_area_order
                LIMIT 1
                """,
                [mode, RequestStatus.WAITING_AREA.value],
                one=True,
            )
            if not waiting_head:
                break

            target_station = _best_station_for_waiting_request(waiting_head, event_dt)
            if not target_station:
                break

            ok, _ = enqueue_request(
                str(target_station["station_code"]),
                str(waiting_head["request_id"]),
                event_dt,
            )
            if not ok:
                break

            scheduled.append(
                {
                    "request_id": str(waiting_head["request_id"]),
                    "target_station_code": str(target_station["station_code"]),
                    "dispatch_mode": "NORMAL",
                }
            )

    for station in _running_stations(charge_mode):
        _settle_station_until(int(station["id"]), event_dt)

    return {
        "dispatch_mode": "NORMAL",
        "scheduled_count": len(scheduled),
        "scheduled": scheduled,
    }


def _station_states(charge_mode: str, as_of: datetime) -> list[dict]:
    states = []
    for station in _running_stations(charge_mode):
        queue_rows = _active_station_rows(int(station["id"]))
        workload = 0
        items = []
        for row in queue_rows:
            if row["request_status"] == RequestStatus.CHARGING.value and row["estimated_finish_time"]:
                remaining = max(0, int((parse_iso_datetime(row["estimated_finish_time"]) - as_of).total_seconds()))
            else:
                remaining = service_seconds_for_request(float(row["request_energy"]), float(station["power_kw"]))
            workload += remaining
            items.append({**dict(row), "remaining_seconds": remaining})
        states.append({"station": dict(station), "items": items, "workload_seconds": workload})
    return states


def predict_waiting_area_request(request_id: str) -> dict | None:
    req_row = query_db(
        """
        SELECT request_id, charge_mode, request_energy, request_status, waiting_area_order, request_time
        FROM charge_request
        WHERE request_id = ?
        """,
        [request_id],
        one=True,
    )
    if not req_row or req_row["request_status"] != RequestStatus.WAITING_AREA.value:
        return None

    as_of = parse_iso_datetime(req_row["request_time"])
    station_states = _station_states(req_row["charge_mode"], as_of)
    if not station_states:
        return {
            "station_code": None,
            "station_queue_position": None,
            "estimated_wait_seconds": None,
            "estimated_start_time": None,
            "estimated_finish_time": None,
        }

    waiting_rows = query_db(
        """
        SELECT request_id, request_energy
        FROM charge_request
        WHERE charge_mode = ?
          AND request_status = ?
          AND waiting_area_order <= ?
        ORDER BY waiting_area_order
        """,
        [req_row["charge_mode"], RequestStatus.WAITING_AREA.value, req_row["waiting_area_order"]],
    )

    prediction = None
    for row in waiting_rows:
        best_state = min(
            station_states,
            key=lambda state: (
                state["workload_seconds"]
                + service_seconds_for_request(float(row["request_energy"]), float(state["station"]["power_kw"])),
                state["station"]["station_code"],
            ),
        )
        own_service = service_seconds_for_request(float(row["request_energy"]), float(best_state["station"]["power_kw"]))
        wait_seconds = int(best_state["workload_seconds"])
        start_time = as_of + timedelta(seconds=wait_seconds)
        finish_time = start_time + timedelta(seconds=own_service)
        if row["request_id"] == request_id:
            prediction = {
                "station_code": None,
                "station_queue_position": None,
                "estimated_wait_seconds": wait_seconds,
                "estimated_start_time": iso_string(start_time),
                "estimated_finish_time": iso_string(finish_time),
            }
            break
        best_state["workload_seconds"] += own_service

    return prediction


def predict_queued_request(request_id: str) -> dict | None:
    req_row = query_db(
        """
        SELECT
            cr.request_id,
            cr.request_energy,
            cr.request_status,
            cr.request_time,
            cr.station_queue_position,
            cr.charge_start_time,
            cr.estimated_start_time,
            cr.estimated_finish_time,
            cs.id AS station_id,
            cs.station_code,
            cs.power_kw
        FROM charge_request cr
        JOIN charging_station cs ON cs.id = cr.station_id
        WHERE cr.request_id = ?
        """,
        [request_id],
        one=True,
    )
    if not req_row or req_row["request_status"] not in QUEUE_ACTIVE_STATUSES:
        return None

    start_time = parse_iso_datetime(req_row["charge_start_time"] or req_row["estimated_start_time"])
    finish_time = parse_iso_datetime(req_row["estimated_finish_time"])
    request_time = parse_iso_datetime(req_row["request_time"])
    wait_seconds = max(0, int((start_time - request_time).total_seconds())) if start_time else None

    return {
        "station_code": req_row["station_code"],
        "station_queue_position": int(req_row["station_queue_position"]),
        "estimated_wait_seconds": wait_seconds,
        "estimated_start_time": iso_string(start_time),
        "estimated_finish_time": iso_string(finish_time),
    }
