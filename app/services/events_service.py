"""Events service — create, manage, participant handling. Now with reward pool."""
import logging
from typing import Optional
from app.integrations.google_sheets import (
    get_sheets, SHEET_EVENTS, SHEET_EVENT_COUNTRIES, SHEET_EVENT_REWARDS,
    SHEET_EVENT_PARTICIPANTS, SHEET_SYSTEM_LOGS,
)
from app.utils.ids import (
    generate_event_id, generate_reward_id, generate_participant_id, generate_log_id,
)
from app.utils.datetime_utils import now_str
from app.utils.cache import events_cache, invalidate_events

logger = logging.getLogger(__name__)

ALLOWED_EVENT_STATUSES = {"draft", "active", "paused", "finished"}
ALLOWED_PARTICIPANT_STATUSES = {"pending", "accepted", "declined"}


def create_event(event_name, description, start_at, end_at, rules_text,
                 country_codes, rewards, created_by_admin_id,
                 reward_pool_amount="", reward_pool_currency="UZS"):
    sheets = get_sheets()
    seq = sheets.get_next_seq(SHEET_EVENTS)
    event_id = generate_event_id(seq)
    event_code = event_id

    row = [
        event_id, event_code, event_name, description,
        "draft", start_at, end_at, rules_text,
        created_by_admin_id, now_str(), "", "",
        str(reward_pool_amount) if reward_pool_amount else "",
        reward_pool_currency or "UZS",
    ]
    sheets.append_row(SHEET_EVENTS, row)

    country_codes = list(dict.fromkeys([cc.upper() for cc in country_codes if cc]))
    for cc in country_codes:
        country_seq = sheets.get_next_seq(SHEET_EVENT_COUNTRIES)
        sheets.append_row(SHEET_EVENT_COUNTRIES,
                          [f"EVC-{country_seq:04d}", event_id, cc, now_str()])

    for rw in rewards:
        rw_seq = sheets.get_next_seq(SHEET_EVENT_REWARDS)
        rw_id = generate_reward_id(rw_seq)
        sheets.append_row(SHEET_EVENT_REWARDS, [
            rw_id, event_id, rw.get("place_number", 1),
            rw.get("reward_title", ""), rw.get("reward_amount", ""),
            rw.get("currency_code", "UZS"), now_str(),
        ])

    invalidate_events()
    _log(sheets, "event_created", "event", event_id, f"Event created: {event_name}")
    logger.info("Event created: %s", event_id)
    return hydrate_event(get_event_by_id(event_id))


def get_event_by_id(event_id):
    sheets = get_sheets()
    return sheets.find_record(SHEET_EVENTS, "event_id", event_id)


def get_event_by_code(event_code):
    sheets = get_sheets()
    return sheets.find_record(SHEET_EVENTS, "event_code", event_code)


def resolve_event_identifier(event_identifier):
    if not event_identifier:
        return None
    event = get_event_by_id(event_identifier)
    if event:
        return event
    return get_event_by_code(event_identifier)


def hydrate_event(event, employee_id=""):
    if not event:
        return None
    result = dict(event)
    event_id = result.get("event_id", "")
    result["countries"] = get_event_countries(event_id)
    result["rewards"] = get_event_rewards(event_id)
    if employee_id:
        result["my_participation"] = get_participation_status(event_id, employee_id)
    return result


def get_active_events():
    sheets = get_sheets()
    events = [e for e in sheets.get_all_records(SHEET_EVENTS) if e.get("status") == "active"]
    return [hydrate_event(e) for e in events]


def get_all_events():
    sheets = get_sheets()
    events = sheets.get_all_records(SHEET_EVENTS)
    return [hydrate_event(e) for e in events]


def set_event_status(event_id, status):
    if status not in ALLOWED_EVENT_STATUSES:
        raise ValueError(f"Invalid event status: {status}")
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_EVENTS, "event_id", event_id)
    if not row_idx:
        raise ValueError(f"Event not found: {event_id}")
    current = get_event_by_id(event_id)
    current_status = current.get("status", "draft") if current else "draft"
    if current_status == "finished" and status != "finished":
        raise ValueError("Finished event cannot be re-opened")
    update = {"status": status}
    if status == "active" and not current.get("started_at"):
        update["started_at"] = now_str()
    elif status == "finished":
        update["finished_at"] = now_str()
    sheets.update_row(SHEET_EVENTS, row_idx, update)
    invalidate_events()
    _log(sheets, f"event_{status}", "event", event_id, f"Event status -> {status}")


def get_event_countries(event_id):
    sheets = get_sheets()
    rows = sheets.find_records(SHEET_EVENT_COUNTRIES, "event_id", event_id)
    return [r["country_code"] for r in rows if r.get("country_code")]


def get_event_rewards(event_id):
    sheets = get_sheets()
    rewards = sheets.find_records(SHEET_EVENT_REWARDS, "event_id", event_id)
    try:
        rewards.sort(key=lambda r: int(r.get("place_number", 999999)))
    except Exception:
        pass
    return rewards


def get_participation(event_id, employee_id):
    sheets = get_sheets()
    all_parts = sheets.get_all_records(SHEET_EVENT_PARTICIPANTS)
    return next((p for p in all_parts
                 if p.get("event_id") == event_id and p.get("employee_id") == employee_id), None)


def get_participation_status(event_id, employee_id):
    part = get_participation(event_id, employee_id)
    return part.get("participant_status", "") if part else ""


def respond_participation(event_id, employee_id, country_code, status):
    if status not in ALLOWED_PARTICIPANT_STATUSES:
        raise ValueError(f"Invalid participant status: {status}")
    sheets = get_sheets()
    existing = get_participation(event_id, employee_id)
    if existing:
        row_idx = sheets.find_row_index(SHEET_EVENT_PARTICIPANTS, "participant_id",
                                        existing["participant_id"])
        if row_idx:
            sheets.update_row(SHEET_EVENT_PARTICIPANTS, row_idx, {
                "participant_status": status, "responded_at": now_str(),
            })
        _log(sheets, "participant_updated", "event", event_id,
             f"Employee {employee_id} -> {status}")
        return get_participation(event_id, employee_id) or existing

    seq = sheets.get_next_seq(SHEET_EVENT_PARTICIPANTS)
    part_id = generate_participant_id(seq)
    row = [part_id, event_id, employee_id, country_code, status, now_str(), ""]
    sheets.append_row(SHEET_EVENT_PARTICIPANTS, row)
    _log(sheets, "participant_responded", "event", event_id,
         f"Employee {employee_id} -> {status}")
    return {"participant_id": part_id, "event_id": event_id,
            "employee_id": employee_id, "country_code": country_code,
            "participant_status": status, "responded_at": now_str(), "notes": ""}


def get_event_participants(event_id, participant_status=""):
    sheets = get_sheets()
    rows = sheets.find_records(SHEET_EVENT_PARTICIPANTS, "event_id", event_id)
    if participant_status:
        rows = [r for r in rows if r.get("participant_status") == participant_status]
    return rows


def get_events_for_employee(employee_id, country_code):
    all_events = get_active_events()
    result = []
    for ev in all_events:
        countries = ev.get("countries") or get_event_countries(ev["event_id"])
        if country_code.upper() in [c.upper() for c in countries]:
            result.append(hydrate_event(ev, employee_id=employee_id))
    return result


def get_active_events_for_country(country_code):
    all_events = get_active_events()
    result = []
    for ev in all_events:
        countries = ev.get("countries") or get_event_countries(ev["event_id"])
        if country_code.upper() in [c.upper() for c in countries]:
            result.append(ev)
    return result


def get_primary_active_event_for_country(country_code):
    events = get_active_events_for_country(country_code)
    if not events:
        return None
    events.sort(key=lambda e: e.get("started_at") or e.get("created_at") or "")
    return events[0]


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action, entity_type, entity_id, message
    ])
