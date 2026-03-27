"""
Tracking redirect router.
GET /r/{employee_code}         → redirect page + log
POST /api/tracking/client-log → receive JS-side device data
"""
import logging
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from app.services.employees_service import get_employee_by_code
from app.services.events_service import get_event_by_id
from app.integrations.google_sheets import get_sheets, SHEET_COUNTRIES
from app.utils.datetime_utils import now_str

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _get_ip(request: Request) -> tuple[str, str]:
    forwarded = request.headers.get("X-Forwarded-For", "")
    real_ip = request.headers.get("X-Real-IP", "")
    client_ip = request.client.host if request.client else ""
    return client_ip, forwarded or real_ip


@router.get("/r/{employee_code}", response_class=HTMLResponse)
async def tracking_redirect(
    employee_code: str,
    request: Request,
    event: Optional[str] = None,
):
    """
    Main tracking endpoint.
    Returns an HTML page that:
    1. Collects JS device info
    2. Posts to /api/tracking/client-log
    3. Attempts Instagram deep-link
    4. Falls back to web Instagram
    """
    employee = get_employee_by_code(employee_code)
    if not employee or employee.get("status") != "active":
        return HTMLResponse("<h3>Link topilmadi.</h3>", status_code=404)

    country_code = employee.get("country_code", "UZ")
    sheets = get_sheets()
    country = sheets.find_record(SHEET_COUNTRIES, "country_code", country_code)

    if not country:
        return HTMLResponse("<h3>Mamlakat ma'lumoti topilmadi.</h3>", status_code=404)

    instagram_app_link = country.get("instagram_app_link", "")
    instagram_web_link = country.get("instagram_web_link", "")

    client_ip, forwarded_ip = _get_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    referer = request.headers.get("Referer", "")
    accept_language = request.headers.get("Accept-Language", "")

    event_id = event or ""
    qr_id = employee.get("qr_id", "")

    from app.config import settings
    api_base = settings.BASE_URL

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
        "api_base": api_base,
    }
    return templates.TemplateResponse("redirect.html", context)


class ClientLogPayload(BaseModel):
    employee_id: str
    employee_code: str
    event_id: str = ""
    qr_id: str = ""
    country_code: str = ""
    # Server data echoed back
    ip_address: str = ""
    forwarded_ip: str = ""
    user_agent: str = ""
    referer: str = ""
    accept_language: str = ""
    request_path: str = ""
    query_string: str = ""
    instagram_target: str = ""
    # Client JS data
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


@router.post("/api/tracking/client-log")
async def client_log(payload: ClientLogPayload):
    """Receive client-side JS device data and process full scan."""
    try:
        from app.services.scans_service import process_scan
        result = process_scan(
            employee_id=payload.employee_id,
            employee_code=payload.employee_code,
            country_code=payload.country_code,
            event_id=payload.event_id,
            qr_id=payload.qr_id,
            ip_address=payload.ip_address,
            forwarded_ip=payload.forwarded_ip,
            user_agent=payload.user_agent,
            referer=payload.referer,
            accept_language=payload.accept_language,
            request_path=payload.request_path,
            query_string=payload.query_string,
            instagram_target=payload.instagram_target,
            fingerprint_id=payload.fingerprint_id,
            device_type=payload.device_type,
            os_name=payload.os_name,
            browser_name=payload.browser_name,
            platform=payload.platform,
            screen_width=payload.screen_width,
            screen_height=payload.screen_height,
            viewport_width=payload.viewport_width,
            viewport_height=payload.viewport_height,
            timezone=payload.timezone,
            deep_link_attempted=payload.deep_link_attempted,
            fallback_used=payload.fallback_used,
        )
        return {"ok": True, "scan_id": result["scan_id"]}
    except Exception as e:
        logger.error(f"client-log error: {e}")
        return {"ok": False, "error": str(e)}
