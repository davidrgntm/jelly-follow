"""
Admin service.
"""
import logging
from typing import Optional

from app.integrations.google_sheets import get_sheets, SHEET_ADMINS, SHEET_SYSTEM_LOGS, SHEET_EMPLOYEES, SHEET_EVENTS, SHEET_SCANS_RAW, SHEET_POINT_TRANSACTIONS
from app.utils.ids import generate_admin_id, generate_log_id
from app.utils.datetime_utils import now_str

logger = logging.getLogger(__name__)


def create_admin(
    telegram_user_id: str,
    full_name: str,
    phone: str,
    role_code: str,
    created_by: str,
) -> dict:
    sheets = get_sheets()

    existing = sheets.find_record(SHEET_ADMINS, "telegram_user_id", str(telegram_user_id))
    if existing:
        return existing

    seq = sheets.get_next_seq(SHEET_ADMINS)
    admin_id = generate_admin_id(seq)

    row = [
        admin_id,
        str(telegram_user_id),
        full_name,
        phone,
        role_code,
        "active",
        now_str(),
        created_by,
    ]
    sheets.append_row(SHEET_ADMINS, row)

    _log(sheets, "admin_created", "admin", admin_id, f"Admin created: {role_code} / {full_name}")
    logger.info("Admin created: %s", admin_id)
    return get_admin_by_id(admin_id)


def get_admin_by_telegram_id(telegram_user_id) -> Optional[dict]:
    sheets = get_sheets()
    return sheets.find_record(SHEET_ADMINS, "telegram_user_id", str(telegram_user_id))


def get_admin_by_id(admin_id: str) -> Optional[dict]:
    sheets = get_sheets()
    return sheets.find_record(SHEET_ADMINS, "admin_id", admin_id)


def is_admin(telegram_user_id) -> bool:
    admin = get_admin_by_telegram_id(telegram_user_id)
    return admin is not None and admin.get("status") == "active"


def has_role(telegram_user_id, *roles: str) -> bool:
    admin = get_admin_by_telegram_id(telegram_user_id)
    return bool(admin and admin.get("status") == "active" and admin.get("role_code") in set(roles))


def is_super_admin(telegram_user_id) -> bool:
    return has_role(telegram_user_id, "super_admin")


def get_all_admins() -> list[dict]:
    sheets = get_sheets()
    return sheets.get_all_records(SHEET_ADMINS)


def seed_super_admin(telegram_user_id: str):
    existing = get_admin_by_telegram_id(telegram_user_id)
    if not existing:
        create_admin(
            telegram_user_id=telegram_user_id,
            full_name="Super Admin",
            phone="",
            role_code="super_admin",
            created_by="system",
        )
        logger.info("Super admin seeded: %s", telegram_user_id)


def get_system_stats() -> dict:
    sheets = get_sheets()
    employees = sheets.get_all_records(SHEET_EMPLOYEES)
    events = sheets.get_all_records(SHEET_EVENTS)
    scans = sheets.get_all_records(SHEET_SCANS_RAW)
    points = sheets.get_all_records(SHEET_POINT_TRANSACTIONS)

    return {
        "employees_total": len(employees),
        "employees_active": len([e for e in employees if e.get("status") == "active"]),
        "admins_total": len(get_all_admins()),
        "events_total": len(events),
        "events_active": len([e for e in events if e.get("status") == "active"]),
        "scans_total": len(scans),
        "unique_awards": len([s for s in scans if s.get("point_decision") == "first_unique_device"]),
        "duplicate_scans": len([s for s in scans if s.get("point_decision") == "duplicate_device"]),
        "points_total": sum(int(p.get("points_delta", 0) or 0) for p in points),
    }


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [generate_log_id(seq), now_str(), level, action, entity_type, entity_id, message])
