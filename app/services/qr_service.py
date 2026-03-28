"""
QR code service — generate and store QR codes.
"""
import logging
from typing import Optional

from app.integrations.google_sheets import get_sheets, SHEET_QR_CODES, SHEET_SYSTEM_LOGS
from app.integrations.qr_generator import generate_qr_image
from app.utils.ids import generate_qr_id, generate_log_id
from app.utils.datetime_utils import now_str
from app.config import settings
from app.services.employees_service import update_employee_qr
from app.services.events_service import get_event_by_id

logger = logging.getLogger(__name__)


def generate_employee_qr(employee_id: str, employee_code: str, country_code: str) -> dict:
    sheets = get_sheets()
    existing = sheets.find_record(SHEET_QR_CODES, "employee_id", employee_id)
    if existing and existing.get("event_id") == "":
        return existing

    short_link = f"{settings.TRACKING_DOMAIN}/r/{employee_code}"
    seq = sheets.get_next_seq(SHEET_QR_CODES)
    qr_id = generate_qr_id(seq)
    filename = f"{qr_id}.png"

    filepath = generate_qr_image(short_link, filename)

    row = [
        qr_id,
        short_link,
        employee_id,
        employee_code,
        "",
        country_code,
        short_link,
        f"/static/qr/{filename}",
        "yes",
        now_str(),
    ]
    sheets.append_row(SHEET_QR_CODES, row)
    update_employee_qr(employee_id, qr_id)

    _log(sheets, "qr_created", "employee", employee_id, f"QR created: {qr_id} for {employee_code}")

    return {
        "qr_id": qr_id,
        "short_link": short_link,
        "qr_image_path": filepath,
        "employee_code": employee_code,
    }


def generate_event_qr(employee_id: str, employee_code: str, event_id: str, country_code: str) -> dict:
    sheets = get_sheets()
    event = get_event_by_id(event_id)
    if not event:
        raise ValueError(f"Event not found: {event_id}")

    event_code = event.get("event_code") or event_id
    existing = next(
        (
            qr
            for qr in sheets.find_records(SHEET_QR_CODES, "employee_id", employee_id)
            if qr.get("event_id") == event_id
        ),
        None,
    )
    if existing:
        return existing

    short_link = f"{settings.TRACKING_DOMAIN}/r/{employee_code}?event={event_code}"
    seq = sheets.get_next_seq(SHEET_QR_CODES)
    qr_id = generate_qr_id(seq)
    filename = f"{qr_id}.png"

    filepath = generate_qr_image(short_link, filename)

    row = [
        qr_id,
        short_link,
        employee_id,
        employee_code,
        event_id,
        country_code,
        short_link,
        f"/static/qr/{filename}",
        "yes",
        now_str(),
    ]
    sheets.append_row(SHEET_QR_CODES, row)

    _log(sheets, "qr_event_created", "employee", employee_id, f"Event QR created: {qr_id} event={event_id}")

    return {
        "qr_id": qr_id,
        "short_link": short_link,
        "qr_image_path": filepath,
        "event_id": event_id,
        "event_code": event_code,
    }


def get_qr_bytes(employee_id: str) -> Optional[bytes]:
    sheets = get_sheets()
    qr = sheets.find_record(SHEET_QR_CODES, "employee_id", employee_id)
    if not qr:
        return None
    from app.integrations.qr_generator import generate_qr_bytes

    return generate_qr_bytes(qr["short_link"])


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [generate_log_id(seq), now_str(), level, action, entity_type, entity_id, message])
