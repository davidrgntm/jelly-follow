"""Scans service — core tracking logic with server-side pre-log."""
import logging
from app.integrations.google_sheets import get_sheets, SHEET_SCANS_RAW, SHEET_SYSTEM_LOGS
from app.utils.ids import generate_scan_id, generate_log_id
from app.utils.datetime_utils import now_str
from app.utils.fingerprint import compute_device_key, is_suspicious_ua
from app.utils.anti_abuse import check_abuse
from app.services.devices_service import check_device, mark_device_suspicious
from app.services.points_service import award_point

logger = logging.getLogger(__name__)


def create_server_pre_log(employee_id, employee_code, country_code, event_id,
                          qr_id, ip_address, forwarded_ip, user_agent, referer,
                          accept_language, request_path, query_string, instagram_target):
    """Server-side pre-log: record minimal data even if JS never runs."""
    sheets = get_sheets()
    seq = sheets.get_next_seq(SHEET_SCANS_RAW)
    scan_id = generate_scan_id(seq)
    suspicious = is_suspicious_ua(user_agent)
    scan_status = "suspicious" if suspicious else "opened"

    row = [
        scan_id, now_str(), employee_id, employee_code,
        event_id or "", country_code, qr_id or "",
        "", "", ip_address, forwarded_ip,
        user_agent, "", "", "", "",
        "", "", "", "",
        "", accept_language, referer, request_path, query_string,
        instagram_target, "no", "no",
        scan_status, "pending", "", now_str()
    ]
    sheets.append_row(SHEET_SCANS_RAW, row)
    logger.info("Pre-log created: %s for %s", scan_id, employee_code)
    return scan_id


def process_scan(employee_id, employee_code, country_code, event_id, qr_id,
                 ip_address, forwarded_ip, user_agent, referer, accept_language,
                 request_path, query_string, instagram_target,
                 client_device_id="", fingerprint_id="", device_type="", os_name="", browser_name="",
                 platform="", screen_width=0, screen_height=0, viewport_width=0,
                 viewport_height=0, timezone="", deep_link_attempted=False,
                 fallback_used=False, pre_scan_id=""):
    sheets = get_sheets()

    suspicious = is_suspicious_ua(user_agent)
    device_key = compute_device_key(
        client_device_id=client_device_id,
        fingerprint_id=fingerprint_id,
        os_name=os_name,
        browser_name=browser_name,
        platform=platform,
        screen_width=screen_width,
        screen_height=screen_height,
        timezone=timezone,
        user_agent=user_agent,
    )

    abuse = check_abuse(ip_address, device_key)
    if abuse["suspicious"]:
        suspicious = True

    point_tx_id = ""
    point_decision = "duplicate_device"
    scan_status = "suspicious" if suspicious else "redirected"

    if suspicious:
        point_decision = "suspicious"
        mark_device_suspicious(device_key, "suspicious_ua_or_abuse")
    else:
        is_new, _ = check_device(
            device_key=device_key, fingerprint_id=fingerprint_id,
            scan_id=pre_scan_id or "direct", employee_id=employee_id,
            event_id=event_id, country_code=country_code, ip_address=ip_address,
        )
        if is_new:
            point_tx_id = award_point(
                employee_id=employee_id, employee_code=employee_code,
                scan_id=pre_scan_id or "direct", device_key=device_key,
                country_code=country_code, event_id=event_id,
                reason_code="first_unique_device",
            )
            point_decision = "first_unique_device"

    if pre_scan_id:
        row_idx = sheets.find_row_index(SHEET_SCANS_RAW, "scan_id", pre_scan_id)
        if row_idx:
            # Idempotency: agar bu scan allaqachon final qarorga ega bo'lsa,
            # ikkinchi sendLogFast chaqiruvi point_decision ni overwrite qilmasin.
            FINAL_DECISIONS = {"first_unique_device", "suspicious", "duplicate_device"}
            existing = sheets.find_record(SHEET_SCANS_RAW, "scan_id", pre_scan_id)
            existing_decision = (existing or {}).get("point_decision", "")
            if existing_decision in FINAL_DECISIONS:
                # Ball allaqachon qayta ishlanganRed — qarorni saqlab qolamiz
                point_decision = existing_decision
                point_tx_id = (existing or {}).get("point_transaction_id", point_tx_id)
                logger.info(
                    "process_scan: pre_scan_id=%s already has decision=%s — skipping re-award",
                    pre_scan_id, existing_decision
                )

            sheets.update_row(SHEET_SCANS_RAW, row_idx, {
                "device_key": device_key, "fingerprint_id": fingerprint_id,
                "device_type": device_type, "os_name": os_name,
                "browser_name": browser_name, "platform": platform,
                "screen_width": screen_width, "screen_height": screen_height,
                "viewport_width": viewport_width, "viewport_height": viewport_height,
                "timezone": timezone,
                "deep_link_attempted": "yes" if deep_link_attempted else "no",
                "fallback_used": "yes" if fallback_used else "no",
                "scan_status": scan_status, "point_decision": point_decision,
                "point_transaction_id": point_tx_id,
            })
            _log(sheets, "scan_updated", "scan", pre_scan_id,
                 f"Client log: {employee_code}, decision={point_decision}")
            return {"scan_id": pre_scan_id, "device_key": device_key,
                    "point_decision": point_decision, "point_tx_id": point_tx_id,
                    "scan_status": scan_status}

    seq = sheets.get_next_seq(SHEET_SCANS_RAW)
    scan_id = generate_scan_id(seq)
    row = [
        scan_id, now_str(), employee_id, employee_code,
        event_id or "", country_code, qr_id or "",
        device_key, fingerprint_id, ip_address, forwarded_ip,
        user_agent, device_type, os_name, browser_name, platform,
        screen_width, screen_height, viewport_width, viewport_height,
        timezone, accept_language, referer, request_path, query_string,
        instagram_target, "yes" if deep_link_attempted else "no",
        "yes" if fallback_used else "no",
        scan_status, point_decision, point_tx_id, now_str()
    ]
    sheets.append_row(SHEET_SCANS_RAW, row)
    _log(sheets, "scan_recorded", "scan", scan_id,
         f"Scan by {employee_code}, decision={point_decision}")

    return {"scan_id": scan_id, "device_key": device_key,
            "point_decision": point_decision, "point_tx_id": point_tx_id,
            "scan_status": scan_status}


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action, entity_type, entity_id, message
    ])


def get_pending_reason(scan: dict) -> str:
    """Analyze WHY a scan is still pending and return a human-readable reason code."""
    decision = (scan.get("point_decision") or "").strip().lower()
    if decision != "pending":
        return ""

    device_key = (scan.get("device_key") or "").strip()
    fingerprint = (scan.get("fingerprint_id") or "").strip()
    scan_status = (scan.get("scan_status") or "").strip().lower()
    os_name = (scan.get("os_name") or "").strip()
    browser = (scan.get("browser_name") or "").strip()
    deep_link = (scan.get("deep_link_attempted") or "").strip().lower()
    fallback = (scan.get("fallback_used") or "").strip().lower()

    # 1) JS hech ishlamagan — device_key yo'q
    if not device_key and not fingerprint and not os_name and not browser:
        if scan_status == "opened":
            return "js_not_fired"          # JS umuman ishlamadi (sahifa tezda yopilgan)
        return "no_device_data"            # Qurilma ma'lumotlari kelmagan

    # 2) Device key bor lekin qaror hali chiqmagan (kamdan-kam holat)
    if device_key and decision == "pending":
        return "processing_incomplete"     # Jarayon yakunlanmagan

    # 3) Fingerprint bor, device_key yo'q
    if fingerprint and not device_key:
        return "fingerprint_only"          # Faqat fingerprint kelgan

    return "unknown"                       # Noma'lum sabab


def enrich_scans_with_reason(scans: list[dict]) -> list[dict]:
    """Add pending_reason field to each scan."""
    for s in scans:
        s["pending_reason"] = get_pending_reason(s)
    return scans


def resolve_scan(scan_id: str, action: str, admin_id: str) -> dict:
    """Manually resolve a pending scan.

    action: 'approve' — give point (first_unique_device)
            'reject'  — mark as rejected (no point)
    """
    sheets = get_sheets()
    scan = sheets.find_record(SHEET_SCANS_RAW, "scan_id", scan_id)
    if not scan:
        raise ValueError(f"Scan not found: {scan_id}")

    current_decision = (scan.get("point_decision") or "").strip().lower()
    if current_decision != "pending":
        raise ValueError(f"Scan already resolved: {current_decision}")

    row_idx = sheets.find_row_index(SHEET_SCANS_RAW, "scan_id", scan_id)
    if not row_idx:
        raise ValueError(f"Scan row not found: {scan_id}")

    employee_id = scan.get("employee_id", "")
    employee_code = scan.get("employee_code", "")
    country_code = scan.get("country_code", "")
    event_id = scan.get("event_id", "")
    device_key = scan.get("device_key", "")

    point_tx_id = ""

    if action == "approve":
        point_tx_id = award_point(
            employee_id=employee_id,
            employee_code=employee_code,
            scan_id=scan_id,
            device_key=device_key or f"manual_{scan_id}",
            country_code=country_code,
            event_id=event_id,
            reason_code="manual_approve",
        )
        new_decision = "first_unique_device"
        new_status = "approved_manual"
    elif action == "reject":
        new_decision = "rejected"
        new_status = "rejected_manual"
    else:
        raise ValueError(f"Invalid action: {action}")

    sheets.update_row(SHEET_SCANS_RAW, row_idx, {
        "point_decision": new_decision,
        "scan_status": new_status,
        "point_transaction_id": point_tx_id,
    })

    _log(sheets, f"scan_{action}", "scan", scan_id,
         f"Manual {action} by admin={admin_id}, employee={employee_code}, decision={new_decision}")

    logger.info("Scan %s %sd by admin %s → %s", scan_id, action, admin_id, new_decision)

    return {
        "scan_id": scan_id,
        "point_decision": new_decision,
        "scan_status": new_status,
        "point_tx_id": point_tx_id,
        "action": action,
    }
