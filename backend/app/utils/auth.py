"""
最小鉴权工具。

当前公共 develop 基线只提供：
1. 用户名唯一校验
2. 基础密码摘要
3. 简单 token 编解码

不引入复杂权限逻辑，避免把协作重点转移到鉴权实现上。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from functools import wraps

from flask import current_app, g, request

from app.utils.db import query_db
from app.utils.response import error_response


def validate_username(username: str) -> tuple[bool, str]:
    username = (username or "").strip()
    if len(username) < 3 or len(username) > 20:
        return False, "用户名长度需为 3-20 个字符"
    if not username.replace("_", "").isalnum():
        return False, "用户名仅支持字母、数字和下划线"
    return True, "ok"


def validate_password(password: str) -> tuple[bool, str]:
    if not password or len(password) < 6:
        return False, "密码长度至少为 6 位"
    return True, "ok"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash or "$" not in password_hash:
        return False
    salt, expected = password_hash.split("$", 1)
    actual = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(actual, expected)


def _b64encode(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode(token: str) -> dict | None:
    try:
        padding = "=" * ((4 - len(token) % 4) % 4)
        raw = base64.urlsafe_b64decode((token + padding).encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def generate_token(user_id: int, username: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": int(time.time()) + int(current_app.config.get("JWT_EXPIRATION_HOURS", 24)) * 3600,
    }
    encoded = _b64encode(payload)
    signature = hmac.new(
        current_app.config["SECRET_KEY"].encode("utf-8"),
        encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded}.{signature}"


def verify_token(token: str) -> dict | None:
    if not token or "." not in token:
        return None
    encoded, provided_signature = token.split(".", 1)
    expected_signature = hmac.new(
        current_app.config["SECRET_KEY"].encode("utf-8"),
        encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        return None

    payload = _b64decode(encoded)
    if not payload or payload.get("exp", 0) < int(time.time()):
        return None
    return payload


def get_current_user():
    return getattr(g, "current_user", None)


def require_auth(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response(1001, "缺少认证令牌")

        payload = verify_token(auth_header[7:])
        if not payload:
            return error_response(1001, "无效的认证令牌或已过期")

        user = query_db(
            "SELECT id, username, role FROM user WHERE id = ?",
            [payload["user_id"]],
            one=True,
        )
        if not user:
            return error_response(1001, "用户不存在")

        g.current_user = {
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
        return view_func(*args, **kwargs)

    return wrapper


def require_admin(view_func):
    @require_auth
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user["role"] != "ADMIN":
            return error_response(1003, "需要管理员权限")
        return view_func(*args, **kwargs)

    return wrapper
