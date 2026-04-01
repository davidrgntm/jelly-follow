"""Points service — awards, penalties, manual adjustments."""
import logging
from app.integrations.google_sheets import get_sheets, SHEET_POINT_TRANSACTIONS, SHEET_SYSTEM_LOGS
from app.utils.ids import generate_point_tx_id, generate_log_id
from app.utils.datetime_utils import now_str
from app.utils.cache import leaderboard_cache

logger = logging.getLogger(__name__)


def award_point(employee_id, employee_code, scan_id, device_key, country_code,
                event_id="", reason_code="first_unique_device", points=1, created_by="system"):
    sheets = get_sheets()
    seq = sheets.get_next_seq(SHEET_POINT_TRANSACTIONS)
    tx_id = generate_point_tx_id(seq)
    row = [tx_id, employee_id, employee_code, event_id or "", country_code,
           scan_id, device_key, points, reason_code, now_str(), created_by]
    sheets.append_row(SHEET_POINT_TRANSACTIONS, row)
    leaderboard_cache.clear()
    _log(sheets, "point_awarded", "employee", employee_id,
         f"+{points} ball ({reason_code}) scan={scan_id}")
    logger.info("Point awarded: %s +%d [%s]", employee_id, points, reason_code)
    return tx_id


def manual_adjust(employee_id, employee_code, points_delta, reason_code, admin_id,
                  event_id="", country_code=""):
    sheets = get_sheets()
    seq = sheets.get_next_seq(SHEET_POINT_TRANSACTIONS)
    tx_id = generate_point_tx_id(seq)
    row = [tx_id, employee_id, employee_code, event_id or "", country_code or "",
           "", "", points_delta, reason_code, now_str(), admin_id]
    sheets.append_row(SHEET_POINT_TRANSACTIONS, row)
    leaderboard_cache.clear()
    _log(sheets, "manual_point", "employee", employee_id,
         f"{points_delta:+d} ball ({reason_code}) by admin={admin_id}")
    logger.info("Manual point: %s %+d by %s", employee_id, points_delta, admin_id)
    return tx_id


def get_employee_total_points(employee_id):
    sheets = get_sheets()
    txs = sheets.find_records(SHEET_POINT_TRANSACTIONS, "employee_id", employee_id)
    return sum(int(t.get("points_delta", 0)) for t in txs)


def get_employee_event_points(employee_id, event_id):
    sheets = get_sheets()
    txs = sheets.get_all_records(SHEET_POINT_TRANSACTIONS)
    return sum(int(t.get("points_delta", 0)) for t in txs
               if t.get("employee_id") == employee_id and t.get("event_id") == event_id)


def _log(sheets, action, entity_type, entity_id, message, level="INFO"):
    seq = sheets.get_next_seq(SHEET_SYSTEM_LOGS)
    sheets.append_row(SHEET_SYSTEM_LOGS, [
        generate_log_id(seq), now_str(), level, action, entity_type, entity_id, message
    ])
