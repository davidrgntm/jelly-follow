"""Events service — create, manage, participant handling. Now with reward pool."""
import logging
from typing import Optional
from app.integrations.google_sheets import (
    get_sheets, SHEET_EVENTS, SHEET_EVENT_COUNTRIES, SHEET_EVENT_REWARDS,
    SHEET_EVENT_PARTICIPANTS, SHEET_SYSTEM_LOGS, SHEET_SCANS_RAW, SHEET_POINT_TRANSACTIONS,
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

    # Return data directly — don't re-fetch (avoids NoneType if cache stale)
    result = {
        "event_id": event_id, "event_code": event_code,
        "event_name": event_name, "description": description,
        "status": "draft", "start_at": start_at, "end_at": end_at,
        "rules_text": rules_text, "created_by_admin_id": created_by_admin_id,
        "reward_pool_amount": str(reward_pool_amount) if reward_pool_amount else "",
        "reward_pool_currency": reward_pool_currency or "UZS",
        "countries": country_codes, "rewards": rewards,
    }
    return result


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
    cached = events_cache.get("active_events")
    if cached is not None:
        return cached
    sheets = get_sheets()
    events = [e for e in sheets.get_all_records(SHEET_EVENTS) if e.get("status") == "active"]
    result = [hydrate_event(e) for e in events]
    events_cache.set("active_events", result)
    return result


def get_all_events():
    cached = events_cache.get("all_events")
    if cached is not None:
        return cached
    sheets = get_sheets()
    events = sheets.get_all_records(SHEET_EVENTS)
    result = [hydrate_event(e) for e in events]
    events_cache.set("all_events", result)
    return result


def set_event_status(event_id, status):
    if status not in ALLOWED_EVENT_STATUSES:
        raise ValueError(f"Invalid event status: {status}")
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_EVENTS, "event_id", event_id)
    if not row_idx:
        raise ValueError(f"Event not found: {event_id}")
    current = get_event_by_id(event_id) or {}
    current_status = current.get("status", "draft")
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


def update_event(event_id, event_name=None, description=None, start_at=None, end_at=None,
                 rules_text=None, country_codes=None, rewards=None,
                 reward_pool_amount=None, reward_pool_currency=None):
    sheets = get_sheets()
    event = get_event_by_id(event_id)
    if not event:
        raise ValueError(f"Event not found: {event_id}")
    row_idx = sheets.find_row_index(SHEET_EVENTS, "event_id", event_id)
    if not row_idx:
        raise ValueError(f"Event not found: {event_id}")

    update = {}
    for key, value in {
        "event_name": event_name,
        "description": description,
        "start_at": start_at,
        "end_at": end_at,
        "rules_text": rules_text,
        "reward_pool_amount": reward_pool_amount,
        "reward_pool_currency": reward_pool_currency,
    }.items():
        if value is not None:
            update[key] = value
    if update:
        sheets.update_row(SHEET_EVENTS, row_idx, update)

    if country_codes is not None:
        current = sheets.get_all_records(SHEET_EVENT_COUNTRIES)
        kept = [r for r in current if r.get("event_id") != event_id]
        deduped = list(dict.fromkeys([str(c).upper() for c in country_codes if c]))
        seq = len(kept)
        for cc in deduped:
            seq += 1
            kept.append({
                "id": f"EVC-{seq:04d}",
                "event_id": event_id,
                "country_code": cc,
                "created_at": now_str(),
            })
        sheets.replace_records(SHEET_EVENT_COUNTRIES, kept)

    if rewards is not None:
        current = sheets.get_all_records(SHEET_EVENT_REWARDS)
        kept = [r for r in current if r.get("event_id") != event_id]
        seq = len(kept)
        for reward in rewards:
            seq += 1
            kept.append({
                "reward_id": generate_reward_id(seq),
                "event_id": event_id,
                "place_number": reward.get("place_number", 1),
                "reward_title": reward.get("reward_title", ""),
                "reward_amount": reward.get("reward_amount", ""),
                "currency_code": reward.get("currency_code", "UZS"),
                "created_at": now_str(),
            })
        sheets.replace_records(SHEET_EVENT_REWARDS, kept)

    invalidate_events()
    _log(sheets, "event_updated", "event", event_id, f"Event updated: {event_id}")
    return hydrate_event(get_event_by_id(event_id))



def delete_event(event_id):
    sheets = get_sheets()
    event = get_event_by_id(event_id)
    if not event:
        raise ValueError(f"Event not found: {event_id}")

    scans = sheets.find_records(SHEET_SCANS_RAW, "event_id", event_id)
    points = sheets.find_records(SHEET_POINT_TRANSACTIONS, "event_id", event_id)
    if scans or points:
        raise ValueError("Event has analytics history and cannot be deleted")

    events = [r for r in sheets.get_all_records(SHEET_EVENTS) if r.get("event_id") != event_id]
    countries = [r for r in sheets.get_all_records(SHEET_EVENT_COUNTRIES) if r.get("event_id") != event_id]
    rewards = [r for r in sheets.get_all_records(SHEET_EVENT_REWARDS) if r.get("event_id") != event_id]
    participants = [r for r in sheets.get_all_records(SHEET_EVENT_PARTICIPANTS) if r.get("event_id") != event_id]

    sheets.replace_records(SHEET_EVENTS, events)
    sheets.replace_records(SHEET_EVENT_COUNTRIES, countries)
    sheets.replace_records(SHEET_EVENT_REWARDS, rewards)
    sheets.replace_records(SHEET_EVENT_PARTICIPANTS, participants)

    invalidate_events()
    _log(sheets, "event_deleted", "event", event_id, f"Event deleted: {event.get('event_name') or event_id}")
    return True
