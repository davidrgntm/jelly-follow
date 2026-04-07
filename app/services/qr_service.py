"""QR code service — generate, rotate and store QR codes."""
import logging
import time
from typing import Optional
from urllib.parse import urlencode

from app.integrations.google_sheets import get_sheets, SHEET_QR_CODES, SHEET_SYSTEM_LOGS
from app.integrations.qr_generator import generate_qr_image, generate_qr_bytes
from app.utils.ids import generate_qr_id, generate_log_id
from app.utils.datetime_utils import now_str
from app.config import settings
from app.services.employees_service import update_employee_qr

logger = logging.getLogger(__name__)


def _build_short_link(employee_code: str, event_code: str = "", qr_id: str = "") -> str:
    base = f"{settings.TRACKING_DOMAIN}/r/{employee_code}"
    params = {}
    if event_code:
        params["event"] = event_code
    if qr_id:
        params["qr"] = qr_id
        params["v"] = str(int(time.time()))
    return f"{base}?{urlencode(params)}" if params else base


def _list_employee_qrs(employee_id: str) -> list[dict]:
    sheets = get_sheets()
    return sheets.find_records(SHEET_QR_CODES, "employee_id", employee_id)


def _deactivate_qrs(employee_id: str, event_id: str = "") -> None:
    sheets = get_sheets()
    qrs = _list_employee_qrs(employee_id)
    for qr in qrs:
        same_scope = (qr.get("event_id", "") or "") == (event_id or "")
        if not same_scope:
            continue
        if qr.get("is_active") == "yes":
            row_idx = sheets.find_row_index(SHEET_QR_CODES, "qr_id", qr.get("qr_id"))
            if row_idx:
                sheets.update_row(SHEET_QR_CODES, row_idx, {"is_active": "no"})


def _latest_qr(employee_id: str, event_id: str = "") -> Optional[dict]:
    qrs = [q for q in _list_employee_qrs(employee_id) if (q.get("event_id", "") or "") == (event_id or "")]
    if not qrs:
        return None
    qrs.sort(key=lambda x: (x.get("created_at", ""), x.get("qr_id", "")), reverse=True)
    active = next((q for q in qrs if q.get("is_active") == "yes"), None)
    return active or qrs[0]


def get_qr_by_id(qr_id: str) -> Optional[dict]:
    sheets = get_sheets()
    return sheets.find_record(SHEET_QR_CODES, "qr_id", qr_id)


def _create_qr_record(employee_id: str, employee_code: str, country_code: str,
                      event_id: str = "", event_code: str = "", rotate: bool = False) -> dict:
    sheets = get_sheets()

    if rotate:
        _deactivate_qrs(employee_id, event_id=event_id)
    else:
        existing = _latest_qr(employee_id, event_id=event_id)
        if existing:
            return existing

    seq = sheets.get_next_seq(SHEET_QR_CODES)
    qr_id = generate_qr_id(seq)
    short_link = _build_short_link(employee_code, event_code=event_code, qr_id=qr_id if rotate else "")
    filename = f"{qr_id}.png"
    filepath = generate_qr_image(short_link, filename)
    row = [
        qr_id,
        short_link,
        employee_id,
        employee_code,
        event_id or "",
        country_code,
        short_link,
        f"/static/qr/{filename}",
        "yes",
        now_str(),
    ]
    sheets.append_row(SHEET_QR_CODES, row)
    if not event_id:
        update_employee_qr(employee_id, qr_id)
    _log(sheets, "qr_created_rotated" if rotate else "qr_created", "employee", employee_id,
         f"QR created: {qr_id} event={event_id or '-'} rotate={rotate}")
    return {
        "qr_id": qr_id,
        "short_link": short_link,
        "qr_image_path": filepath,
        "employee_id": employee_id,
        "employee_code": employee_code,
        "event_id": event_id or "",
        "event_code": event_code or "",
        "country_code": country_code,
        "is_active": "yes",
        "created_at": now_str(),
    }


def generate_employee_qr(employee_id, employee_code, country_code):
    return _create_qr_record(employee_id, employee_code, country_code, event_id="", event_code="", rotate=False)


def rotate_employee_qr(employee_id, employee_code, country_code):
    return _create_qr_record(employee_id, employee_code, country_code, event_id="", event_code="", rotate=True)


def generate_event_qr(employee_id, employee_code, event_id, country_code):
    from app.services.events_service import get_event_by_id
    event = get_event_by_id(event_id)
    if not event:
        raise ValueError(f"Event not found: {event_id}")
    event_code = event.get("event_code") or event_id
    return _create_qr_record(employee_id, employee_code, country_code, event_id=event_id, event_code=event_code, rotate=False)


def rotate_event_qr(employee_id, employee_code, event_id, country_code):
    from app.services.events_service import get_event_by_id
    event = get_event_by_id(event_id)
    if not event:
        raise ValueError(f"Event not found: {event_id}")
    event_code = event.get("event_code") or event_id
    return _create_qr_record(employee_id, employee_code, country_code, event_id=event_id, event_code=event_code, rotate=True)


def get_qr_bytes(employee_id):
    qr = _latest_qr(employee_id)
    if not qr:
        return None
    return generate_qr_bytes(qr["short_link"])


def get_event_qr_bytes(employee_id, event_id):
    qr = _latest_qr(employee_id, event_id=event_id)
    if not qr:
        return None
    return generate_qr_bytes(qr["short_link"])


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action, entity_type, entity_id, message
    ])
