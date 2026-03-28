"""
Google Sheets integration layer.
All sheet operations go through this module.
Includes retry logic and cache-aware helpers.
"""
import asyncio
import logging
import time
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
        "created_by_admin_id", "created_at", "started_at", "finished_at",
        "reward_pool_amount", "reward_pool_currency"
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


def _retry(max_attempts=3, backoff=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except gspread.exceptions.APIError as e:
                    last_err = e
                    code = e.response.status_code if hasattr(e, "response") else 0
                    if code in (429, 500, 503) and attempt < max_attempts:
                        wait = backoff * (2 ** (attempt - 1))
                        logger.warning("Sheets API %s attempt %d/%d, retry in %.1fs", code, attempt, max_attempts, wait)
                        time.sleep(wait)
                    else:
                        raise
                except Exception as e:
                    last_err = e
                    if attempt < max_attempts:
                        time.sleep(backoff)
                    else:
                        raise
            raise last_err
        return wrapper
    return decorator


class SheetsClient:
    _instance = None
    _spreadsheet = None
    _gc = None

    def __init__(self):
        self._sheet_cache = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _connect(self):
        if self._gc is None:
            creds_data = settings.get_google_credentials()
            creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
            self._gc = gspread.authorize(creds)
            logger.info("Google Sheets connected")

    def _get_spreadsheet(self):
        self._connect()
        if self._spreadsheet is None:
            sid = settings.SPREADSHEET_ID
            if sid:
                self._spreadsheet = self._gc.open_by_key(sid)
                logger.info("Opened spreadsheet by ID: %s", sid)
            else:
                try:
                    self._spreadsheet = self._gc.open(settings.SPREADSHEET_NAME)
                    logger.info("Opened spreadsheet: %s", settings.SPREADSHEET_NAME)
                except gspread.SpreadsheetNotFound:
                    self._spreadsheet = self._gc.create(settings.SPREADSHEET_NAME)
                    logger.info("Created spreadsheet: %s", settings.SPREADSHEET_NAME)
                    self._share_spreadsheet()
        return self._spreadsheet

    def _share_spreadsheet(self):
        for email in settings.get_share_emails():
            try:
                self._spreadsheet.share(email, perm_type="user", role="writer")
                logger.info("Shared spreadsheet with: %s", email)
            except Exception as e:
                logger.warning("Failed to share with %s: %s", email, e)

    def get_sheet(self, name):
        if name not in self._sheet_cache:
            ss = self._get_spreadsheet()
            try:
                ws = ss.worksheet(name)
            except gspread.WorksheetNotFound:
                ws = ss.add_worksheet(title=name, rows=1000, cols=50)
                logger.info("Created worksheet: %s", name)
            self._sheet_cache[name] = ws
        return self._sheet_cache[name]

    def invalidate_cache(self, name=None):
        if name:
            self._sheet_cache.pop(name, None)
        else:
            self._sheet_cache.clear()

    @_retry(max_attempts=3, backoff=1.0)
    def get_all_records(self, sheet_name):
        ws = self.get_sheet(sheet_name)
        try:
            return ws.get_all_records()
        except Exception as e:
            logger.error("get_all_records(%s): %s", sheet_name, e)
            return []

    @_retry(max_attempts=3, backoff=1.0)
    def append_row(self, sheet_name, row):
        ws = self.get_sheet(sheet_name)
        ws.append_row(row, value_input_option="USER_ENTERED")

    @_retry(max_attempts=3, backoff=1.0)
    def find_row_index(self, sheet_name, col_name, value):
        ws = self.get_sheet(sheet_name)
        headers = ws.row_values(1)
        if col_name not in headers:
            return None
        col_idx = headers.index(col_name) + 1
        try:
            cell = ws.find(str(value), in_column=col_idx)
            return cell.row if cell else None
        except Exception:
            return None

    @_retry(max_attempts=3, backoff=1.0)
    def update_row(self, sheet_name, row_idx, data):
        ws = self.get_sheet(sheet_name)
        headers = ws.row_values(1)
        for col_name, val in data.items():
            if col_name in headers:
                col_idx = headers.index(col_name) + 1
                ws.update_cell(row_idx, col_idx, val)

    def find_record(self, sheet_name, col_name, value):
        records = self.get_all_records(sheet_name)
        for r in records:
            if str(r.get(col_name, "")) == str(value):
                return r
        return None

    def find_records(self, sheet_name, col_name, value):
        records = self.get_all_records(sheet_name)
        return [r for r in records if str(r.get(col_name, "")) == str(value)]

    def count_records(self, sheet_name):
        return len(self.get_all_records(sheet_name))

    def get_next_seq(self, sheet_name):
        return self.count_records(sheet_name) + 1

    def set_filter(self, sheet_name):
        try:
            ws = self.get_sheet(sheet_name)
            ws.set_basic_filter()
            logger.info("Filter set: %s", sheet_name)
        except Exception as e:
            logger.debug("Filter skip for %s: %s", sheet_name, e)


async def async_get_all_records(sheet_name):
    return await asyncio.to_thread(get_sheets().get_all_records, sheet_name)

async def async_append_row(sheet_name, row):
    await asyncio.to_thread(get_sheets().append_row, sheet_name, row)

async def async_find_record(sheet_name, col_name, value):
    return await asyncio.to_thread(get_sheets().find_record, sheet_name, col_name, value)

async def async_update_row(sheet_name, row_idx, data):
    await asyncio.to_thread(get_sheets().update_row, sheet_name, row_idx, data)


def get_sheets():
    return SheetsClient.get_instance()
