from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List
from app.services.events_service import (
    create_event, set_event_status, get_event_by_id, get_all_events,
    get_active_events, hydrate_event, respond_participation,
)
from app.services.event_bonus_service import (
    create_bonus_rule, list_bonus_rules, submit_bonus, list_submissions, review_submission,
)
from app.services.leaderboard_service import build_leaderboard
from app.config import settings

router = APIRouter(prefix="/api/events")

def _check_internal(secret):
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
    reward_pool_amount: str = ""
    reward_pool_currency: str = "UZS"

class ParticipationPayload(BaseModel):
    employee_id: str
    country_code: str
    status: str

class BonusRulePayload(BaseModel):
    title: str
    description: str = ""
    task_type: str = "other"
    points: int
    max_per_employee: int = 1
    requires_moderation: bool = True
    min_followers: int = 0
    is_active: bool = True
    sort_order: int = 100
    created_by: str


class BonusSubmissionPayload(BaseModel):
    employee_id: str
    evidence_url: str = ""
    notes: str = ""


class BonusReviewPayload(BaseModel):
    admin_id: str
    notes: str = ""


@router.get("")
async def api_list_events(status: str = ""):
    events = get_active_events() if status == "active" else get_all_events()
    return {"events": events}

@router.get("/{event_id}")
async def api_get_event(event_id: str):
    event = hydrate_event(get_event_by_id(event_id))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/create")
async def api_create_event(payload: CreateEventPayload, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    return create_event(
        event_name=payload.event_name, description=payload.description,
        start_at=payload.start_at, end_at=payload.end_at,
        rules_text=payload.rules_text, country_codes=payload.country_codes,
        rewards=[r.model_dump() for r in payload.rewards],
        created_by_admin_id=payload.created_by_admin_id,
        reward_pool_amount=payload.reward_pool_amount,
        reward_pool_currency=payload.reward_pool_currency)

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
    return respond_participation(
        event_id=event_id, employee_id=payload.employee_id,
        country_code=payload.country_code, status=payload.status)

@router.get("/{event_id}/leaderboard")
async def api_event_leaderboard(event_id: str, period: str = "all"):
    lb = build_leaderboard(event_id=event_id, period=period, top_n=50)
    return {"leaderboard": lb}


@router.get("/{event_id}/bonus-rules")
async def api_event_bonus_rules(event_id: str, active_only: bool = True):
    return {"bonus_rules": list_bonus_rules(event_id, only_active=active_only)}


@router.post("/{event_id}/bonus-rules")
async def api_create_bonus_rule(event_id: str, payload: BonusRulePayload, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    return create_bonus_rule(
        event_id=event_id, title=payload.title, description=payload.description,
        task_type=payload.task_type, points=payload.points,
        max_per_employee=payload.max_per_employee, requires_moderation=payload.requires_moderation,
        min_followers=payload.min_followers, is_active=payload.is_active,
        sort_order=payload.sort_order, created_by=payload.created_by,
    )


@router.get("/{event_id}/bonus-submissions")
async def api_list_bonus_submissions(event_id: str, status: str = "", x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    return {"submissions": list_submissions(event_id, status=status)}


@router.post("/{event_id}/bonus-rules/{bonus_rule_id}/submit")
async def api_submit_bonus(event_id: str, bonus_rule_id: str, payload: BonusSubmissionPayload):
    return submit_bonus(
        event_id=event_id, bonus_rule_id=bonus_rule_id, employee_id=payload.employee_id,
        evidence_url=payload.evidence_url, notes=payload.notes,
    )


@router.post("/{event_id}/bonus-submissions/{submission_id}/approve")
async def api_approve_bonus_submission(event_id: str, submission_id: str, payload: BonusReviewPayload, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    return review_submission(submission_id, status="approved", admin_id=payload.admin_id, notes=payload.notes)


@router.post("/{event_id}/bonus-submissions/{submission_id}/reject")
async def api_reject_bonus_submission(event_id: str, submission_id: str, payload: BonusReviewPayload, x_internal_secret: str = Header("")):
    _check_internal(x_internal_secret)
    return review_submission(submission_id, status="rejected", admin_id=payload.admin_id, notes=payload.notes)
