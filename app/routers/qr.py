from fastapi import APIRouter, HTTPException, Header
from app.services.qr_service import generate_employee_qr, generate_event_qr
from app.services.employees_service import get_employee_by_id
from app.config import settings

router = APIRouter(prefix="/api/qr")


def _check_internal(secret: str):
    if secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/generate/employee/{employee_id}")
async def api_gen_employee_qr(employee_id: str, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    emp = get_employee_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return generate_employee_qr(
        employee_id=employee_id,
        employee_code=emp["employee_code"],
        country_code=emp["country_code"],
    )


@router.post("/generate/event/{employee_id}/{event_id}")
async def api_gen_event_qr(employee_id: str, event_id: str, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    emp = get_employee_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return generate_event_qr(
        employee_id=employee_id,
        employee_code=emp["employee_code"],
        event_id=event_id,
        country_code=emp["country_code"],
    )
