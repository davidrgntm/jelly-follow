import hashlib
import hmac
import json
import logging
from typing import Optional
from urllib.parse import parse_qsl

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import settings
from app.integrations.google_sheets import get_sheets, SHEET_SCANS_RAW
from app.services.employees_service import get_employee_by_telegram_id
from app.services.events_service import get_active_events_for_country, get_event_by_id, hydrate_event
from app.services.points_service import get_employee_total_points, get_employee_event_points
from app.services.qr_service import rotate_employee_qr, rotate_event_qr, get_qr_by_id

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


class MiniAppAuthPayload(BaseModel):
    init_data: str = ""
    telegram_user_id: str = ""


class QrSessionPayload(BaseModel):
    telegram_user_id: str
    event_id: str = ""


def _validate_telegram_init_data(init_data: str, bot_token: str) -> Optional[dict]:
    if not init_data:
        return None

    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items(), key=lambda x: x[0])
        )

        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        user_raw = parsed.get("user")
        if not user_raw:
            return None

        user = json.loads(user_raw)
        if not isinstance(user, dict):
            return None

        return user

    except Exception as e:
        logger.warning("Mini App initData validation failed: %s", e)
        return None


def _build_employee_payload(employee: dict) -> dict:
    return {
        "employee_id": employee.get("employee_id", ""),
        "employee_code": employee.get("employee_code", ""),
        "full_name": employee.get("full_name", ""),
        "country_code": employee.get("country_code", ""),
        "total_points": get_employee_total_points(employee.get("employee_id", "")),
    }


def _build_events_payload(employee: dict) -> list[dict]:
    events = get_active_events_for_country(employee.get("country_code", ""))
    return [
        {
            "event_id": ev.get("event_id", ""),
            "event_name": ev.get("event_name", ""),
            "description": ev.get("description", ""),
            "bonus_rules": ev.get("bonus_rules", []),
        }
        for ev in events
    ]


@router.get("/miniapp/qr", response_class=HTMLResponse)
async def qr_miniapp_page(request: Request):
    return templates.TemplateResponse(
        "miniapp_qr.html",
        {
            "request": request,
            "api_base": str(settings.BASE_URL).rstrip("/"),
        },
    )


@router.post("/api/miniapp/auth")
async def miniapp_auth(payload: MiniAppAuthPayload):
    telegram_user_id = ""

    # 1) Telegram signed initData
    if payload.init_data:
        user = _validate_telegram_init_data(payload.init_data, settings.BOT_TOKEN)
        if user:
            telegram_user_id = str(user.get("id", "")).strip()

    # 2) Fallback — agar initData bo'sh yoki validatsiya o'tmagan bo'lsa
    if not telegram_user_id and payload.telegram_user_id:
        telegram_user_id = str(payload.telegram_user_id).strip()

    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="Telegram user not found")

    employee = get_employee_by_telegram_id(telegram_user_id)
    if not employee or employee.get("status") != "active":
        raise HTTPException(status_code=404, detail="Employee not found")

    return {
        "ok": True,
        "telegram_user_id": telegram_user_id,
        "employee": _build_employee_payload(employee),
        "events": _build_events_payload(employee),
    }


@router.get("/api/miniapp/me")
async def miniapp_me(telegram_user_id: str):
    employee = get_employee_by_telegram_id(telegram_user_id)
    if not employee or employee.get("status") != "active":
        raise HTTPException(status_code=404, detail="Employee not found")

    return {
        "ok": True,
        "employee": _build_employee_payload(employee),
        "events": _build_events_payload(employee),
    }


@router.post("/api/miniapp/qr-session")
async def create_qr_session(payload: QrSessionPayload):
    employee = get_employee_by_telegram_id(payload.telegram_user_id)
    if not employee or employee.get("status") != "active":
        raise HTTPException(status_code=404, detail="Employee not found")

    event = None

    if payload.event_id:
        event = hydrate_event(get_event_by_id(payload.event_id))
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        qr = rotate_event_qr(
            employee_id=employee.get("employee_id", ""),
            employee_code=employee.get("employee_code", ""),
            event_id=payload.event_id,
            country_code=employee.get("country_code", ""),
        )
    else:
        qr = rotate_employee_qr(
            employee_id=employee.get("employee_id", ""),
            employee_code=employee.get("employee_code", ""),
            country_code=employee.get("country_code", ""),
        )

    image_url = qr.get("qr_image_path", "")
    if image_url.startswith("static/"):
        image_url = "/" + image_url

    return {
        "ok": True,
        "employee": {
            "employee_id": employee.get("employee_id", ""),
            "employee_code": employee.get("employee_code", ""),
            "full_name": employee.get("full_name", ""),
            "total_points": get_employee_total_points(employee.get("employee_id", "")),
        },
        "event": {
            "event_id": event.get("event_id", "") if event else "",
            "event_name": event.get("event_name", "") if event else "",
            "event_points": get_employee_event_points(
                employee.get("employee_id", ""),
                event.get("event_id", "")
            ) if event else 0,
            "bonus_rules": event.get("bonus_rules", []) if event else [],
        },
        "qr": {
            "qr_id": qr.get("qr_id", ""),
            "short_link": qr.get("short_link", ""),
            "image_url": image_url,
            "created_at": qr.get("created_at", ""),
        },
    }


@router.get("/api/miniapp/qr-session/{qr_id}/live")
async def qr_session_live(qr_id: str):
    qr = get_qr_by_id(qr_id)
    if not qr:
        raise HTTPException(status_code=404, detail="QR not found")

    sheets = get_sheets()
    rows = sheets.find_records(SHEET_SCANS_RAW, "qr_id", qr_id)
    rows.sort(key=lambda r: (r.get("created_at", ""), r.get("scan_id", "")))
    latest = rows[-1] if rows else None

    decision_counts = {
        "unique_count": len([r for r in rows if r.get("point_decision") == "first_unique_device"]),
        "duplicate_count": len([r for r in rows if r.get("point_decision") == "duplicate_device"]),
        "suspicious_count": len([r for r in rows if r.get("point_decision") == "suspicious"]),
        "pending_count": len([r for r in rows if r.get("point_decision") == "pending"]),
        "total_scans": len(rows),
    }

    employee_total_points = 0
    event_points = 0

    if qr.get("employee_id"):
        employee_total_points = get_employee_total_points(qr.get("employee_id", ""))
        if qr.get("event_id"):
            event_points = get_employee_event_points(
                qr.get("employee_id", ""),
                qr.get("event_id", ""),
            )

    return {
        "ok": True,
        "qr": {
            "qr_id": qr.get("qr_id", ""),
            "event_id": qr.get("event_id", ""),
            "employee_id": qr.get("employee_id", ""),
            "is_active": qr.get("is_active", ""),
            "created_at": qr.get("created_at", ""),
        },
        "stats": {
            **decision_counts,
            "employee_total_points": employee_total_points,
            "event_points": event_points,
        },
        "latest_scan": latest or {},
    }
