"""
Events service — create, manage, participant handling.
"""
import logging
from typing import Optional

from app.integrations.google_sheets import (
    get_sheets,
    SHEET_EVENTS, SHEET_EVENT_COUNTRIES, SHEET_EVENT_REWARDS,
    SHEET_EVENT_PARTICIPANTS, SHEET_EMPLOYEES, SHEET_SYSTEM_LOGS,
)
from app.utils.ids import (
    generate_event_id, generate_reward_id,
    generate_participant_id, generate_log_id,
)
from app.utils.datetime_utils import now_str

logger = logging.getLogger(__name__)


def create_event(
    event_name: str,
    description: str,
    start_at: str,
    end_at: str,
    rules_text: str,
    country_codes: list[str],
    rewards: list[dict],
    created_by_admin_id: str,
) -> dict:
    sheets = get_sheets()
    seq = sheets.get_next_seq(SHEET_EVENTS)
    event_id = generate_event_id(seq)
    event_code = event_id

    row = [
        event_id, event_code, event_name, description,
        "draft", start_at, end_at, rules_text,
        created_by_admin_id, now_str(), "", ""
    ]
    sheets.append_row(SHEET_EVENTS, row)

    # Assign countries
    for cc in country_codes:
        country_seq = sheets.get_next_seq(SHEET_EVENT_COUNTRIES)
        sheets.append_row(SHEET_EVENT_COUNTRIES, [
            f"EVC-{country_seq:04d}", event_id, cc.upper(), now_str()
        ])

    # Add rewards
    for rw in rewards:
        rw_seq = sheets.get_next_seq(SHEET_EVENT_REWARDS)
        rw_id = generate_reward_id(rw_seq)
        sheets.append_row(SHEET_EVENT_REWARDS, [
            rw_id, event_id,
            rw.get("place_number", 1),
            rw.get("reward_title", ""),
            rw.get("reward_amount", ""),
            rw.get("currency_code", "UZS"),
            now_str()
        ])

    _log(sheets, "event_created", "event", event_id, f"Event created: {event_name}")
    logger.info(f"Event created: {event_id}")
    return get_event_by_id(event_id)


def get_event_by_id(event_id: str) -> Optional[dict]:
    sheets = get_sheets()
    return sheets.find_record(SHEET_EVENTS, "event_id", event_id)


def get_active_events() -> list[dict]:
    sheets = get_sheets()
    return [e for e in sheets.get_all_records(SHEET_EVENTS) if e.get("status") == "active"]


def get_all_events() -> list[dict]:
    sheets = get_sheets()
    return sheets.get_all_records(SHEET_EVENTS)


def set_event_status(event_id: str, status: str):
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_EVENTS, "event_id", event_id)
    if not row_idx:
        raise ValueError(f"Event not found: {event_id}")

    update = {"status": status}
    if status == "active":
        update["started_at"] = now_str()
    elif status == "finished":
        update["finished_at"] = now_str()
    sheets.update_row(SHEET_EVENTS, row_idx, update)
    _log(sheets, f"event_{status}", "event", event_id, f"Event status → {status}")


def get_event_countries(event_id: str) -> list[str]:
    sheets = get_sheets()
    rows = sheets.find_records(SHEET_EVENT_COUNTRIES, "event_id", event_id)
    return [r["country_code"] for r in rows]


def get_event_rewards(event_id: str) -> list[dict]:
    sheets = get_sheets()
    return sheets.find_records(SHEET_EVENT_REWARDS, "event_id", event_id)


def respond_participation(
    event_id: str,
    employee_id: str,
    country_code: str,
    status: str,  # accepted / declined
) -> dict:
    sheets = get_sheets()

    # Check existing
    all_parts = sheets.get_all_records(SHEET_EVENT_PARTICIPANTS)
    existing = next(
        (p for p in all_parts
         if p.get("event_id") == event_id and p.get("employee_id") == employee_id),
        None
    )

    if existing:
        row_idx = sheets.find_row_index(SHEET_EVENT_PARTICIPANTS, "participant_id",
                                         existing["participant_id"])
        if row_idx:
            sheets.update_row(SHEET_EVENT_PARTICIPANTS, row_idx, {
                "participant_status": status,
                "responded_at": now_str(),
            })
        return existing

    seq = sheets.get_next_seq(SHEET_EVENT_PARTICIPANTS)
    part_id = generate_participant_id(seq)
    row = [part_id, event_id, employee_id, country_code, status, now_str(), ""]
    sheets.append_row(SHEET_EVENT_PARTICIPANTS, row)
    _log(sheets, "participant_responded", "event", event_id,
         f"Employee {employee_id} → {status}")
    return {"participant_id": part_id, "status": status}


def get_events_for_employee(employee_id: str, country_code: str) -> list[dict]:
    """Return active events for employee's country."""
    sheets = get_sheets()
    all_events = get_active_events()
    result = []
    for ev in all_events:
        countries = get_event_countries(ev["event_id"])
        if country_code.upper() in [c.upper() for c in countries]:
            ev["rewards"] = get_event_rewards(ev["event_id"])
            # Check participation
            all_parts = sheets.get_all_records(SHEET_EVENT_PARTICIPANTS)
            part = next(
                (p for p in all_parts
                 if p.get("event_id") == ev["event_id"] and p.get("employee_id") == employee_id),
                None
            )
            ev["my_participation"] = part.get("participant_status", "") if part else ""
            result.append(ev)
    return result


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action,
        entity_type, entity_id, message
    ])
