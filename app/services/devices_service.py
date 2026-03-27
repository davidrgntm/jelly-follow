"""
Device uniqueness module.
1 unique device = 1 ball (globally, across all employees).
"""
import logging
from typing import Optional, Tuple

from app.integrations.google_sheets import (
    get_sheets, SHEET_DEVICE_REGISTRY,
)
from app.utils.datetime_utils import now_str

logger = logging.getLogger(__name__)


def check_device(
    device_key: str,
    fingerprint_id: str,
    scan_id: str,
    employee_id: str,
    event_id: str,
    country_code: str,
    ip_address: str,
) -> Tuple[bool, Optional[dict]]:
    """
    Check if device is new.
    Returns (is_new_device, existing_record_or_None)
    If new: creates registry entry with point_already_given=yes
    If existing: updates last_seen_at and total_scans
    """
    sheets = get_sheets()
    existing = sheets.find_record(SHEET_DEVICE_REGISTRY, "device_key", device_key)

    if existing:
        # Known device — update counters
        row_idx = sheets.find_row_index(SHEET_DEVICE_REGISTRY, "device_key", device_key)
        if row_idx:
            total = int(existing.get("total_scans", 0)) + 1
            sheets.update_row(SHEET_DEVICE_REGISTRY, row_idx, {
                "last_seen_at": now_str(),
                "total_scans": total,
            })
        logger.info(f"Duplicate device: {device_key[:16]}...")
        return False, existing

    # New device — register it
    row = [
        device_key, fingerprint_id, scan_id,
        employee_id, event_id or "", country_code,
        ip_address, now_str(), now_str(),
        1, "yes", "clean", ""
    ]
    sheets.append_row(SHEET_DEVICE_REGISTRY, row)
    logger.info(f"New device registered: {device_key[:16]}...")
    return True, None


def mark_device_suspicious(device_key: str, reason: str = ""):
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_DEVICE_REGISTRY, "device_key", device_key)
    if row_idx:
        sheets.update_row(SHEET_DEVICE_REGISTRY, row_idx, {
            "device_status": "suspicious",
            "notes": reason,
        })
