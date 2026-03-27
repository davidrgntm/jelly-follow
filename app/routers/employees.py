from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.employees_service import (
    register_employee, get_employee_by_id, get_employee_stats,
)
from app.services.leaderboard_service import build_leaderboard, get_employee_rank

router = APIRouter(prefix="/api/employees")


class RegisterPayload(BaseModel):
    telegram_user_id: str
    telegram_username: str = ""
    full_name: str
    phone: str
    country_code: str
    language_code: str = "uz"


@router.post("/register")
async def api_register(payload: RegisterPayload):
    emp = register_employee(
        telegram_user_id=payload.telegram_user_id,
        telegram_username=payload.telegram_username,
        full_name=payload.full_name,
        phone=payload.phone,
        country_code=payload.country_code,
        language_code=payload.language_code,
    )
    return emp


@router.get("/{employee_id}")
async def api_get_employee(employee_id: str):
    emp = get_employee_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.get("/{employee_id}/stats")
async def api_get_stats(employee_id: str):
    emp = get_employee_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return get_employee_stats(employee_id)


@router.get("/{employee_id}/leaderboard")
async def api_get_leaderboard(employee_id: str):
    emp = get_employee_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    country = emp.get("country_code")
    lb = build_leaderboard(country_code=country, top_n=10)
    rank = get_employee_rank(employee_id, country_code=country)
    return {"leaderboard": lb, "my_rank": rank}
