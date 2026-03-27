"""
Admin service.
"""
import logging
from typing import Optional

from app.integrations.google_sheets import (
    get_sheets, SHEET_ADMINS, SHEET_SYSTEM_LOGS,
)
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
        admin_id, str(telegram_user_id), full_name, phone,
        role_code, "active", now_str(), created_by
    ]
    sheets.append_row(SHEET_ADMINS, row)

    _log(sheets, "admin_created", "admin", admin_id,
         f"Admin created: {role_code} / {full_name}")
    logger.info(f"Admin created: {admin_id}")
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


def is_super_admin(telegram_user_id) -> bool:
    admin = get_admin_by_telegram_id(telegram_user_id)
    return (
        admin is not None
        and admin.get("status") == "active"
        and admin.get("role_code") == "super_admin"
    )


def get_all_admins() -> list[dict]:
    sheets = get_sheets()
    return sheets.get_all_records(SHEET_ADMINS)


def seed_super_admin(telegram_user_id: str):
    """Create super admin from env on first run."""
    from app.config import settings
    existing = get_admin_by_telegram_id(telegram_user_id)
    if not existing:
        create_admin(
            telegram_user_id=telegram_user_id,
            full_name="Super Admin",
            phone="",
            role_code="super_admin",
            created_by="system",
        )
        logger.info(f"Super admin seeded: {telegram_user_id}")


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action,
        entity_type, entity_id, message
    ])
