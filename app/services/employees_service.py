"""
Employee service — registration, profile, stats.
"""
import logging
from typing import Optional

from app.integrations.google_sheets import (
    get_sheets, SHEET_EMPLOYEES, SHEET_POINT_TRANSACTIONS,
    SHEET_SCANS_RAW, SHEET_SYSTEM_LOGS,
)
from app.utils.ids import (
    generate_employee_id, generate_employee_code, generate_log_id,
)
from app.utils.datetime_utils import (
    now_str, start_of_day_utc, start_of_week_utc, start_of_month_utc,
)

logger = logging.getLogger(__name__)


def register_employee(
    telegram_user_id: str,
    telegram_username: str,
    full_name: str,
    phone: str,
    country_code: str,
    language_code: str,
) -> dict:
    """Create new employee. Returns employee dict."""
    sheets = get_sheets()

    # Check duplicate
    existing = sheets.find_record(SHEET_EMPLOYEES, "telegram_user_id", str(telegram_user_id))
    if existing:
        return existing

    seq = sheets.get_next_seq(SHEET_EMPLOYEES)
    employee_id = generate_employee_id(seq)

    # Employee code: per country sequence
    country_employees = sheets.find_records(SHEET_EMPLOYEES, "country_code", country_code.upper())
    country_seq = len(country_employees) + 1
    employee_code = generate_employee_code(country_code, country_seq)

    from app.config import settings
    short_link = f"{settings.TRACKING_DOMAIN}/r/{employee_code}"

    row = [
        employee_id, employee_code, full_name, phone,
        str(telegram_user_id), telegram_username or "",
        country_code.upper(), language_code.lower(),
        "active", now_str(), now_str(), "", short_link, ""
    ]
    sheets.append_row(SHEET_EMPLOYEES, row)

    # Log
    _log(sheets, "employee_created", "employee", employee_id,
         f"Employee created: {employee_code} ({full_name})")

    logger.info(f"Employee registered: {employee_id} / {employee_code}")
    return get_employee_by_telegram_id(telegram_user_id)


def get_employee_by_telegram_id(telegram_user_id) -> Optional[dict]:
    sheets = get_sheets()
    return sheets.find_record(SHEET_EMPLOYEES, "telegram_user_id", str(telegram_user_id))


def get_employee_by_id(employee_id: str) -> Optional[dict]:
    sheets = get_sheets()
    return sheets.find_record(SHEET_EMPLOYEES, "employee_id", employee_id)


def get_employee_by_code(employee_code: str) -> Optional[dict]:
    sheets = get_sheets()
    return sheets.find_record(SHEET_EMPLOYEES, "employee_code", employee_code)


def update_employee_qr(employee_id: str, qr_id: str):
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_EMPLOYEES, "employee_id", employee_id)
    if row_idx:
        sheets.update_row(SHEET_EMPLOYEES, row_idx, {"qr_id": qr_id, "last_active_at": now_str()})


def update_employee_status(employee_id: str, status: str, updated_by: str = "admin"):
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_EMPLOYEES, "employee_id", employee_id)
    if row_idx:
        sheets.update_row(SHEET_EMPLOYEES, row_idx, {"status": status})
    _log(sheets, "employee_status_changed", "employee", employee_id,
         f"Status changed to {status} by {updated_by}")


def update_employee_language(telegram_user_id: str, language_code: str):
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_EMPLOYEES, "telegram_user_id", str(telegram_user_id))
    if row_idx:
        sheets.update_row(SHEET_EMPLOYEES, row_idx, {"language_code": language_code})


def get_employee_stats(employee_id: str) -> dict:
    sheets = get_sheets()
    txs = sheets.find_records(SHEET_POINT_TRANSACTIONS, "employee_id", employee_id)
    scans = sheets.find_records(SHEET_SCANS_RAW, "employee_id", employee_id)

    total_points = sum(int(t.get("points_delta", 0)) for t in txs)

    day_start = start_of_day_utc().strftime("%Y-%m-%d")
    week_start = start_of_week_utc().strftime("%Y-%m-%d")
    month_start = start_of_month_utc().strftime("%Y-%m-%d %H:%M:%S")

    today_pts = sum(
        int(t.get("points_delta", 0)) for t in txs
        if t.get("created_at", "") >= day_start
    )
    week_pts = sum(
        int(t.get("points_delta", 0)) for t in txs
        if t.get("created_at", "") >= week_start
    )
    month_pts = sum(
        int(t.get("points_delta", 0)) for t in txs
        if t.get("created_at", "") >= month_start
    )

    unique_devices = len({
        s.get("device_key") for s in scans
        if s.get("point_decision") == "first_unique_device"
    })
    duplicate_scans = len([
        s for s in scans
        if s.get("point_decision") == "duplicate_device"
    ])

    return {
        "total_points": total_points,
        "today_points": today_pts,
        "week_points": week_pts,
        "month_points": month_pts,
        "unique_devices": unique_devices,
        "duplicate_scans": duplicate_scans,
        "total_scans": len(scans),
    }


def get_all_employees() -> list[dict]:
    sheets = get_sheets()
    return sheets.get_all_records(SHEET_EMPLOYEES)


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action,
        entity_type, entity_id, message
    ])
