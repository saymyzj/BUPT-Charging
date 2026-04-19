"""V3 time-of-use billing and request-detail services."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from app.utils.db import execute_db, query_db

DETAIL_FINAL_STATUSES = {"COMPLETED", "COMPLETED_EARLY", "FAULT_INTERRUPTED"}


def _parse_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _db_string(value):
    if value is None:
        return None
    return _parse_datetime(value).strftime("%Y-%m-%dT%H:%M:%S")


def _iso_string(value):
    if value is None:
        return None
    return _parse_datetime(value).strftime("%Y-%m-%dT%H:%M:%S")


def _get_rate_config():
    rows = query_db(
        """
        SELECT config_key, config_value
        FROM scheduler_config
        WHERE config_key IN ('peak_price', 'flat_price', 'valley_price', 'service_fee_unit_price')
        """
    )
    config = {row["config_key"]: float(row["config_value"]) for row in rows}
    return {
        "peak_price": config.get("peak_price", 1.0),
        "flat_price": config.get("flat_price", 0.7),
        "valley_price": config.get("valley_price", 0.4),
        "service_fee_unit_price": config.get("service_fee_unit_price", 0.8),
    }


def _next_detail_id() -> str:
    row = query_db(
        """
        SELECT detail_id
        FROM request_detail
        WHERE detail_id LIKE 'DETAIL%'
        ORDER BY CAST(SUBSTR(detail_id, 7) AS INTEGER) DESC
        LIMIT 1
        """,
        one=True,
    )
    next_number = 1 if not row else int(str(row["detail_id"])[6:]) + 1
    return f"DETAIL{next_number:04d}"


def _segment_price(at_time: datetime, config: dict) -> float:
    current = at_time.time()
    if time(10, 0) <= current < time(15, 0) or time(18, 0) <= current < time(21, 0):
        return config["peak_price"]
    if time(7, 0) <= current < time(10, 0) or time(15, 0) <= current < time(18, 0) or time(21, 0) <= current < time(23, 0):
        return config["flat_price"]
    return config["valley_price"]


def _next_boundary(at_time: datetime) -> datetime:
    current = at_time.time()
    if time(7, 0) <= current < time(10, 0):
        return at_time.replace(hour=10, minute=0, second=0, microsecond=0)
    if time(10, 0) <= current < time(15, 0):
        return at_time.replace(hour=15, minute=0, second=0, microsecond=0)
    if time(15, 0) <= current < time(18, 0):
        return at_time.replace(hour=18, minute=0, second=0, microsecond=0)
    if time(18, 0) <= current < time(21, 0):
        return at_time.replace(hour=21, minute=0, second=0, microsecond=0)
    if time(21, 0) <= current < time(23, 0):
        return at_time.replace(hour=23, minute=0, second=0, microsecond=0)
    if current >= time(23, 0):
        next_day = at_time + timedelta(days=1)
        return next_day.replace(hour=7, minute=0, second=0, microsecond=0)
    return at_time.replace(hour=7, minute=0, second=0, microsecond=0)


def calculate_charge_fee(start_time, stop_time, power_kw: float) -> float:
    start_dt = _parse_datetime(start_time)
    stop_dt = _parse_datetime(stop_time)
    if not start_dt or not stop_dt or stop_dt <= start_dt or power_kw <= 0:
        return 0.0

    config = _get_rate_config()
    charge_fee = 0.0
    cursor = start_dt
    while cursor < stop_dt:
        segment_end = min(_next_boundary(cursor), stop_dt)
        segment_seconds = max(0, (segment_end - cursor).total_seconds())
        segment_energy = float(power_kw) * segment_seconds / 3600.0
        charge_fee += _segment_price(cursor, config) * segment_energy
        cursor = segment_end
    return round(charge_fee, 2)


def _serialize_detail_row(detail_row):
    return {
        "detail_id": detail_row["detail_id"],
        "detail_generated_at": _iso_string(detail_row["detail_generated_at"]),
        "station_code": detail_row["station_code"],
        "actual_energy": float(detail_row["actual_energy"]),
        "charge_duration_seconds": int(detail_row["charge_duration_seconds"]),
        "start_time": _iso_string(detail_row["start_time"]),
        "stop_time": _iso_string(detail_row["stop_time"]),
        "charge_fee": float(detail_row["charge_fee"]),
        "service_fee": float(detail_row["service_fee"]),
        "total_fee": float(detail_row["total_fee"]),
        "request_status": detail_row["request_status"],
    }


def get_request_detail(request_id: str):
    detail_row = query_db(
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
        JOIN charge_request cr ON cr.id = rd.request_id
        WHERE cr.request_id = ?
        ORDER BY rd.id DESC
        LIMIT 1
        """,
        [request_id],
        one=True,
    )
    return _serialize_detail_row(detail_row) if detail_row else None


def ensure_request_detail(request_id: str):
    existing = get_request_detail(request_id)
    if existing:
        return existing

    req_row = query_db(
        """
        SELECT
            cr.id,
            cr.request_id,
            cr.user_id,
            cr.actual_energy,
            cr.charge_duration_seconds,
            cr.charge_start_time,
            cr.charge_stop_time,
            cr.request_status,
            cs.station_code,
            cs.power_kw
        FROM charge_request cr
        LEFT JOIN charging_station cs ON cs.id = cr.station_id
        WHERE cr.request_id = ?
        """,
        [request_id],
        one=True,
    )
    if not req_row or req_row["request_status"] not in DETAIL_FINAL_STATUSES:
        return None
    if not req_row["station_code"] or not req_row["charge_start_time"] or not req_row["charge_stop_time"]:
        return None

    start_time = _parse_datetime(req_row["charge_start_time"])
    stop_time = _parse_datetime(req_row["charge_stop_time"])
    charge_duration_seconds = int(req_row["charge_duration_seconds"] or max(0, (stop_time - start_time).total_seconds()))
    actual_energy = float(req_row["actual_energy"])

    config = _get_rate_config()
    charge_fee = calculate_charge_fee(start_time, stop_time, float(req_row["power_kw"]))
    service_fee = round(config["service_fee_unit_price"] * actual_energy, 2)
    total_fee = round(charge_fee + service_fee, 2)
    detail_generated_at = stop_time

    execute_db(
        """
        INSERT INTO request_detail (
            detail_id,
            request_id,
            user_id,
            station_code,
            actual_energy,
            charge_duration_seconds,
            start_time,
            stop_time,
            detail_generated_at,
            charge_fee,
            service_fee,
            total_fee,
            request_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            _next_detail_id(),
            req_row["id"],
            req_row["user_id"],
            req_row["station_code"],
            actual_energy,
            charge_duration_seconds,
            _db_string(start_time),
            _db_string(stop_time),
            _db_string(detail_generated_at),
            charge_fee,
            service_fee,
            total_fee,
            req_row["request_status"],
        ],
    )
    return get_request_detail(request_id)
