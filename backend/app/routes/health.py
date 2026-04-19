from datetime import datetime

from flask import Blueprint

from app.utils.response import success_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
@health_bp.route("/health", methods=["GET"])
def health_check():
    return success_response(
        {
            "status": "ok",
            "timestamp": datetime.now().replace(microsecond=0).isoformat(),
        }
    )
