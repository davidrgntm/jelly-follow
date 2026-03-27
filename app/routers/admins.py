from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from app.services.admins_service import create_admin
from app.services.employees_service import update_employee_status, get_employee_by_id
from app.services.points_service import manual_adjust
from app.config import settings

router = APIRouter(prefix="/api/admins")


def _check_internal(secret: str):
    if secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


class CreateAdminPayload(BaseModel):
    telegram_user_id: str
    full_name: str
    phone: str = ""
    role_code: str
    created_by: str


class EmployeeStatusPayload(BaseModel):
    employee_id: str
    status: str
    updated_by: str = "admin"


class ManualPointsPayload(BaseModel):
    employee_id: str
    points_delta: int
    reason_code: str
    admin_id: str
    event_id: str = ""
    country_code: str = ""


@router.post("/create")
async def api_create_admin(payload: CreateAdminPayload, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    return create_admin(
        telegram_user_id=payload.telegram_user_id,
        full_name=payload.full_name,
        phone=payload.phone,
        role_code=payload.role_code,
        created_by=payload.created_by,
    )


@router.post("/employee-status")
async def api_employee_status(payload: EmployeeStatusPayload, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    emp = get_employee_by_id(payload.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    update_employee_status(payload.employee_id, payload.status, payload.updated_by)
    return {"ok": True}


@router.post("/manual-points")
async def api_manual_points(payload: ManualPointsPayload, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    emp = get_employee_by_id(payload.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    tx_id = manual_adjust(
        employee_id=payload.employee_id,
        employee_code=emp.get("employee_code", ""),
        points_delta=payload.points_delta,
        reason_code=payload.reason_code,
        admin_id=payload.admin_id,
        event_id=payload.event_id,
        country_code=payload.country_code or emp.get("country_code", ""),
    )
    return {"ok": True, "point_tx_id": tx_id}
