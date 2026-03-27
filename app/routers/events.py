from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List

from app.services.events_service import (
    create_event, set_event_status, get_event_by_id, respond_participation,
)
from app.services.leaderboard_service import build_leaderboard
from app.config import settings

router = APIRouter(prefix="/api/events")


def _check_internal(secret: str):
    if secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


class RewardIn(BaseModel):
    place_number: int
    reward_title: str
    reward_amount: str
    currency_code: str = "UZS"


class CreateEventPayload(BaseModel):
    event_name: str
    description: str = ""
    start_at: str
    end_at: str
    rules_text: str = ""
    country_codes: List[str]
    rewards: List[RewardIn] = []
    created_by_admin_id: str


class ParticipationPayload(BaseModel):
    employee_id: str
    country_code: str
    status: str  # accepted | declined


@router.post("/create")
async def api_create_event(payload: CreateEventPayload, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    event = create_event(
        event_name=payload.event_name,
        description=payload.description,
        start_at=payload.start_at,
        end_at=payload.end_at,
        rules_text=payload.rules_text,
        country_codes=payload.country_codes,
        rewards=[r.dict() for r in payload.rewards],
        created_by_admin_id=payload.created_by_admin_id,
    )
    return event


@router.post("/{event_id}/activate")
async def api_activate(event_id: str, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    set_event_status(event_id, "active")
    return {"ok": True}


@router.post("/{event_id}/pause")
async def api_pause(event_id: str, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    set_event_status(event_id, "paused")
    return {"ok": True}


@router.post("/{event_id}/finish")
async def api_finish(event_id: str, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    set_event_status(event_id, "finished")
    return {"ok": True}


@router.post("/{event_id}/participation")
async def api_participation(event_id: str, payload: ParticipationPayload):
    result = respond_participation(
        event_id=event_id,
        employee_id=payload.employee_id,
        country_code=payload.country_code,
        status=payload.status,
    )
    return result


@router.get("/{event_id}/leaderboard")
async def api_event_leaderboard(event_id: str):
    lb = build_leaderboard(event_id=event_id, top_n=50)
    return {"leaderboard": lb}
