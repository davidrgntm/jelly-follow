"""Simple in-memory Telegram-based web login approval service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

_REQUESTS: dict[str, dict] = {}
TTL_MINUTES = 10


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cleanup() -> None:
    now = _now()
    expired = [rid for rid, item in _REQUESTS.items() if item.get("expires_at") <= now]
    for rid in expired:
        _REQUESTS.pop(rid, None)


def create_login_request(admin: dict, telegram_user_id: str, device_label: str = "") -> dict:
    _cleanup()
    request_id = token_urlsafe(18)
    code = token_urlsafe(4).upper()
    payload = {
        "request_id": request_id,
        "code": code,
        "telegram_user_id": str(telegram_user_id),
        "admin": {
            "admin_id": admin.get("admin_id", ""),
            "full_name": admin.get("full_name", ""),
            "role_code": admin.get("role_code", "ga"),
        },
        "device_label": device_label or "Browser",
        "created_at": _now(),
        "expires_at": _now() + timedelta(minutes=TTL_MINUTES),
        "approved": False,
        "approved_at": None,
    }
    _REQUESTS[request_id] = payload
    return serialize_request(payload)


def get_request(request_id: str) -> Optional[dict]:
    _cleanup()
    item = _REQUESTS.get(request_id)
    if not item:
        return None
    return serialize_request(item)


def approve_request(request_id: str, telegram_user_id: str) -> Optional[dict]:
    _cleanup()
    item = _REQUESTS.get(request_id)
    if not item:
        return None
    if str(item.get("telegram_user_id")) != str(telegram_user_id):
        return None
    item["approved"] = True
    item["approved_at"] = _now()
    return serialize_request(item)


def pop_approved_request(request_id: str) -> Optional[dict]:
    _cleanup()
    item = _REQUESTS.get(request_id)
    if not item or not item.get("approved"):
        return None
    _REQUESTS.pop(request_id, None)
    return serialize_request(item)


def serialize_request(item: dict) -> dict:
    return {
        "request_id": item.get("request_id"),
        "code": item.get("code"),
        "telegram_user_id": item.get("telegram_user_id"),
        "admin": dict(item.get("admin") or {}),
        "device_label": item.get("device_label", ""),
        "approved": bool(item.get("approved")),
        "created_at": item.get("created_at").isoformat() if item.get("created_at") else None,
        "expires_at": item.get("expires_at").isoformat() if item.get("expires_at") else None,
        "approved_at": item.get("approved_at").isoformat() if item.get("approved_at") else None,
    }
