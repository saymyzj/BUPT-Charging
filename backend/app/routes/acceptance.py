"""Acceptance-console routes."""

from __future__ import annotations

from flask import Blueprint, request, send_file

from app.services.acceptance_service import (
    acceptance_state,
    add_manual_event,
    build_snapshot,
    disable_acceptance,
    enable_acceptance,
    execute_all,
    execute_current,
    execute_event,
    execute_until,
    export_table_xlsx,
    initialize_acceptance_database,
    list_events,
    parse_xlsx_file,
    replace_events,
    reset_acceptance,
    set_acceptance_time,
    set_status,
    snapshot_history,
)
from app.utils.response import error_response, success_response

acceptance_bp = Blueprint("acceptance", __name__)


@acceptance_bp.route("/state", methods=["GET"])
def get_state():
    return success_response(acceptance_state())


@acceptance_bp.route("/initialize", methods=["POST"])
def initialize():
    data = request.get_json(silent=True) or {}
    try:
        return success_response(initialize_acceptance_database(int(data.get("user_count") or 22)))
    except Exception as exc:
        return error_response(1003, str(exc))


@acceptance_bp.route("/reset", methods=["POST"])
def reset():
    data = request.get_json(silent=True) or {}
    return success_response(reset_acceptance(data.get("sample_name") or ""))


@acceptance_bp.route("/enable", methods=["POST"])
def enable():
    data = request.get_json(silent=True) or {}
    return success_response(enable_acceptance(data.get("sample_name") or ""))


@acceptance_bp.route("/disable", methods=["POST"])
def disable():
    return success_response(disable_acceptance())


@acceptance_bp.route("/time", methods=["PUT"])
def update_time():
    data = request.get_json(silent=True) or {}
    if not data.get("simulation_time"):
        return error_response(1001, "simulation_time is required")
    try:
        return success_response(
            {"simulation_time": set_acceptance_time(data["simulation_time"], advance_runtime=bool(data.get("advance_runtime")))}
        )
    except Exception as exc:
        return error_response(1001, str(exc))


@acceptance_bp.route("/status", methods=["PUT"])
def update_status():
    data = request.get_json(silent=True) or {}
    try:
        return success_response(set_status(data.get("status") or "PAUSED"))
    except Exception as exc:
        return error_response(1001, str(exc))


@acceptance_bp.route("/xlsx/parse", methods=["POST"])
def parse_xlsx():
    file = request.files.get("file")
    if not file:
        return error_response(1001, "file is required")
    try:
        return success_response(parse_xlsx_file(file))
    except Exception as exc:
        return error_response(1099, f"xlsx parse failed: {exc}")


@acceptance_bp.route("/events", methods=["GET"])
def events():
    return success_response({"events": list_events()})


@acceptance_bp.route("/events", methods=["PUT"])
def save_events():
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("events"), list):
        return error_response(1001, "events must be an array")
    return success_response(replace_events(data["events"], data.get("sample_name") or ""))


@acceptance_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True) or {}
    try:
        return success_response(add_manual_event(data))
    except Exception as exc:
        return error_response(1001, str(exc))


@acceptance_bp.route("/events/<event_id>/execute", methods=["POST"])
def execute_one(event_id):
    try:
        return success_response(execute_event(event_id))
    except Exception as exc:
        return error_response(1003, str(exc))


@acceptance_bp.route("/execute-current", methods=["POST"])
def execute_current_time():
    try:
        return success_response(execute_current())
    except Exception as exc:
        return error_response(1003, str(exc))


@acceptance_bp.route("/execute-until", methods=["POST"])
def execute_to_time():
    data = request.get_json(silent=True) or {}
    if not data.get("target_time"):
        return error_response(1001, "target_time is required")
    try:
        return success_response(execute_until(data["target_time"]))
    except Exception as exc:
        return error_response(1003, str(exc))


@acceptance_bp.route("/execute-all", methods=["POST"])
def execute_everything():
    try:
        return success_response(execute_all())
    except Exception as exc:
        return error_response(1003, str(exc))


@acceptance_bp.route("/snapshot", methods=["GET"])
def snapshot():
    at_time = request.args.get("time")
    try:
        return success_response(build_snapshot(at_time))
    except Exception as exc:
        return error_response(1003, str(exc))


@acceptance_bp.route("/snapshots", methods=["GET"])
def snapshots():
    return success_response({"snapshots": snapshot_history()})


@acceptance_bp.route("/export.xlsx", methods=["GET"])
def export_xlsx():
    try:
        return send_file(
            export_table_xlsx(),
            as_attachment=True,
            download_name="acceptance-events.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as exc:
        return error_response(1003, str(exc))
