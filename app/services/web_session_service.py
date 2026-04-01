"""In-memory web admin session registry for dashboard visibility."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

_SESSIONS: dict[str, dict] = {}
IDLE_TTL_HOURS = 24


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cleanup() -> None:
    cutoff = _now() - timedelta(hours=IDLE_TTL_HOURS)
    expired = [sid for sid, item in _SESSIONS.items() if (item.get("last_seen_at") or item.get("created_at") or _now()) < cutoff]
    for sid in expired:
        _SESSIONS.pop(sid, None)


def register_session(*, admin: dict, device_label: str = "Browser", session_id: Optional[str] = None, ip_address: str = "", user_agent: str = "") -> dict:
    _cleanup()
    sid = session_id or token_urlsafe(24)
    payload = {
        "session_id": sid,
        "admin_id": admin.get("admin_id", ""),
        "telegram_user_id": str(admin.get("telegram_user_id", "")),
        "full_name": admin.get("full_name", ""),
        "role_code": admin.get("role_code", "ga"),
        "device_label": device_label or "Browser",
        "ip_address": ip_address or "",
        "user_agent": user_agent or "",
        "created_at": _now(),
        "last_seen_at": _now(),
        "is_current": False,
    }
    _SESSIONS[sid] = payload
    return serialize_session(payload)


def touch_session(session_id: Optional[str]) -> Optional[dict]:
    _cleanup()
    if not session_id:
        return None
    item = _SESSIONS.get(session_id)
    if not item:
        return None
    item["last_seen_at"] = _now()
    return serialize_session(item)


def close_session(session_id: Optional[str]) -> bool:
    _cleanup()
    if not session_id:
        return False
    return _SESSIONS.pop(session_id, None) is not None


def list_active_sessions(admin_id: Optional[str] = None) -> list[dict]:
    _cleanup()
    items = list(_SESSIONS.values())
    if admin_id:
        items = [item for item in items if item.get("admin_id") == admin_id]
    items.sort(key=lambda item: item.get("last_seen_at") or item.get("created_at") or _now(), reverse=True)
    return [serialize_session(item) for item in items]


def serialize_session(item: dict) -> dict:
    return {
        "session_id": item.get("session_id", ""),
        "admin_id": item.get("admin_id", ""),
        "telegram_user_id": item.get("telegram_user_id", ""),
        "full_name": item.get("full_name", ""),
        "role_code": item.get("role_code", "ga"),
        "device_label": item.get("device_label", "Browser"),
        "ip_address": item.get("ip_address", ""),
        "user_agent": item.get("user_agent", ""),
        "created_at": item.get("created_at").isoformat() if item.get("created_at") else None,
        "last_seen_at": item.get("last_seen_at").isoformat() if item.get("last_seen_at") else None,
        "is_current": bool(item.get("is_current")),
    }
