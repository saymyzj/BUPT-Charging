"""V3 最小认证接口。"""

from flask import Blueprint, request

from app.utils.auth import (
    generate_token,
    get_current_user,
    hash_password,
    require_auth,
    validate_password,
    validate_username,
    verify_password,
)
from app.utils.db import execute_db, query_db
from app.utils.response import error_response, success_response

auth_bp = Blueprint("auth", __name__)


def _next_public_user_id() -> str:
    row = query_db(
        """
        SELECT user_id
        FROM user
        WHERE user_id LIKE 'U%'
        ORDER BY CAST(SUBSTR(user_id, 2) AS INTEGER) DESC
        LIMIT 1
        """,
        one=True,
    )
    next_number = 1 if not row else int(str(row["user_id"])[1:]) + 1
    return f"U{next_number:03d}"


def _iso_string(value):
    if value is None:
        return None
    return str(value).replace(" ", "T")


def _validate_positive_float(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


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


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = "USER"

    try:
        battery_capacity = float(data.get("battery_capacity"))
    except (TypeError, ValueError):
        return error_response(1001, "battery_capacity 必须是正数")

    if battery_capacity <= 0:
        return error_response(1001, "battery_capacity 必须是正数")

    is_valid, message = validate_username(username)
    if not is_valid:
        return error_response(1001, message)
    is_valid, message = validate_password(password)
    if not is_valid:
        return error_response(1001, message)

    existing = query_db("SELECT id FROM user WHERE username = ?", [username], one=True)
    if existing:
        return error_response(1001, "用户名已存在")

    public_user_id = _next_public_user_id()
    db_user_id = execute_db(
        """
        INSERT INTO user (user_id, username, password_hash, battery_capacity, role)
        VALUES (?, ?, ?, ?, ?)
        """,
        [public_user_id, username, hash_password(password), battery_capacity, role],
    )

    created = query_db(
        "SELECT user_id, username, role, created_at FROM user WHERE id = ?",
        [db_user_id],
        one=True,
    )
    return success_response(
        {
            "user_id": created["user_id"],
            "username": created["username"],
            "role": created["role"],
            "created_at": _iso_string(created["created_at"]),
        }
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return error_response(1001, "用户名和密码不能为空")

    user = query_db(
        "SELECT id, user_id, username, password_hash, role FROM user WHERE username = ?",
        [username],
        one=True,
    )
    if not user or not verify_password(password, user["password_hash"]):
        return error_response(1001, "用户名或密码错误")

    token = generate_token(user["id"], user["username"], user["role"])
    return success_response(
        {
            "token": token,
            "user_id": user["user_id"],
            "role": user["role"],
        }
    )


@auth_bp.route("/profile", methods=["GET"])
@require_auth
def profile():
    user = get_current_user()
    record = query_db(
        """
        SELECT user_id, username, role, battery_capacity, created_at
        FROM user
        WHERE id = ?
        """,
        [user["id"]],
        one=True,
    )
    if not record:
        return error_response(1002, "用户不存在")

    return success_response(
        {
            "user_id": record["user_id"],
            "username": record["username"],
            "role": record["role"],
            "battery_capacity": float(record["battery_capacity"]),
            "created_at": _iso_string(record["created_at"]),
        }
    )


@auth_bp.route("/profile/battery-capacity", methods=["PUT"])
@require_auth
def update_profile_battery_capacity():
    current_user = get_current_user()
    if current_user["role"] == "ADMIN":
        return error_response(1003, "管理员账号没有电池容量")

    data = request.get_json(silent=True) or {}
    battery_capacity = _validate_positive_float(data.get("battery_capacity"))
    if battery_capacity is None:
        return error_response(1001, "battery_capacity 必须是正数")

    if _has_active_request(int(current_user["id"])):
        return error_response(1010, "当前有进行中的充电请求，不能修改电池容量")

    execute_db(
        """
        UPDATE user
        SET battery_capacity = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        [battery_capacity, current_user["id"]],
    )
    return success_response({"battery_capacity": battery_capacity, "updated": True})
