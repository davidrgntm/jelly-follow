"""
SQLite-backed data layer that preserves the old Google Sheets API.
This lets the rest of the project keep working without major rewrites.
"""
import asyncio
import logging
import os
import sqlite3
import threading
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

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
SHEET_EVENT_BONUS_RULES = "event_bonus_rules"
SHEET_EVENT_BONUS_SUBMISSIONS = "event_bonus_submissions"
SHEET_SYSTEM_LOGS = "system_logs"

ALL_SHEETS = [
    SHEET_META, SHEET_DICT, SHEET_COUNTRIES, SHEET_ADMINS,
    SHEET_EMPLOYEES, SHEET_EVENTS, SHEET_EVENT_COUNTRIES,
    SHEET_EVENT_REWARDS, SHEET_EVENT_PARTICIPANTS, SHEET_QR_CODES,
    SHEET_SCANS_RAW, SHEET_DEVICE_REGISTRY, SHEET_POINT_TRANSACTIONS,
    SHEET_EVENT_BONUS_RULES, SHEET_EVENT_BONUS_SUBMISSIONS,
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
    SHEET_EVENT_BONUS_RULES: [
        "bonus_rule_id", "event_id", "title", "description", "task_type",
        "points", "max_per_employee", "requires_moderation", "min_followers",
        "is_active", "sort_order", "created_at", "created_by"
    ],
    SHEET_EVENT_BONUS_SUBMISSIONS: [
        "submission_id", "event_id", "bonus_rule_id", "employee_id", "employee_code",
        "country_code", "status", "evidence_url", "notes", "points_awarded",
        "point_tx_id", "created_at", "reviewed_at", "reviewed_by"
    ],
    SHEET_SYSTEM_LOGS: [
        "log_id", "logged_at", "level", "action",
        "entity_type", "entity_id", "message"
    ],
}


def _quote(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _resolve_sqlite_path() -> str:
    raw = str(getattr(settings, "SQLITE_PATH", "data/jelly_follow.db") or "data/jelly_follow.db").strip()
    raw = raw.strip('"').strip("'")

    if os.path.isabs(raw):
        return raw

    if os.path.isdir("/data"):
        return os.path.join("/data", os.path.basename(raw))

    return raw


class SQLiteWorksheet:
    def __init__(self, client: "SheetsClient", name: str):
        self.client = client
        self.name = name

    def row_values(self, row_index: int):
        if row_index == 1:
            return list(self.client.get_headers(self.name))
        record = self.client.get_record_by_row_index(self.name, row_index)
        if not record:
            return []
        return [record.get(h, "") for h in self.client.get_headers(self.name)]

    def insert_row(self, row, index=1):
        headers = self.client.get_headers(self.name)
        if index == 1 and row:
            self.client.ensure_headers(self.name, [str(x) for x in row])
            return
        self.client.append_row(self.name, row)

    def freeze(self, rows=1):
        return None

    def update_cell(self, row_idx: int, col_idx: int, value: Any):
        headers = self.client.get_headers(self.name)
        if col_idx < 1:
            return
        while col_idx > len(headers):
            self.client.add_column(self.name, f"col_{len(headers)+1}")
            headers = self.client.get_headers(self.name)
        col_name = headers[col_idx - 1]
        if row_idx == 1:
            self.client.rename_or_add_header(self.name, col_idx, str(value))
            return
        self.client.update_row(self.name, row_idx, {col_name: value})

    def get_all_records(self):
        return self.client.get_all_records(self.name)

    def get_all_values(self):
        headers = self.client.get_headers(self.name)
        values = [headers]
        for record in self.client.get_all_records(self.name):
            values.append([record.get(h, "") for h in headers])
        return values

    def append_row(self, row, value_input_option="USER_ENTERED"):
        self.client.append_row(self.name, row)

    def clear(self):
        self.client.clear_table(self.name)

    def update(self, rows, value_input_option="USER_ENTERED"):
        self.client.update_rows_from_matrix(self.name, rows)

    def set_basic_filter(self):
        return None

    def find(self, value, in_column: Optional[int] = None):
        return self.client.find_cell(self.name, value, in_column=in_column)


class _FoundCell:
    def __init__(self, row: int):
        self.row = row


class SheetsClient:
    _instance = None
    _init_lock = threading.Lock()

    def __init__(self):
        raw_db_path = str(getattr(settings, "SQLITE_PATH", "data/jelly_follow.db") or "data/jelly_follow.db")
        self.db_path = _resolve_sqlite_path()
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        logger.info("SQLite path resolved: raw=%s effective=%s", raw_db_path, self.db_path)

        self._local = threading.local()
        self._sheet_cache = {}
        self._ensure_schema()

    @classmethod
    def get_instance(cls):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def _conn(self):
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=settings.SQLITE_TIMEOUT, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA foreign_keys=OFF")
            self._local.conn = conn
        return conn

    def _ensure_schema(self):
        conn = sqlite3.connect(self.db_path, timeout=settings.SQLITE_TIMEOUT, check_same_thread=False)
        try:
            for table, headers in SHEET_HEADERS.items():
                cols = ", ".join([f'{_quote(h)} TEXT' for h in headers])
                conn.execute(f'CREATE TABLE IF NOT EXISTS {_quote(table)} (_rowid INTEGER PRIMARY KEY AUTOINCREMENT, {cols})')
            self._ensure_indexes(conn)
            conn.commit()
        finally:
            conn.close()
        logger.info("SQLite connected: %s", self.db_path)

    def _ensure_indexes(self, conn):
        indexes = {
            SHEET_EMPLOYEES: ["employee_id", "employee_code", "telegram_user_id", "country_code"],
            SHEET_ADMINS: ["admin_id", "telegram_user_id"],
            SHEET_EVENTS: ["event_id", "event_code", "status"],
            SHEET_EVENT_COUNTRIES: ["event_id", "country_code"],
            SHEET_EVENT_PARTICIPANTS: ["participant_id", "event_id", "employee_id", "country_code", "participant_status"],
            SHEET_QR_CODES: ["qr_id", "employee_id", "employee_code", "event_id", "country_code", "is_active"],
            SHEET_SCANS_RAW: ["scan_id", "employee_id", "employee_code", "event_id", "country_code", "qr_id", "device_key", "fingerprint_id", "point_decision", "scan_status"],
            SHEET_DEVICE_REGISTRY: ["device_key", "fingerprint_id", "first_employee_id", "first_event_id", "first_country_code"],
            SHEET_POINT_TRANSACTIONS: ["point_tx_id", "employee_id", "employee_code", "event_id", "country_code", "scan_id", "device_key", "reason_code"],
            SHEET_EVENT_BONUS_RULES: ["bonus_rule_id", "event_id", "task_type", "is_active"],
            SHEET_EVENT_BONUS_SUBMISSIONS: ["submission_id", "event_id", "bonus_rule_id", "employee_id", "status", "point_tx_id"],
            SHEET_SYSTEM_LOGS: ["log_id", "entity_type", "entity_id", "action", "level"],
            SHEET_COUNTRIES: ["country_code", "is_active"],
            SHEET_DICT: ["dict_type", "code", "is_active"],
            SHEET_META: ["key"],
        }
        for table, cols in indexes.items():
            for col in cols:
                if col in SHEET_HEADERS.get(table, []):
                    idx_name = f"idx_{table}_{col}"
                    conn.execute(f'CREATE INDEX IF NOT EXISTS {_quote(idx_name)} ON {_quote(table)} ({_quote(col)})')

    def get_headers(self, table):
        conn = self._conn()
        rows = conn.execute(f'PRAGMA table_info({_quote(table)})').fetchall()
        headers = [r[1] for r in rows if r[1] != '_rowid']
        if not headers and table in SHEET_HEADERS:
            self.ensure_headers(table, SHEET_HEADERS[table])
            return list(SHEET_HEADERS[table])
        return headers

    def ensure_headers(self, table, headers):
        existing = set(self.get_headers(table))
        for header in headers:
            if header not in existing:
                self.add_column(table, header)
        return self.get_headers(table)

    def add_column(self, table, col_name):
        conn = self._conn()
        headers = set(self.get_headers(table))
        if col_name in headers:
            return
        conn.execute(f'ALTER TABLE {_quote(table)} ADD COLUMN {_quote(col_name)} TEXT')
        conn.commit()

    def rename_or_add_header(self, table, col_idx, new_name):
        headers = self.get_headers(table)
        if 1 <= col_idx <= len(headers):
            old_name = headers[col_idx - 1]
            if old_name == new_name:
                return
            conn = self._conn()
            try:
                conn.execute(f'ALTER TABLE {_quote(table)} RENAME COLUMN {_quote(old_name)} TO {_quote(new_name)}')
                conn.commit()
            except Exception:
                self.add_column(table, new_name)
        else:
            self.add_column(table, new_name)

    def get_sheet(self, name):
        if name not in self._sheet_cache:
            self.ensure_headers(name, SHEET_HEADERS.get(name, []))
            self._sheet_cache[name] = SQLiteWorksheet(self, name)
        return self._sheet_cache[name]

    def invalidate_cache(self, name=None):
        if name:
            self._sheet_cache.pop(name, None)
        else:
            self._sheet_cache.clear()

    def clear_table(self, table):
        conn = self._conn()
        conn.execute(f'DELETE FROM {_quote(table)}')
        conn.commit()

    def update_rows_from_matrix(self, table, rows):
        headers = rows[0] if rows else self.get_headers(table)
        self.ensure_headers(table, headers)
        self.clear_table(table)
        for row in rows[1:]:
            if not any(str(cell).strip() for cell in row):
                continue
            self.append_row(table, row)

    def get_all_records(self, sheet_name):
        headers = self.get_headers(sheet_name)
        if not headers:
            return []
        conn = self._conn()
        query = f'SELECT {", ".join(_quote(h) for h in headers)} FROM {_quote(sheet_name)} ORDER BY _rowid ASC'
        rows = conn.execute(query).fetchall()
        return [{h: ("" if row[h] is None else str(row[h])) for h in headers} for row in rows]

    def append_row(self, sheet_name, row):
        headers = self.get_headers(sheet_name)
        if not headers:
            self.ensure_headers(sheet_name, SHEET_HEADERS.get(sheet_name, []))
            headers = self.get_headers(sheet_name)
        values = list(row)
        if len(values) < len(headers):
            values += [""] * (len(headers) - len(values))
        payload = {headers[i]: values[i] if i < len(values) else "" for i in range(len(headers))}
        conn = self._conn()
        cols_sql = ", ".join(_quote(h) for h in headers)
        placeholders = ", ".join(["?"] * len(headers))
        conn.execute(f'INSERT INTO {_quote(sheet_name)} ({cols_sql}) VALUES ({placeholders})', [payload[h] for h in headers])
        conn.commit()

    def replace_records(self, sheet_name, records):
        self.clear_table(sheet_name)
        headers = self.get_headers(sheet_name)
        for record in records:
            row = [record.get(h, "") for h in headers]
            self.append_row(sheet_name, row)

    def get_record_by_row_index(self, sheet_name, row_idx):
        if row_idx <= 1:
            return None
        headers = self.get_headers(sheet_name)
        offset = row_idx - 2
        conn = self._conn()
        row = conn.execute(
            f'SELECT _rowid, {", ".join(_quote(h) for h in headers)} FROM {_quote(sheet_name)} ORDER BY _rowid ASC LIMIT 1 OFFSET ?',
            (offset,),
        ).fetchone()
        if not row:
            return None
        return {h: ("" if row[h] is None else str(row[h])) for h in headers}

    def find_row_index(self, sheet_name, col_name, value):
        if col_name not in self.get_headers(sheet_name):
            return None
        conn = self._conn()
        rows = conn.execute(
            f'SELECT _rowid FROM {_quote(sheet_name)} WHERE COALESCE({_quote(col_name)}, "") = ? ORDER BY _rowid ASC LIMIT 1',
            (str(value),),
        ).fetchall()
        if not rows:
            return None
        target_rowid = rows[0][0]
        ordinal = conn.execute(
            f'SELECT COUNT(*) FROM {_quote(sheet_name)} WHERE _rowid <= ?', (target_rowid,)
        ).fetchone()[0]
        return ordinal + 1

    def update_row(self, sheet_name, row_idx, data):
        if row_idx <= 1 or not data:
            return
        headers = self.get_headers(sheet_name)
        offset = row_idx - 2
        conn = self._conn()
        row = conn.execute(
            f'SELECT _rowid FROM {_quote(sheet_name)} ORDER BY _rowid ASC LIMIT 1 OFFSET ?', (offset,)
        ).fetchone()
        if not row:
            return
        actual_rowid = row[0]
        valid_items = [(k, data[k]) for k in data.keys() if k in headers]
        if not valid_items:
            return
        set_sql = ", ".join([f'{_quote(k)} = ?' for k, _ in valid_items])
        params = [v for _, v in valid_items] + [actual_rowid]
        conn.execute(f'UPDATE {_quote(sheet_name)} SET {set_sql} WHERE _rowid = ?', params)
        conn.commit()

    def find_record(self, sheet_name, col_name, value):
        records = self.find_records(sheet_name, col_name, value, limit=1)
        return records[0] if records else None

    def find_records(self, sheet_name, col_name, value, limit: Optional[int] = None):
        headers = self.get_headers(sheet_name)
        if col_name not in headers:
            return []
        conn = self._conn()
        limit_sql = f' LIMIT {int(limit)}' if limit else ''
        query = f'SELECT {", ".join(_quote(h) for h in headers)} FROM {_quote(sheet_name)} WHERE COALESCE({_quote(col_name)}, "") = ? ORDER BY _rowid ASC{limit_sql}'
        rows = conn.execute(query, (str(value),)).fetchall()
        return [{h: ("" if row[h] is None else str(row[h])) for h in headers} for row in rows]

    def count_records(self, sheet_name):
        conn = self._conn()
        return conn.execute(f'SELECT COUNT(*) FROM {_quote(sheet_name)}').fetchone()[0]

    def get_next_seq(self, sheet_name):
        return self.count_records(sheet_name) + 1

    def set_filter(self, sheet_name):
        return None

    def find_cell(self, sheet_name, value, in_column: Optional[int] = None):
        headers = self.get_headers(sheet_name)
        conn = self._conn()
        if in_column and 1 <= in_column <= len(headers):
            col = headers[in_column - 1]
            row_idx = self.find_row_index(sheet_name, col, value)
            return _FoundCell(row_idx) if row_idx else None
        for col in headers:
            row_idx = self.find_row_index(sheet_name, col, value)
            if row_idx:
                return _FoundCell(row_idx)
        return None


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
