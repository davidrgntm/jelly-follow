"""Admin service."""
import logging
from typing import Optional
from app.integrations.google_sheets import (
    get_sheets, SHEET_ADMINS, SHEET_SYSTEM_LOGS, SHEET_EMPLOYEES,
    SHEET_EVENTS, SHEET_SCANS_RAW, SHEET_POINT_TRANSACTIONS, SHEET_DEVICE_REGISTRY,
)
from app.utils.ids import generate_admin_id, generate_log_id
from app.utils.datetime_utils import now_str

logger = logging.getLogger(__name__)

def create_admin(telegram_user_id, full_name, phone, role_code, created_by):
    sheets = get_sheets()
    existing = sheets.find_record(SHEET_ADMINS, "telegram_user_id", str(telegram_user_id))
    if existing:
        return existing
    seq = sheets.get_next_seq(SHEET_ADMINS)
    admin_id = generate_admin_id(seq)
    row = [admin_id, str(telegram_user_id), full_name, phone, role_code,
           "active", now_str(), created_by]
    sheets.append_row(SHEET_ADMINS, row)
    _log(sheets, "admin_created", "admin", admin_id, f"Admin created: {role_code} / {full_name}")
    logger.info("Admin created: %s", admin_id)
    return get_admin_by_id(admin_id)

def get_admin_by_telegram_id(telegram_user_id):
    sheets = get_sheets()
    return sheets.find_record(SHEET_ADMINS, "telegram_user_id", str(telegram_user_id))

def get_admin_by_id(admin_id):
    sheets = get_sheets()
    return sheets.find_record(SHEET_ADMINS, "admin_id", admin_id)

def is_admin(telegram_user_id):
    admin = get_admin_by_telegram_id(telegram_user_id)
    return admin is not None and admin.get("status") == "active"

def has_role(telegram_user_id, *roles):
    admin = get_admin_by_telegram_id(telegram_user_id)
    return bool(admin and admin.get("status") == "active" and admin.get("role_code") in set(roles))

def is_super_admin(telegram_user_id):
    return has_role(telegram_user_id, "super_admin")

def get_all_admins():
    return get_sheets().get_all_records(SHEET_ADMINS)

def seed_super_admin(telegram_user_id):
    existing = get_admin_by_telegram_id(telegram_user_id)
    if not existing:
        create_admin(telegram_user_id=telegram_user_id, full_name="Super Admin",
                     phone="", role_code="super_admin", created_by="system")
        logger.info("Super admin seeded: %s", telegram_user_id)

def get_system_stats():
    sheets = get_sheets()
    employees = sheets.get_all_records(SHEET_EMPLOYEES)
    events = sheets.get_all_records(SHEET_EVENTS)
    scans = sheets.get_all_records(SHEET_SCANS_RAW)
    points = sheets.get_all_records(SHEET_POINT_TRANSACTIONS)
    devices = sheets.get_all_records(SHEET_DEVICE_REGISTRY)
    country_stats = {}
    for e in employees:
        cc = e.get("country_code", "??")
        country_stats.setdefault(cc, {"employees": 0, "active": 0})
        country_stats[cc]["employees"] += 1
        if e.get("status") == "active":
            country_stats[cc]["active"] += 1
    return {
        "employees_total": len(employees),
        "employees_active": len([e for e in employees if e.get("status") == "active"]),
        "admins_total": len(get_all_admins()),
        "events_total": len(events),
        "events_active": len([e for e in events if e.get("status") == "active"]),
        "scans_total": len(scans),
        "unique_awards": len([s for s in scans if s.get("point_decision") == "first_unique_device"]),
        "duplicate_scans": len([s for s in scans if s.get("point_decision") == "duplicate_device"]),
        "suspicious_scans": len([s for s in scans if s.get("point_decision") == "suspicious"]),
        "points_total": sum(int(p.get("points_delta", 0) or 0) for p in points),
        "devices_total": len(devices),
        "devices_clean": len([d for d in devices if d.get("device_status") == "clean"]),
        "devices_suspicious": len([d for d in devices if d.get("device_status") == "suspicious"]),
        "country_stats": country_stats,
    }

def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action, entity_type, entity_id, message
    ])
