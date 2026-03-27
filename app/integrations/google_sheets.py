"""
Google Sheets integration layer.
All sheet operations go through this module.
"""
import asyncio
import logging
from typing import Any, Optional
from functools import wraps

import gspread
from google.oauth2.service_account import Credentials
from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Sheet names
SHEET_META = "meta"
SHEET_DICT = "dictionaries"
SHEET_COUNTRIES = "countries"
SHEET_ADMINS = "admins"
SHEET_EMPLOYEES = "employees"
SHEET_EVENTS = "events"
SHEET_EVENT_COUNTRIES = "event_countries"
SHEET_EVENT_REWARDS = "event_rewards"
SHEET_EVENT_PARTICIPANTS = "event_participants"
SHEET_QR_CODES = "qr_codes"
SHEET_SCANS_RAW = "scans_raw"
SHEET_DEVICE_REGISTRY = "device_registry"
SHEET_POINT_TRANSACTIONS = "point_transactions"
SHEET_SYSTEM_LOGS = "system_logs"

ALL_SHEETS = [
    SHEET_META, SHEET_DICT, SHEET_COUNTRIES, SHEET_ADMINS,
    SHEET_EMPLOYEES, SHEET_EVENTS, SHEET_EVENT_COUNTRIES,
    SHEET_EVENT_REWARDS, SHEET_EVENT_PARTICIPANTS, SHEET_QR_CODES,
    SHEET_SCANS_RAW, SHEET_DEVICE_REGISTRY, SHEET_POINT_TRANSACTIONS,
    SHEET_SYSTEM_LOGS,
]

SHEET_HEADERS = {
    SHEET_META: ["key", "value", "updated_at"],
    SHEET_DICT: ["dict_type", "code", "label", "sort_order", "is_active"],
    SHEET_COUNTRIES: [
        "country_code", "country_name", "instagram_username",
        "instagram_app_link", "instagram_web_link", "is_active",
        "created_at", "updated_at"
    ],
    SHEET_ADMINS: [
        "admin_id", "telegram_user_id", "full_name", "phone",
        "role_code", "status", "created_at", "created_by"
    ],
    SHEET_EMPLOYEES: [
        "employee_id", "employee_code", "full_name", "phone",
        "telegram_user_id", "telegram_username", "country_code",
        "language_code", "status", "registered_at", "last_active_at",
        "qr_id", "short_link", "notes"
    ],
    SHEET_EVENTS: [
        "event_id", "event_code", "event_name", "description",
        "status", "start_at", "end_at", "rules_text",
        "created_by_admin_id", "created_at", "started_at", "finished_at"
    ],
    SHEET_EVENT_COUNTRIES: ["id", "event_id", "country_code", "created_at"],
    SHEET_EVENT_REWARDS: [
        "reward_id", "event_id", "place_number", "reward_title",
        "reward_amount", "currency_code", "created_at"
    ],
    SHEET_EVENT_PARTICIPANTS: [
        "participant_id", "event_id", "employee_id", "country_code",
        "participant_status", "responded_at", "notes"
    ],
    SHEET_QR_CODES: [
        "qr_id", "qr_code_value", "employee_id", "employee_code",
        "event_id", "country_code", "short_link", "qr_image_url",
        "is_active", "created_at"
    ],
    SHEET_SCANS_RAW: [
        "scan_id", "scanned_at", "employee_id", "employee_code",
        "event_id", "country_code", "qr_id", "device_key",
        "fingerprint_id", "ip_address", "forwarded_ip", "user_agent",
        "device_type", "os_name", "browser_name", "platform",
        "screen_width", "screen_height", "viewport_width", "viewport_height",
        "timezone", "accept_language", "referer", "request_path",
        "query_string", "instagram_target", "deep_link_attempted",
        "fallback_used", "scan_status", "point_decision",
        "point_transaction_id", "created_at"
    ],
    SHEET_DEVICE_REGISTRY: [
        "device_key", "fingerprint_id", "first_scan_id", "first_employee_id",
        "first_event_id", "first_country_code", "first_ip_address",
        "first_seen_at", "last_seen_at", "total_scans",
        "point_already_given", "device_status", "notes"
    ],
    SHEET_POINT_TRANSACTIONS: [
        "point_tx_id", "employee_id", "employee_code", "event_id",
        "country_code", "scan_id", "device_key", "points_delta",
        "reason_code", "created_at", "created_by"
    ],
    SHEET_SYSTEM_LOGS: [
        "log_id", "logged_at", "level", "action",
        "entity_type", "entity_id", "message"
    ],
}


class SheetsClient:
    _instance: Optional["SheetsClient"] = None
    _spreadsheet: Optional[gspread.Spreadsheet] = None
    _gc: Optional[gspread.Client] = None

    def __init__(self):
        self._sheet_cache: dict[str, gspread.Worksheet] = {}

    @classmethod
    def get_instance(cls) -> "SheetsClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _connect(self):
        if self._gc is None:
            creds_data = settings.get_google_credentials()
            creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
            self._gc = gspread.authorize(creds)
            logger.info("Google Sheets connected")

    def _get_spreadsheet(self) -> gspread.Spreadsheet:
        self._connect()
        if self._spreadsheet is None:
            import os
            spreadsheet_id = os.getenv("SPREADSHEET_ID")
            if spreadsheet_id:
                self._spreadsheet = self._gc.open_by_key(spreadsheet_id)
                logger.info(f"Opened spreadsheet by ID: {spreadsheet_id}")
            else:
                try:
                    self._spreadsheet = self._gc.open(settings.SPREADSHEET_NAME)
                    logger.info(f"Opened spreadsheet: {settings.SPREADSHEET_NAME}")
                except gspread.SpreadsheetNotFound:
                    self._spreadsheet = self._gc.create(settings.SPREADSHEET_NAME)
                    logger.info(f"Created spreadsheet: {settings.SPREADSHEET_NAME}")
        return self._spreadsheet

    def get_sheet(self, name: str) -> gspread.Worksheet:
        if name not in self._sheet_cache:
            ss = self._get_spreadsheet()
            try:
                ws = ss.worksheet(name)
            except gspread.WorksheetNotFound:
                ws = ss.add_worksheet(title=name, rows=1000, cols=50)
                logger.info(f"Created worksheet: {name}")
            self._sheet_cache[name] = ws
        return self._sheet_cache[name]

    def invalidate_cache(self, name: str = None):
        if name:
            self._sheet_cache.pop(name, None)
        else:
            self._sheet_cache.clear()

    # ── Generic CRUD ──────────────────────────────────────────────────────────

    def get_all_records(self, sheet_name: str) -> list[dict]:
        ws = self.get_sheet(sheet_name)
        try:
            return ws.get_all_records()
        except Exception as e:
            logger.error(f"get_all_records({sheet_name}): {e}")
            return []

    def append_row(self, sheet_name: str, row: list) -> None:
        ws = self.get_sheet(sheet_name)
        ws.append_row(row, value_input_option="USER_ENTERED")

    def find_row_index(self, sheet_name: str, col_name: str, value: str) -> Optional[int]:
        """Returns 1-based row index (including header), or None."""
        ws = self.get_sheet(sheet_name)
        headers = ws.row_values(1)
        if col_name not in headers:
            return None
        col_idx = headers.index(col_name) + 1
        try:
            cell = ws.find(value, in_column=col_idx)
            return cell.row if cell else None
        except Exception:
            return None

    def update_row(self, sheet_name: str, row_idx: int, data: dict) -> None:
        """Update specific cells in a row by column name."""
        ws = self.get_sheet(sheet_name)
        headers = ws.row_values(1)
        for col_name, val in data.items():
            if col_name in headers:
                col_idx = headers.index(col_name) + 1
                ws.update_cell(row_idx, col_idx, val)

    def find_record(self, sheet_name: str, col_name: str, value: str) -> Optional[dict]:
        records = self.get_all_records(sheet_name)
        for r in records:
            if str(r.get(col_name, "")) == str(value):
                return r
        return None

    def find_records(self, sheet_name: str, col_name: str, value: str) -> list[dict]:
        records = self.get_all_records(sheet_name)
        return [r for r in records if str(r.get(col_name, "")) == str(value)]

    def count_records(self, sheet_name: str) -> int:
        records = self.get_all_records(sheet_name)
        return len(records)

    def get_next_seq(self, sheet_name: str) -> int:
        """Return next sequence number (count + 1)."""
        return self.count_records(sheet_name) + 1


# Singleton accessor
def get_sheets() -> SheetsClient:
    return SheetsClient.get_instance()