"""Device uniqueness with cache + anti-abuse integration."""
import logging
from typing import Tuple, Optional
from app.integrations.google_sheets import get_sheets, SHEET_DEVICE_REGISTRY
from app.utils.datetime_utils import now_str
from app.utils.cache import device_cache
from app.utils.anti_abuse import check_abuse

logger = logging.getLogger(__name__)


def check_device(device_key, fingerprint_id, scan_id, employee_id,
                 event_id, country_code, ip_address) -> Tuple[bool, Optional[dict]]:
    sheets = get_sheets()

    cached = device_cache.get(f"dk:{device_key}")
    if cached is not None:
        row_idx = sheets.find_row_index(SHEET_DEVICE_REGISTRY, "device_key", device_key)
        if row_idx:
            total = int(cached.get("total_scans", 0)) + 1
            sheets.update_row(SHEET_DEVICE_REGISTRY, row_idx, {
                "last_seen_at": now_str(), "total_scans": total,
            })
            cached["total_scans"] = total
            device_cache.set(f"dk:{device_key}", cached)
        logger.info("Duplicate device (cached): %s...", device_key[:16])
        return False, cached

    existing = sheets.find_record(SHEET_DEVICE_REGISTRY, "device_key", device_key)
    if existing:
        device_cache.set(f"dk:{device_key}", existing)
        row_idx = sheets.find_row_index(SHEET_DEVICE_REGISTRY, "device_key", device_key)
        if row_idx:
            total = int(existing.get("total_scans", 0)) + 1
            sheets.update_row(SHEET_DEVICE_REGISTRY, row_idx, {
                "last_seen_at": now_str(), "total_scans": total,
            })
        logger.info("Duplicate device: %s...", device_key[:16])
        return False, existing

    abuse = check_abuse(ip_address, device_key)
    device_status = "suspicious" if abuse["suspicious"] else "clean"
    notes = "; ".join(abuse["reasons"]) if abuse["suspicious"] else ""

    row = [
        device_key, fingerprint_id, scan_id,
        employee_id, event_id or "", country_code,
        ip_address, now_str(), now_str(),
        1, "yes", device_status, notes
    ]
    sheets.append_row(SHEET_DEVICE_REGISTRY, row)
    new_record = {"device_key": device_key, "total_scans": 1,
                  "device_status": device_status, "point_already_given": "yes"}
    device_cache.set(f"dk:{device_key}", new_record)

    logger.info("New device registered: %s... status=%s", device_key[:16], device_status)
    return True, None


def mark_device_suspicious(device_key, reason=""):
    sheets = get_sheets()
    row_idx = sheets.find_row_index(SHEET_DEVICE_REGISTRY, "device_key", device_key)
    if row_idx:
        sheets.update_row(SHEET_DEVICE_REGISTRY, row_idx, {
            "device_status": "suspicious", "notes": reason,
        })
    device_cache.delete(f"dk:{device_key}")
