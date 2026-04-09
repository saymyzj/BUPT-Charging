"""
最小登录注册接口。

当前仅提供：
1. 注册
2. 登录
3. 当前用户信息

保持实现简单，满足公共 develop 分支联调需要。
"""

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


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "USER").upper()
    if role not in {"USER", "ADMIN"}:
        role = "USER"

    is_valid, message = validate_username(username)
    if not is_valid:
        return error_response(1001, message)
    is_valid, message = validate_password(password)
    if not is_valid:
        return error_response(1001, message)

    existing = query_db("SELECT id FROM user WHERE username = ?", [username], one=True)
    if existing:
        return error_response(1001, "用户名已存在")

    user_id = execute_db(
        """
        INSERT INTO user (username, password_hash, role, balance)
        VALUES (?, ?, ?, 0.0)
        """,
        [username, hash_password(password), role],
    )
    return success_response(
        {
            "user_id": user_id,
            "username": username,
            "role": role,
        }
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return error_response(1001, "用户名和密码不能为空")

    user = query_db(
        "SELECT id, username, password_hash, role FROM user WHERE username = ?",
        [username],
        one=True,
    )
    if not user or not verify_password(password, user["password_hash"]):
        return error_response(1001, "用户名或密码错误")

    token = generate_token(user["id"], user["username"], user["role"])
    return success_response(
        {
            "token": token,
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
    )


@auth_bp.route("/profile", methods=["GET"])
@require_auth
def profile():
    user = get_current_user()
    record = query_db(
        "SELECT id, username, role, balance FROM user WHERE id = ?",
        [user["user_id"]],
        one=True,
    )
    if not record:
        return error_response(1002, "用户不存在")

    return success_response(
        {
            "user_id": record["id"],
            "username": record["username"],
            "role": record["role"],
            "balance": float(record["balance"]),
        }
    )
