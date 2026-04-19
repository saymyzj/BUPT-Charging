"""Legacy public station overview route backed by the V3 schema.

The formal V3 management interface is GET /api/admin/stations.  This route is
kept only so older demos or front-end probes do not crash on removed V2 fields.
"""

from flask import Blueprint, current_app

from app.enums import RequestStatus
from app.utils.db import query_db
from app.utils.response import success_response

stations_bp = Blueprint("stations", __name__)


def _serialize_station(row):
    return {
        "station_code": row["station_code"],
        "charge_mode": row["charge_mode"],
        "power_kw": float(row["power_kw"]),
        "station_status": row["station_status"],
        "current_request_id": row["current_request_id"],
        "queue_length": int(row["current_queue_length"]),
        "queue_capacity": int(row["queue_capacity"]),
        "available_time": str(row["available_time"]).replace(" ", "T") if row["available_time"] else None,
        "total_charge_count": int(row["total_charge_count"]),
        "total_charge_seconds": int(row["total_charge_seconds"]),
        "total_charge_energy": float(row["total_charge_energy"]),
    }


def _waiting_count(charge_mode=None):
    sql = """
        SELECT COUNT(*) AS cnt
        FROM charge_request
        WHERE request_status = ?
    """
    args = [RequestStatus.WAITING_AREA.value]
    if charge_mode:
        sql += " AND charge_mode = ?"
        args.append(charge_mode)
    row = query_db(sql, args, one=True)
    return int(row["cnt"]) if row else 0


def _waiting_area_capacity():
    row = query_db(
        """
        SELECT config_value
        FROM scheduler_config
        WHERE config_key = 'waiting_area_capacity'
        """,
        one=True,
    )
    if not row:
        return int(current_app.config.get("WAITING_AREA_SIZE", 6))
    try:
        return int(row["config_value"])
    except (TypeError, ValueError):
        return int(current_app.config.get("WAITING_AREA_SIZE", 6))


@stations_bp.route("/overview", methods=["GET"])
def get_stations_overview():
    rows = query_db(
        """
        SELECT
            cs.station_code,
            cs.charge_mode,
            cs.power_kw,
            cs.station_status,
            cs.queue_capacity,
            cs.current_queue_length,
            cs.available_time,
            cs.total_charge_count,
            cs.total_charge_seconds,
            cs.total_charge_energy,
            cr.request_id AS current_request_id
        FROM charging_station cs
        LEFT JOIN charge_request cr ON cr.id = cs.current_request_id
        ORDER BY cs.station_code
        """
    )

    fast_stations = []
    slow_stations = []
    for row in rows:
        station = _serialize_station(row)
        if row["charge_mode"] == "FAST":
            fast_stations.append(station)
        else:
            slow_stations.append(station)

    waiting_queue = {
        "fast_queue_count": _waiting_count("FAST"),
        "slow_queue_count": _waiting_count("SLOW"),
        "total_waiting": _waiting_count(),
        "capacity": _waiting_area_capacity(),
    }

    return success_response(
        {
            "deprecated": True,
            "replacement": "/api/admin/stations",
            "fast_stations": fast_stations,
            "slow_stations": slow_stations,
            "waiting_queue": waiting_queue,
        }
    )
