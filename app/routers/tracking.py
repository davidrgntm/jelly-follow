"""Tracking redirect router with server-side pre-log."""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.services.employees_service import get_employee_by_code, get_employee_by_id
from app.services.events_service import resolve_event_identifier, get_event_by_id
from app.services.scans_service import create_server_pre_log, process_scan
from app.services.notifications_service import notify_scan_result
from app.services.qr_service import get_qr_by_id
from app.integrations.google_sheets import get_sheets, SHEET_COUNTRIES, SHEET_QR_CODES
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _get_ip(request):
    forwarded = request.headers.get("X-Forwarded-For", "")
    real_ip = request.headers.get("X-Real-IP", "")
    client_ip = request.client.host if request.client else ""
    return client_ip, forwarded or real_ip


@router.get("/r/{employee_code}", response_class=HTMLResponse)
async def tracking_redirect(employee_code: str, request: Request, event: Optional[str] = None, qr: Optional[str] = None):
    employee = get_employee_by_code(employee_code)
    if not employee or employee.get("status") != "active":
        return HTMLResponse("<h3>Link topilmadi.</h3>", status_code=404)

    country_code = employee.get("country_code", "UZ")
    sheets = get_sheets()
    country = sheets.find_record(SHEET_COUNTRIES, "country_code", country_code)
    if not country:
        return HTMLResponse("<h3>Mamlakat topilmadi.</h3>", status_code=404)

    instagram_app_link = country.get("instagram_app_link", "")
    instagram_web_link = country.get("instagram_web_link", "")
    client_ip, forwarded_ip = _get_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    referer = request.headers.get("Referer", "")
    accept_language = request.headers.get("Accept-Language", "")

    event_record = resolve_event_identifier(event or "") if event else None
    event_id = event_record.get("event_id", "") if event_record else ""

    qr_id = ""
    if qr:
        qr_record = get_qr_by_id(qr)
        if qr_record and qr_record.get("employee_id") == employee.get("employee_id"):
            qr_id = qr_record.get("qr_id", "")
            if qr_record.get("event_id"):
                event_id = qr_record.get("event_id", "")

    if not qr_id:
        qr_id = employee.get("qr_id", "")
        if event_id:
            event_qr = next(
                (r for r in sheets.find_records(SHEET_QR_CODES, "employee_id", employee["employee_id"])
                 if r.get("event_id") == event_id and r.get("is_active") == "yes"), None)
            if event_qr:
                qr_id = event_qr.get("qr_id", qr_id)

    pre_scan_id = create_server_pre_log(
        employee_id=employee["employee_id"], employee_code=employee_code,
        country_code=country_code, event_id=event_id, qr_id=qr_id,
        ip_address=client_ip, forwarded_ip=forwarded_ip,
        user_agent=user_agent, referer=referer,
        accept_language=accept_language, request_path=request.url.path,
        query_string=str(request.query_params), instagram_target=instagram_web_link,
    )

    context = {
        "request": request,
        "employee_id": employee["employee_id"],
        "employee_code": employee_code,
        "event_id": event_id,
        "qr_id": qr_id,
        "country_code": country_code,
        "instagram_app_link": instagram_app_link,
        "instagram_web_link": instagram_web_link,
        "ip_address": client_ip,
        "forwarded_ip": forwarded_ip,
        "user_agent": user_agent,
        "referer": referer,
        "accept_language": accept_language,
        "request_path": request.url.path,
        "query_string": str(request.query_params),
        "api_base": settings.BASE_URL,
        "pre_scan_id": pre_scan_id,
    }
    return templates.TemplateResponse("redirect.html", context)


class ClientLogPayload(BaseModel):
    employee_id: str
    employee_code: str
    event_id: str = ""
    qr_id: str = ""
    country_code: str = ""
    ip_address: str = ""
    forwarded_ip: str = ""
    user_agent: str = ""
    referer: str = ""
    accept_language: str = ""
    request_path: str = ""
    query_string: str = ""
    instagram_target: str = ""
    client_device_id: str = ""
    fingerprint_id: str = ""
    device_type: str = ""
    os_name: str = ""
    browser_name: str = ""
    platform: str = ""
    screen_width: int = 0
    screen_height: int = 0
    viewport_width: int = 0
    viewport_height: int = 0
    timezone: str = ""
    deep_link_attempted: bool = False
    fallback_used: bool = False
    pre_scan_id: str = ""


@router.post("/api/tracking/client-log")
async def client_log(payload: ClientLogPayload):
    try:
        result = process_scan(
            employee_id=payload.employee_id, employee_code=payload.employee_code,
            country_code=payload.country_code, event_id=payload.event_id,
            qr_id=payload.qr_id, ip_address=payload.ip_address,
            forwarded_ip=payload.forwarded_ip, user_agent=payload.user_agent,
            referer=payload.referer, accept_language=payload.accept_language,
            request_path=payload.request_path, query_string=payload.query_string,
            instagram_target=payload.instagram_target, client_device_id=payload.client_device_id,
            fingerprint_id=payload.fingerprint_id,
            device_type=payload.device_type, os_name=payload.os_name,
            browser_name=payload.browser_name, platform=payload.platform,
            screen_width=payload.screen_width, screen_height=payload.screen_height,
            viewport_width=payload.viewport_width, viewport_height=payload.viewport_height,
            timezone=payload.timezone, deep_link_attempted=payload.deep_link_attempted,
            fallback_used=payload.fallback_used, pre_scan_id=payload.pre_scan_id,
        )

        try:
            employee = get_employee_by_id(payload.employee_id)
            event = get_event_by_id(payload.event_id) if payload.event_id else None
            if employee:
                await notify_scan_result(employee, result, event)
        except Exception as notify_err:
            logger.warning("Scan notification error: %s", notify_err)

        return {"ok": True, **result}
    except Exception as e:
        logger.error("client-log error: %s", e)
        return {"ok": False, "error": str(e)}
