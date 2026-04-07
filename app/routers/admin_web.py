"""Session-based full web admin panel with Telegram approval login."""
from __future__ import annotations

import logging
import os
import sqlite3
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from itsdangerous import URLSafeSerializer, BadSignature

from app.integrations.google_sheets import (
    get_sheets,
    SHEET_SCANS_RAW,
    SHEET_SYSTEM_LOGS,
    SHEET_COUNTRIES,
    SHEET_QR_CODES,
    SHEET_POINT_TRANSACTIONS,
)
from app.services.admins_service import (
    get_admin_by_telegram_id,
    get_all_admins,
    get_system_stats,
    create_admin,
)
from app.services.employees_service import get_all_employees, get_employee_by_id, update_employee_status, get_employee_by_telegram_id, get_employee_stats
from app.services.events_service import get_all_events, create_event, set_event_status, update_event, get_event_countries, get_event_rewards, get_event_by_id, get_event_participants, delete_event
from app.services.leaderboard_service import build_leaderboard
from app.services.points_service import manual_adjust
from app.services.web_auth_service import create_login_request, get_request, pop_approved_request
from app.services.web_session_service import register_session, touch_session, close_session, list_active_sessions
from app.services.notifications_service import notify_event_started
from app.services.scans_service import enrich_scans_with_reason, resolve_scan
from app.config import settings
from app.bot.texts.translations import t
from app.utils.datetime_utils import now_str

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    real_ip = request.headers.get("x-real-ip", "")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else ""



def _resolve_sqlite_path() -> str:
    raw = str(getattr(settings, "SQLITE_PATH", "data/jelly_follow.db") or "data/jelly_follow.db").strip()
    raw = raw.strip("\"").strip("'")
    if os.path.isabs(raw):
        return raw
    if os.path.isdir("/data"):
        return os.path.join("/data", os.path.basename(raw))
    return raw

def _fetch_recent_scans_sql(limit: int = 100) -> list[dict]:
    db_path = _resolve_sqlite_path()
    conn = sqlite3.connect(
        db_path,
        timeout=float(getattr(settings, "SQLITE_TIMEOUT", 30.0)),
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    try:
        safe_limit = max(1, min(int(limit or 100), 1000))
        rows = conn.execute(
            f'''
            SELECT *
            FROM "{SHEET_SCANS_RAW}"
            ORDER BY _rowid DESC
            LIMIT ?
            ''',
            (safe_limit,),
        ).fetchall()
        scans: list[dict] = []
        for row in rows:
            scans.append({k: ("" if row[k] is None else str(row[k])) for k in row.keys()})
        return scans
    finally:
        conn.close()


def _event_stats_payload(event: dict, employees: list[dict], scans: list[dict], points: list[dict], participants: list[dict]) -> dict:
    event_id = event.get("event_id", "")
    country_codes = [c.upper() for c in (event.get("countries") or event.get("country_codes") or get_event_countries(event_id))]
    eligible = [e for e in employees if (e.get("country_code", "").upper() in country_codes and e.get("status") == "active")]
    event_scans = [s for s in scans if s.get("event_id") == event_id]
    event_points = [p for p in points if p.get("event_id") == event_id]
    unique_devices = len({s.get("device_key") for s in event_scans if s.get("point_decision") == "first_unique_device" and s.get("device_key")})
    participant_by_emp = {p.get("employee_id"): p for p in participants}
    accepted_ids = {p.get("employee_id") for p in participants if p.get("participant_status") == "accepted"}
    declined_ids = {p.get("employee_id") for p in participants if p.get("participant_status") == "declined"}
    pending_ids = {p.get("employee_id") for p in participants if p.get("participant_status") == "pending"}
    eligible_ids = {e.get("employee_id") for e in eligible}
    not_responded_ids = eligible_ids - accepted_ids - declined_ids - pending_ids
    return {
        "eligible_employees": len(eligible),
        "accepted_count": len(accepted_ids),
        "declined_count": len(declined_ids),
        "pending_count": len(pending_ids),
        "not_responded_count": len(not_responded_ids),
        "total_scans": len(event_scans),
        "unique_devices": unique_devices,
        "total_points": sum(int(p.get("points_delta", 0) or 0) for p in event_points),
    }


def _employee_public_card(employee: dict) -> dict:
    return {
        "employee_id": employee.get("employee_id", ""),
        "employee_code": employee.get("employee_code", ""),
        "full_name": employee.get("full_name", ""),
        "country_code": employee.get("country_code", ""),
        "status": employee.get("status", ""),
        "last_active_at": employee.get("last_active_at", ""),
        "short_link": employee.get("short_link", ""),
    }


def _attach_participant_people(participants: list[dict], employee_map: dict[str, dict]) -> list[dict]:
    out = []
    for part in participants:
        emp = employee_map.get(part.get("employee_id"), {})
        item = dict(part)
        item["employee"] = _employee_public_card(emp) if emp else {
            "employee_id": part.get("employee_id", ""),
            "employee_code": part.get("employee_id", ""),
            "full_name": part.get("employee_id", ""),
            "country_code": part.get("country_code", ""),
            "status": "",
            "last_active_at": "",
            "short_link": "",
        }
        out.append(item)
    return out


def _admin_profile_payload(admin: dict, request: Request) -> dict:
    sessions = list_active_sessions(admin_id=admin.get("admin_id"))
    current_session_id = request.session.get("session_id") or request.headers.get("authorization", "").replace("Bearer ", "").strip()
    for item in sessions:
        item["is_current"] = item.get("session_id") == current_session_id
    return {
        "admin": admin,
        "active_sessions": sessions,
        "stats": get_system_stats(),
    }


def _web_token_serializer() -> URLSafeSerializer:
    secret = settings.WEB_SESSION_SECRET or settings.ADMIN_WEB_SECRET or "change_this_session"
    return URLSafeSerializer(secret_key=secret, salt="jelly-follow-web-admin")


def create_web_token(admin: dict) -> str:
    payload = {
        "admin_id": admin.get("admin_id", ""),
        "telegram_user_id": str(admin.get("telegram_user_id", "")),
        "full_name": admin.get("full_name", ""),
        "role_code": admin.get("role_code", "ga"),
    }
    return _web_token_serializer().dumps(payload)


def parse_web_token(token: str | None) -> Optional[dict]:
    if not token:
        return None
    try:
        payload = _web_token_serializer().loads(token)
    except BadSignature:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


class AuthRequestIn(BaseModel):
    telegram_user_id: str
    device_label: str = "Browser"


class RewardIn(BaseModel):
    place_number: int
    reward_title: str = ""
    reward_amount: str = ""
    currency_code: str = "UZS"


class WebEventPayload(BaseModel):
    event_name: str
    description: str = ""
    start_at: str
    end_at: str
    rules_text: str = ""
    country_codes: List[str] = Field(default_factory=list)
    rewards: List[RewardIn] = Field(default_factory=list)
    reward_pool_amount: str = ""
    reward_pool_currency: str = "UZS"


class EmployeeStatusIn(BaseModel):
    status: str


class LegacyEmployeeStatusIn(BaseModel):
    employee_id: str
    status: str


class ManualPointsIn(BaseModel):
    employee_id: str
    points_delta: int
    reason_code: str
    event_id: str = ""


class LegacyManualPointsIn(BaseModel):
    employee_id: str
    points: int
    reason_code: str
    event_id: str = ""


class AdminCreateIn(BaseModel):
    telegram_user_id: str
    full_name: str
    phone: str = ""
    role_code: str = "ga"


class CountryUpdateIn(BaseModel):
    instagram_username: Optional[str] = None
    country_name: Optional[str] = None
    is_active: Optional[str] = None


def _session_admin(request: Request) -> Optional[dict]:
    admin = request.session.get("admin")
    if not admin:
        return None
    db_admin = get_admin_by_telegram_id(admin.get("telegram_user_id"))
    if not db_admin or db_admin.get("status") != "active":
        request.session.pop("admin", None)
        return None
    admin["admin_id"] = db_admin.get("admin_id", admin.get("admin_id", ""))
    admin["full_name"] = db_admin.get("full_name", admin.get("full_name", ""))
    admin["role_code"] = db_admin.get("role_code", admin.get("role_code", "ga"))
    request.session["admin"] = admin
    touch_session(request.session.get("session_id"))
    return admin


def require_web_admin(request: Request) -> dict:
    admin = _session_admin(request)
    if admin:
        return admin

    auth_header = request.headers.get("authorization", "")
    bearer_token = ""
    if auth_header.lower().startswith("bearer "):
        bearer_token = auth_header.split(" ", 1)[1].strip()
    raw_token = bearer_token or request.headers.get("x-admin-token", "") or request.query_params.get("token", "")
    token_admin = parse_web_token(raw_token)
    if token_admin:
        db_admin = get_admin_by_telegram_id(token_admin.get("telegram_user_id"))
        if db_admin and db_admin.get("status") == "active":
            admin = {
                "admin_id": db_admin.get("admin_id", token_admin.get("admin_id", "")),
                "telegram_user_id": str(db_admin.get("telegram_user_id", token_admin.get("telegram_user_id", ""))),
                "full_name": db_admin.get("full_name", token_admin.get("full_name", "")),
                "role_code": db_admin.get("role_code", token_admin.get("role_code", "ga")),
            }
            request.session["admin"] = admin
            request.session["session_id"] = raw_token or request.session.get("session_id")
            touch_session(request.session.get("session_id"))
            return admin

    raise HTTPException(status_code=401, detail="Not authenticated")


def require_super_admin(admin: dict = Depends(require_web_admin)) -> dict:
    if admin.get("role_code") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    return admin


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    admin = _session_admin(request)
    return templates.TemplateResponse("admin_panel.html", {
        "request": request,
        "admin": admin,
        "app_env": settings.APP_ENV,
    })


@router.get("/api/web/me")
async def web_me(admin: dict = Depends(require_web_admin)):
    return {"admin": admin}


@router.get("/api/web/admin/profile")
async def web_admin_profile(request: Request, admin: dict = Depends(require_web_admin)):
    return _admin_profile_payload(admin, request)


@router.get("/api/web/session")
async def web_session(admin: dict = Depends(require_web_admin)):
    return {"session": admin}


@router.post("/api/web/auth/request")
async def web_auth_request(payload: AuthRequestIn, request: Request):
    admin = get_admin_by_telegram_id(payload.telegram_user_id)
    if not admin or admin.get("status") != "active":
        raise HTTPException(status_code=404, detail="Admin not found")

    login_request = create_login_request(admin=admin, telegram_user_id=payload.telegram_user_id, device_label=payload.device_label)
    bot = getattr(request.app.state, "bot", None)
    if not bot:
        raise HTTPException(status_code=500, detail="Bot is not available for Telegram approval")

    employee = get_employee_by_telegram_id(payload.telegram_user_id)
    lang = (employee or {}).get("language_code", "") or get_admin_language(payload.telegram_user_id, default="uz")
    code = login_request["code"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("admin.web.approve", lang), callback_data=f"web:approve:{login_request['request_id']}")]
    ])
    message_text = t("admin.web.login_request", lang).format(device=payload.device_label, code=code)
    await bot.send_message(chat_id=int(payload.telegram_user_id), text=message_text, parse_mode="HTML", reply_markup=keyboard)
    return {"ok": True, "request_id": login_request["request_id"], "expires_at": login_request["expires_at"]}


@router.post("/api/web/auth/start")
async def web_auth_start_legacy(payload: AuthRequestIn, request: Request):
    return await web_auth_request(payload, request)


@router.get("/api/web/auth/poll/{request_id}")
async def web_auth_poll(request_id: str, request: Request):
    approved = pop_approved_request(request_id)
    if approved:
        admin = {
            "admin_id": approved["admin"].get("admin_id", ""),
            "telegram_user_id": approved["telegram_user_id"],
            "full_name": approved["admin"].get("full_name", ""),
            "role_code": approved["admin"].get("role_code", "ga"),
        }
        token = create_web_token(admin)
        request.session["admin"] = admin
        request.session["session_id"] = token
        register_session(
            admin=admin,
            device_label=approved.get("device_label", "Browser"),
            session_id=token,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
        return {"ok": True, "approved": True, "admin": admin, "token": token}
    pending = get_request(request_id)
    if not pending:
        return {"ok": False, "approved": False, "expired": True}
    return {"ok": True, "approved": False, "expires_at": pending["expires_at"]}


@router.get("/api/web/auth/status/{request_id}")
async def web_auth_status_legacy(request_id: str, request: Request):
    result = await web_auth_poll(request_id, request)
    if result.get("approved"):
        return {"status": "approved", "authorized": True, "admin": result.get("admin")}
    if result.get("expired"):
        return {"status": "expired", "authorized": False}
    return {"status": "pending", "authorized": False, "expires_at": result.get("expires_at")}


@router.post("/api/web/auth/logout")
async def web_logout(request: Request):
    close_session(request.session.get("session_id"))
    request.session.pop("session_id", None)
    request.session.pop("admin", None)
    return {"ok": True}


@router.get("/api/web/stats")
async def web_stats(admin: dict = Depends(require_web_admin)):
    return get_system_stats()


@router.get("/api/web/employees")
async def web_employees(admin: dict = Depends(require_web_admin)):
    employees = get_all_employees()
    employees.sort(key=lambda e: ((e.get("country_code") or ""), (e.get("full_name") or "")))
    return {"employees": employees}


@router.get("/api/web/employees/{employee_id}/detail")
async def web_employee_detail(employee_id: str, admin: dict = Depends(require_web_admin)):
    employee = get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    sheets = get_sheets()
    stats = get_employee_stats(employee_id)
    scans = sheets.find_records(SHEET_SCANS_RAW, "employee_id", employee_id)
    scans.sort(key=lambda s: s.get("scanned_at", ""), reverse=True)
    qrs = sheets.find_records(SHEET_QR_CODES, "employee_id", employee_id)
    participations = []
    for event in get_all_events():
        part = next((p for p in get_event_participants(event.get("event_id", "")) if p.get("employee_id") == employee_id), None)
        if part:
            participations.append({
                "event_id": event.get("event_id", ""),
                "event_name": event.get("event_name", ""),
                "status": event.get("status", ""),
                "participant_status": part.get("participant_status", ""),
                "responded_at": part.get("responded_at", ""),
            })
    participations.sort(key=lambda x: x.get("responded_at", ""), reverse=True)
    return {
        "employee": employee,
        "stats": stats,
        "qrs": qrs,
        "recent_scans": enrich_scans_with_reason(scans[:100]),
        "participations": participations,
    }


@router.post("/api/web/employees/{employee_id}/status")
async def web_employee_status(employee_id: str, payload: EmployeeStatusIn, admin: dict = Depends(require_web_admin)):
    employee = get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    update_employee_status(employee_id, payload.status, updated_by=admin.get("admin_id", "web"))
    return {"ok": True}


@router.post("/api/web/employees/status")
async def web_employee_status_legacy(payload: LegacyEmployeeStatusIn, admin: dict = Depends(require_web_admin)):
    return await web_employee_status(payload.employee_id, EmployeeStatusIn(status=payload.status), admin)


@router.get("/api/web/events")
async def web_events(admin: dict = Depends(require_web_admin)):
    return {"events": get_all_events()}


@router.get("/api/web/events/{event_id}/detail")
async def web_event_detail(event_id: str, admin: dict = Depends(require_web_admin)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event = {**event, "countries": get_event_countries(event_id), "rewards": get_event_rewards(event_id)}
    sheets = get_sheets()
    employees = get_all_employees()
    employee_map = {e.get("employee_id"): e for e in employees}
    participants = get_event_participants(event_id)
    participant_cards = _attach_participant_people(participants, employee_map)
    scans = sheets.get_all_records(SHEET_SCANS_RAW)
    points = sheets.get_all_records(SHEET_POINT_TRANSACTIONS)
    stats = _event_stats_payload(event, employees, scans, points, participants)
    countries = [c.upper() for c in event.get("countries", [])]
    eligible = [e for e in employees if e.get("status") == "active" and e.get("country_code", "").upper() in countries]
    participant_ids = {p.get("employee_id") for p in participants}
    accepted = [p for p in participant_cards if p.get("participant_status") == "accepted"]
    pending = [p for p in participant_cards if p.get("participant_status") == "pending"]
    declined = [p for p in participant_cards if p.get("participant_status") == "declined"]
    not_responded = [_employee_public_card(e) for e in eligible if e.get("employee_id") not in participant_ids]
    event_scans = [s for s in scans if s.get("event_id") == event_id]
    event_scans.sort(key=lambda s: s.get("scanned_at", ""), reverse=True)
    leaderboard = build_leaderboard(event_id=event_id, top_n=50)

    # ── Per-country leaderboards ──
    leaderboard_by_country = {}
    for cc in countries:
        lb = build_leaderboard(event_id=event_id, country_code=cc, top_n=50)
        leaderboard_by_country[cc] = lb

    return {
        "event": event,
        "stats": stats,
        "participants": {
            "accepted": accepted,
            "pending": pending,
            "declined": declined,
            "not_responded": not_responded,
        },
        "leaderboard": leaderboard,
        "leaderboard_by_country": leaderboard_by_country,
        "recent_scans": enrich_scans_with_reason(event_scans[:100]),
    }


@router.delete("/api/web/events/{event_id}")
async def web_delete_event(event_id: str, admin: dict = Depends(require_web_admin)):
    try:
        delete_event(event_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/api/web/events")
async def web_create_event(payload: WebEventPayload, admin: dict = Depends(require_web_admin)):
    event = create_event(
        event_name=payload.event_name,
        description=payload.description,
        start_at=payload.start_at,
        end_at=payload.end_at,
        rules_text=payload.rules_text,
        country_codes=payload.country_codes,
        rewards=[r.model_dump() for r in payload.rewards],
        created_by_admin_id=admin.get("admin_id", ""),
        reward_pool_amount=payload.reward_pool_amount,
        reward_pool_currency=payload.reward_pool_currency,
    )

    # Save = publish immediately for simpler admin flow
    event_id = event.get("event_id", "")
    if event_id:
        set_event_status(event_id, "active")
        event = get_event_by_id(event_id) or event
        countries = get_event_countries(event_id)
        employees = get_all_employees()
        target_emps = [
            e for e in employees
            if e.get("status") == "active" and e.get("country_code", "").upper() in [c.upper() for c in countries]
        ]
        rewards = get_event_rewards(event_id)
        if target_emps:
            await notify_event_started(target_emps, event, rewards)
    return event


@router.put("/api/web/events/{event_id}")
async def web_update_event(event_id: str, payload: WebEventPayload, admin: dict = Depends(require_web_admin)):
    return update_event(
        event_id=event_id,
        event_name=payload.event_name,
        description=payload.description,
        start_at=payload.start_at,
        end_at=payload.end_at,
        rules_text=payload.rules_text,
        country_codes=payload.country_codes,
        rewards=[r.model_dump() for r in payload.rewards],
        reward_pool_amount=payload.reward_pool_amount,
        reward_pool_currency=payload.reward_pool_currency,
    )


@router.post("/api/web/events/{event_id}/{action}")
async def web_event_action(event_id: str, action: str, admin: dict = Depends(require_web_admin)):
    mapping = {"activate": "active", "pause": "paused", "finish": "finished"}
    status = mapping.get(action)
    if not status:
        raise HTTPException(status_code=400, detail="Unsupported action")
    set_event_status(event_id, status)
    if status == "active":
        event = get_event_by_id(event_id)
        if event:
            countries = get_event_countries(event_id)
            employees = get_all_employees()
            target_emps = [
                e for e in employees
                if e.get("status") == "active" and e.get("country_code", "").upper() in [c.upper() for c in countries]
            ]
            rewards = get_event_rewards(event_id)
            if target_emps:
                await notify_event_started(target_emps, event, rewards)
    return {"ok": True, "status": status}


@router.get("/api/web/leaderboard")
async def web_leaderboard(country: str = "", event_id: str = "", period: str = "all", admin: dict = Depends(require_web_admin)):
    lb = build_leaderboard(country_code=country or None, event_id=event_id or None, period=period, top_n=100)
    return {"leaderboard": lb}


@router.post("/api/web/points/manual")
async def web_manual_points(payload: ManualPointsIn, admin: dict = Depends(require_web_admin)):
    employee = get_employee_by_id(payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    point_tx_id = manual_adjust(
        employee_id=payload.employee_id,
        employee_code=employee.get("employee_code", ""),
        points_delta=payload.points_delta,
        reason_code=payload.reason_code,
        admin_id=admin.get("admin_id", ""),
        event_id=payload.event_id,
        country_code=employee.get("country_code", ""),
    )
    return {"ok": True, "point_tx_id": point_tx_id}


@router.post("/api/web/admins/manual-points")
async def web_manual_points_legacy(payload: LegacyManualPointsIn, admin: dict = Depends(require_web_admin)):
    return await web_manual_points(
        ManualPointsIn(
            employee_id=payload.employee_id,
            points_delta=payload.points,
            reason_code=payload.reason_code,
            event_id=payload.event_id,
        ),
        admin,
    )


@router.get("/api/web/scans")
async def web_scans(limit: int = 100, admin: dict = Depends(require_web_admin)):
    scans = _fetch_recent_scans_sql(limit=limit)
    enriched = enrich_scans_with_reason(scans)
    response = JSONResponse({"scans": enriched})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


class ScanResolveIn(BaseModel):
    action: str  # "approve" or "reject"


@router.post("/api/web/scans/{scan_id}/resolve")
async def web_resolve_scan(scan_id: str, payload: ScanResolveIn, admin: dict = Depends(require_web_admin)):
    try:
        result = resolve_scan(
            scan_id=scan_id,
            action=payload.action,
            admin_id=admin.get("admin_id", "web"),
        )
        return {"ok": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/web/logs")
async def web_logs(limit: int = 100, admin: dict = Depends(require_web_admin)):
    sheets = get_sheets()
    logs = sheets.get_all_records(SHEET_SYSTEM_LOGS)
    logs.sort(key=lambda s: s.get("logged_at", ""), reverse=True)
    return {"logs": logs[:limit]}


@router.get("/api/web/admins")
async def web_admins(admin: dict = Depends(require_web_admin)):
    return {"admins": get_all_admins()}


@router.post("/api/web/admins")
async def web_create_admin(payload: AdminCreateIn, admin: dict = Depends(require_super_admin)):
    created = create_admin(
        telegram_user_id=payload.telegram_user_id,
        full_name=payload.full_name,
        phone=payload.phone,
        role_code=payload.role_code,
        created_by=admin.get("admin_id", ""),
    )
    return created


@router.get("/api/web/settings")
async def web_settings(admin: dict = Depends(require_web_admin)):
    sheets = get_sheets()
    countries = sheets.get_all_records(SHEET_COUNTRIES)
    countries.sort(key=lambda c: c.get("country_code", ""))
    return {
        "settings": {
            "base_url": settings.BASE_URL,
            "tracking_domain": settings.TRACKING_DOMAIN,
            "app_env": settings.APP_ENV,
            "bot_mode": settings.BOT_MODE,
            "countries": countries,
        }
    }


@router.put("/api/web/settings/countries/{country_code}")
async def web_update_country(country_code: str, payload: CountryUpdateIn, admin: dict = Depends(require_web_admin)):
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_COUNTRIES, "country_code", country_code.upper())
    if not row_idx:
        raise HTTPException(status_code=404, detail="Country not found")
    current = sheets.find_record(SHEET_COUNTRIES, "country_code", country_code.upper()) or {}
    username = payload.instagram_username if payload.instagram_username is not None else current.get("instagram_username", "")
    update = {}
    if payload.country_name is not None:
        update["country_name"] = payload.country_name
    if payload.is_active is not None:
        update["is_active"] = payload.is_active
    if username is not None:
        update["instagram_username"] = username
        update["instagram_app_link"] = f"instagram://user?username={username}"
        update["instagram_web_link"] = f"https://www.instagram.com/{username}/"
    update["updated_at"] = now_str()
    sheets.update_row(SHEET_COUNTRIES, row_idx, update)
    return {"ok": True}

from fastapi import UploadFile, File
from fastapi.responses import FileResponse
import os
import shutil
import sqlite3

from app.integrations.google_sheets import SheetsClient

@router.post("/admin/upload-db")
async def upload_db(key: str, db_file: UploadFile = File(...)):
    if key != "mySecretKey123":
        return {"error": "unauthorized"}

    if not db_file.filename.endswith(".db"):
        return {"error": "only .db file allowed"}

    tmp_path = "/data/jelly_follow.upload.tmp.db"
    final_path = "/data/jelly_follow.db"
    backup_path = "/data/jelly_follow.backup.db"
    wal_path = final_path + "-wal"
    shm_path = final_path + "-shm"
    backup_wal_path = backup_path + "-wal"
    backup_shm_path = backup_path + "-shm"

    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(db_file.file, f)

    try:
        conn = sqlite3.connect(tmp_path)
        conn.execute("SELECT name FROM sqlite_master LIMIT 1")
        conn.close()
    except Exception as e:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return {"error": f"invalid sqlite file: {e}"}

    try:
        old_instance = SheetsClient._instance
        if old_instance is not None:
            old_conn = getattr(old_instance._local, "conn", None)
            if old_conn is not None:
                try:
                    old_conn.execute("PRAGMA wal_checkpoint(FULL)")
                    old_conn.close()
                except Exception:
                    pass
                try:
                    old_instance._local.conn = None
                except Exception:
                    pass
    except Exception:
        pass

    if os.path.exists(final_path):
        shutil.copy2(final_path, backup_path)

    if os.path.exists(wal_path):
        try:
            shutil.copy2(wal_path, backup_wal_path)
        except Exception:
            pass

    if os.path.exists(shm_path):
        try:
            shutil.copy2(shm_path, backup_shm_path)
        except Exception:
            pass

    os.replace(tmp_path, final_path)

    for sidecar in [wal_path, shm_path]:
        if os.path.exists(sidecar):
            try:
                os.remove(sidecar)
            except Exception:
                pass

    try:
        SheetsClient._instance = None
        fresh = SheetsClient.get_instance()
        conn = fresh._conn()
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA wal_checkpoint(FULL)")
    except Exception as e:
        return {
            "ok": False,
            "error": f"db uploaded but reopen failed: {e}",
            "path": final_path,
        }

    return {
        "ok": True,
        "message": "database uploaded successfully",
        "path": final_path,
        "backup": backup_path if os.path.exists(backup_path) else None,
        "removed_sidecars": {
            "wal_removed": not os.path.exists(wal_path),
            "shm_removed": not os.path.exists(shm_path),
        },
    }
    
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
import os
import shutil
import sqlite3

@router.post("/admin/upload-db")
async def upload_db(key: str, db_file: UploadFile = File(...)):
    if key != "mySecretKey123":
        return {"error": "unauthorized"}

    if not db_file.filename.endswith(".db"):
        return {"error": "only .db file allowed"}

    tmp_path = "/data/jelly_follow.upload.tmp.db"
    final_path = "/data/jelly_follow.db"
    backup_path = "/data/jelly_follow.backup.db"

    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(db_file.file, f)

    try:
        conn = sqlite3.connect(tmp_path)
        conn.execute("SELECT name FROM sqlite_master LIMIT 1")
        conn.close()
    except Exception as e:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return {"error": f"invalid sqlite file: {e}"}

    if os.path.exists(final_path):
        shutil.copy2(final_path, backup_path)

    os.replace(tmp_path, final_path)

    return {
        "ok": True,
        "message": "database uploaded successfully",
        "path": final_path,
        "backup": backup_path if os.path.exists(backup_path) else None,
    }

import os
from app.integrations.google_sheets import SheetsClient

@router.post("/admin/reset-sqlite-wal")
async def reset_sqlite_wal(key: str):
    if key != "mySecretKey123":
        return {"error": "unauthorized"}

    base = "/data/jelly_follow.db"
    wal = base + "-wal"
    shm = base + "-shm"

    try:
        old_instance = SheetsClient._instance
        if old_instance is not None:
            old_conn = getattr(old_instance._local, "conn", None)
            if old_conn is not None:
                try:
                    old_conn.close()
                except Exception:
                    pass
                try:
                    old_instance._local.conn = None
                except Exception:
                    pass
    except Exception:
        pass

    SheetsClient._instance = None

    removed = {}
    for p in [wal, shm]:
        if os.path.exists(p):
            try:
                os.remove(p)
                removed[p] = True
            except Exception as e:
                removed[p] = f"failed: {e}"
        else:
            removed[p] = False

    return {
        "ok": True,
        "removed": removed,
    }
import csv
import io
import sqlite3
from fastapi import UploadFile, File

@router.post("/admin/import-employees-csv")
async def import_employees_csv(
    key: str,
    csv_file: UploadFile = File(...),
    replace: bool = True
):
    if key != "mySecretKey123":
        return {"error": "unauthorized"}

    if not csv_file.filename.lower().endswith(".csv"):
        return {"error": "only .csv file allowed"}

    content = await csv_file.read()

    try:
        text = content.decode("utf-8-sig")
    except Exception:
        return {"error": "csv must be utf-8 encoded"}

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        return {"error": "csv is empty"}

    db_path = "/data/jelly_follow.db"

    required_columns = [
        "employee_id",
        "employee_code",
        "full_name",
        "phone",
        "telegram_user_id",
        "telegram_username",
        "country_code",
        "language_code",
        "status",
        "registered_at",
        "last_active_at",
        "qr_id",
        "short_link",
        "notes",
    ]

    missing = [c for c in required_columns if c not in rows[0].keys()]
    if missing:
        return {
            "error": "missing required columns",
            "missing": missing,
            "found": list(rows[0].keys()),
        }

    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA busy_timeout = 30000")

        if replace:
            conn.execute('DELETE FROM "employees"')

        inserted = 0

        for row in rows:
            conn.execute(
                '''
                INSERT INTO "employees" (
                    employee_id,
                    employee_code,
                    full_name,
                    phone,
                    telegram_user_id,
                    telegram_username,
                    country_code,
                    language_code,
                    status,
                    registered_at,
                    last_active_at,
                    qr_id,
                    short_link,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    (row.get("employee_id") or "").strip(),
                    (row.get("employee_code") or "").strip(),
                    (row.get("full_name") or "").strip(),
                    (row.get("phone") or "").strip(),
                    (row.get("telegram_user_id") or "").strip(),
                    (row.get("telegram_username") or "").strip(),
                    (row.get("country_code") or "").strip(),
                    (row.get("language_code") or "").strip(),
                    (row.get("status") or "").strip(),
                    (row.get("registered_at") or "").strip(),
                    (row.get("last_active_at") or "").strip(),
                    (row.get("qr_id") or "").strip(),
                    (row.get("short_link") or "").strip(),
                    (row.get("notes") or "").strip(),
                ),
            )
            inserted += 1

        conn.commit()

        count_now = conn.execute('SELECT COUNT(*) FROM "employees"').fetchone()[0]

        return {
            "ok": True,
            "message": "employees imported successfully",
            "inserted": inserted,
            "replace": replace,
            "count_now": count_now,
        }

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()
