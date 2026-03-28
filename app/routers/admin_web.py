"""Web admin panel API endpoints."""
import logging
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from app.config import settings
from app.services.admins_service import get_system_stats
from app.services.employees_service import get_all_employees
from app.services.events_service import get_all_events, get_active_events
from app.services.leaderboard_service import build_leaderboard
from app.integrations.google_sheets import get_sheets, SHEET_SCANS_RAW, SHEET_DEVICE_REGISTRY

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _check_web_auth(secret: str):
    if secret != settings.ADMIN_WEB_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, key: str = ""):
    if key != settings.ADMIN_WEB_SECRET:
        return HTMLResponse("<h2>403 — Kirish taqiqlangan</h2><p>URL ga ?key=... qo'shing</p>", status_code=403)
    return templates.TemplateResponse("admin_panel.html", {"request": request, "key": key})


@router.get("/api/web/stats")
async def web_stats(x_admin_key: str = Header("")):
    _check_web_auth(x_admin_key)
    return get_system_stats()


@router.get("/api/web/employees")
async def web_employees(x_admin_key: str = Header("")):
    _check_web_auth(x_admin_key)
    return {"employees": get_all_employees()}


@router.get("/api/web/events")
async def web_events(x_admin_key: str = Header("")):
    _check_web_auth(x_admin_key)
    return {"events": get_all_events()}


@router.get("/api/web/leaderboard")
async def web_leaderboard(country: str = "", event_id: str = "", period: str = "all",
                           x_admin_key: str = Header("")):
    _check_web_auth(x_admin_key)
    lb = build_leaderboard(country_code=country or None, event_id=event_id or None,
                           period=period, top_n=100)
    return {"leaderboard": lb}


@router.get("/api/web/scans")
async def web_scans(limit: int = 50, x_admin_key: str = Header("")):
    _check_web_auth(x_admin_key)
    sheets = get_sheets()
    scans = sheets.get_all_records(SHEET_SCANS_RAW)
    scans.sort(key=lambda s: s.get("scanned_at", ""), reverse=True)
    return {"scans": scans[:limit]}
