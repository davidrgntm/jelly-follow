"""
Scans service — core tracking logic.
Records every scan event and coordinates device check + point award.
"""
import logging
from typing import Optional

from app.integrations.google_sheets import (
    get_sheets, SHEET_SCANS_RAW, SHEET_SYSTEM_LOGS,
)
from app.utils.ids import generate_scan_id, generate_log_id
from app.utils.datetime_utils import now_str
from app.utils.fingerprint import compute_device_key, is_suspicious_ua
from app.services.devices_service import check_device, mark_device_suspicious
from app.services.points_service import award_point

logger = logging.getLogger(__name__)


def process_scan(
    employee_id: str,
    employee_code: str,
    country_code: str,
    event_id: str,
    qr_id: str,
    # Server-side
    ip_address: str,
    forwarded_ip: str,
    user_agent: str,
    referer: str,
    accept_language: str,
    request_path: str,
    query_string: str,
    instagram_target: str,
    # Client-side (sent by JS)
    fingerprint_id: str = "",
    device_type: str = "",
    os_name: str = "",
    browser_name: str = "",
    platform: str = "",
    screen_width: int = 0,
    screen_height: int = 0,
    viewport_width: int = 0,
    viewport_height: int = 0,
    timezone: str = "",
    deep_link_attempted: bool = False,
    fallback_used: bool = False,
) -> dict:
    """
    Full scan processing:
    1. Compute device_key
    2. Check device uniqueness
    3. Award point if new device
    4. Write scan log
    Returns scan result dict.
    """
    sheets = get_sheets()
    seq = sheets.get_next_seq(SHEET_SCANS_RAW)
    scan_id = generate_scan_id(seq)

    # Suspicious UA check
    suspicious = is_suspicious_ua(user_agent)
    scan_status = "suspicious" if suspicious else "redirected"

    # Compute device fingerprint
    device_key = compute_device_key(
        fingerprint_id=fingerprint_id,
        os_name=os_name,
        browser_name=browser_name,
        platform=platform,
        screen_width=screen_width,
        screen_height=screen_height,
        timezone=timezone,
        user_agent=user_agent,
    )

    point_tx_id = ""
    point_decision = "duplicate_device"

    if suspicious:
        point_decision = "suspicious"
        mark_device_suspicious(device_key, "suspicious_ua")
    else:
        is_new, _ = check_device(
            device_key=device_key,
            fingerprint_id=fingerprint_id,
            scan_id=scan_id,
            employee_id=employee_id,
            event_id=event_id,
            country_code=country_code,
            ip_address=ip_address,
        )
        if is_new:
            point_tx_id = award_point(
                employee_id=employee_id,
                employee_code=employee_code,
                scan_id=scan_id,
                device_key=device_key,
                country_code=country_code,
                event_id=event_id,
                reason_code="first_unique_device",
            )
            point_decision = "first_unique_device"

    # Write scan log
    row = [
        scan_id, now_str(), employee_id, employee_code,
        event_id or "", country_code, qr_id or "",
        device_key, fingerprint_id, ip_address, forwarded_ip,
        user_agent, device_type, os_name, browser_name, platform,
        screen_width, screen_height, viewport_width, viewport_height,
        timezone, accept_language, referer, request_path, query_string,
        instagram_target,
        "yes" if deep_link_attempted else "no",
        "yes" if fallback_used else "no",
        scan_status, point_decision, point_tx_id, now_str()
    ]
    sheets.append_row(SHEET_SCANS_RAW, row)

    _log(sheets, "scan_recorded", "scan", scan_id,
         f"Scan by {employee_code}, decision={point_decision}")

    return {
        "scan_id": scan_id,
        "device_key": device_key,
        "point_decision": point_decision,
        "point_tx_id": point_tx_id,
        "scan_status": scan_status,
    }


def update_scan_client_data(scan_id: str, data: dict):
    """Update scan record with client-side JS data."""
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_SCANS_RAW, "scan_id", scan_id)
    if row_idx:
        sheets.update_row(SHEET_SCANS_RAW, row_idx, data)


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action,
        entity_type, entity_id, message
    ])
