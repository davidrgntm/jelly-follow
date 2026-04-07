"""Event bonus tasks: extra point actions inside events."""
import logging

from app.integrations.google_sheets import (
    get_sheets,
    SHEET_EVENT_BONUS_RULES,
    SHEET_EVENT_BONUS_SUBMISSIONS,
    SHEET_SYSTEM_LOGS,
)
from app.services.points_service import award_point
from app.services.employees_service import get_employee_by_id
from app.utils.ids import generate_bonus_rule_id, generate_bonus_submission_id, generate_log_id
from app.utils.datetime_utils import now_str
from app.utils.cache import invalidate_events

logger = logging.getLogger(__name__)

ALLOWED_TASK_TYPES = {
    "story_mention",
    "story_with_store_visit",
    "blogger_mention",
    "blogger_mention_10k",
    "reel_mention",
    "review_video",
    "photo_with_product",
    "other",
}
ALLOWED_SUBMISSION_STATUSES = {"pending", "approved", "rejected"}


def create_bonus_rule(event_id: str, title: str, points: int, created_by: str,
                      description: str = "", task_type: str = "other",
                      max_per_employee: int = 1, requires_moderation: bool = True,
                      min_followers: int = 0, is_active: bool = True, sort_order: int = 100) -> dict:
    task_type = (task_type or "other").strip().lower()
    if task_type not in ALLOWED_TASK_TYPES:
        task_type = "other"

    sheets = get_sheets()
    seq = sheets.get_next_seq(SHEET_EVENT_BONUS_RULES)
    rule_id = generate_bonus_rule_id(seq)
    row = [
        rule_id,
        event_id,
        title,
        description,
        task_type,
        int(points),
        int(max_per_employee or 1),
        "yes" if requires_moderation else "no",
        int(min_followers or 0),
        "yes" if is_active else "no",
        int(sort_order or 100),
        now_str(),
        created_by,
    ]
    sheets.append_row(SHEET_EVENT_BONUS_RULES, row)
    invalidate_events()
    _log(sheets, "event_bonus_rule_created", "event", event_id, f"Bonus rule created: {rule_id}")
    return get_bonus_rule(rule_id)


def get_bonus_rule(rule_id: str):
    sheets = get_sheets()
    return sheets.find_record(SHEET_EVENT_BONUS_RULES, "bonus_rule_id", rule_id)


def list_bonus_rules(event_id: str, only_active: bool = False) -> list[dict]:
    sheets = get_sheets()
    rules = sheets.find_records(SHEET_EVENT_BONUS_RULES, "event_id", event_id)
    if only_active:
        rules = [r for r in rules if r.get("is_active") == "yes"]
    try:
        rules.sort(key=lambda r: (int(r.get("sort_order", 9999) or 9999), r.get("title", "")))
    except Exception:
        pass
    return rules


def submit_bonus(event_id: str, bonus_rule_id: str, employee_id: str,
                 evidence_url: str = "", notes: str = "") -> dict:
    sheets = get_sheets()
    rule = get_bonus_rule(bonus_rule_id)
    if not rule or rule.get("event_id") != event_id:
        raise ValueError("Bonus rule not found")
    if rule.get("is_active") != "yes":
        raise ValueError("Bonus rule is inactive")

    employee = get_employee_by_id(employee_id)
    if not employee:
        raise ValueError("Employee not found")

    existing = get_employee_rule_submissions(event_id, bonus_rule_id, employee_id)
    approved_count = len([s for s in existing if s.get("status") == "approved"])
    max_per_employee = int(rule.get("max_per_employee", 1) or 1)
    if approved_count >= max_per_employee:
        raise ValueError("Submission limit reached for this bonus task")

    seq = sheets.get_next_seq(SHEET_EVENT_BONUS_SUBMISSIONS)
    submission_id = generate_bonus_submission_id(seq)
    row = [
        submission_id,
        event_id,
        bonus_rule_id,
        employee_id,
        employee.get("employee_code", ""),
        employee.get("country_code", ""),
        "pending",
        evidence_url,
        notes,
        "0",
        "",
        now_str(),
        "",
        "",
    ]
    sheets.append_row(SHEET_EVENT_BONUS_SUBMISSIONS, row)
    _log(sheets, "event_bonus_submitted", "event", event_id, f"Submission created: {submission_id}")
    return get_submission(submission_id)


def get_submission(submission_id: str):
    sheets = get_sheets()
    return sheets.find_record(SHEET_EVENT_BONUS_SUBMISSIONS, "submission_id", submission_id)


def list_submissions(event_id: str, status: str = "") -> list[dict]:
    sheets = get_sheets()
    rows = sheets.find_records(SHEET_EVENT_BONUS_SUBMISSIONS, "event_id", event_id)
    if status:
        rows = [r for r in rows if r.get("status") == status]
    rows.sort(key=lambda r: (r.get("created_at", ""), r.get("submission_id", "")), reverse=True)
    return rows


def get_employee_rule_submissions(event_id: str, bonus_rule_id: str, employee_id: str) -> list[dict]:
    rows = list_submissions(event_id)
    return [r for r in rows if r.get("bonus_rule_id") == bonus_rule_id and r.get("employee_id") == employee_id]


def review_submission(submission_id: str, status: str, admin_id: str, notes: str = "") -> dict:
    status = (status or "").strip().lower()
    if status not in {"approved", "rejected"}:
        raise ValueError("Invalid review status")

    sheets = get_sheets()
    submission = get_submission(submission_id)
    if not submission:
        raise ValueError("Submission not found")
    if submission.get("status") != "pending":
        raise ValueError(f"Submission already reviewed: {submission.get('status')}")

    rule = get_bonus_rule(submission.get("bonus_rule_id", ""))
    if not rule:
        raise ValueError("Bonus rule not found")

    row_idx = sheets.find_row_index(SHEET_EVENT_BONUS_SUBMISSIONS, "submission_id", submission_id)
    if not row_idx:
        raise ValueError("Submission row not found")

    update = {
        "status": status,
        "notes": notes or submission.get("notes", ""),
        "reviewed_at": now_str(),
        "reviewed_by": admin_id,
    }

    if status == "approved":
        employee = get_employee_by_id(submission.get("employee_id", ""))
        if not employee:
            raise ValueError("Employee not found")
        points = int(rule.get("points", 0) or 0)
        reason_code = f"bonus:{rule.get('task_type') or rule.get('bonus_rule_id')}"
        point_tx_id = award_point(
            employee_id=submission.get("employee_id", ""),
            employee_code=employee.get("employee_code", ""),
            scan_id=f"bonus:{submission_id}",
            device_key=f"bonus:{submission.get('bonus_rule_id', '')}:{submission.get('employee_id', '')}",
            country_code=employee.get("country_code", ""),
            event_id=submission.get("event_id", ""),
            reason_code=reason_code,
            points=points,
            created_by=admin_id,
        )
        update["points_awarded"] = str(points)
        update["point_tx_id"] = point_tx_id
    else:
        update["points_awarded"] = "0"
        update["point_tx_id"] = ""

    sheets.update_row(SHEET_EVENT_BONUS_SUBMISSIONS, row_idx, update)
    _log(sheets, f"event_bonus_{status}", "event", submission.get("event_id", ""),
         f"Submission {submission_id} -> {status}")
    return get_submission(submission_id)


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action, entity_type, entity_id, message
    ])
