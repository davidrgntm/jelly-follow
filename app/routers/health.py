from __future__ import annotations

import os
import sqlite3
from fastapi import APIRouter

from app.config import settings
from app.integrations.google_sheets import (
    get_sheets,
    SHEET_META,
    SHEET_EMPLOYEES,
    SHEET_EVENTS,
    SHEET_SCANS_RAW,
    SHEET_POINT_TRANSACTIONS,
    SHEET_ADMINS,
)

router = APIRouter()


def _resolve_sqlite_path() -> str:
    raw = str(getattr(settings, "SQLITE_PATH", "data/jelly_follow.db") or "data/jelly_follow.db").strip()
    raw = raw.strip('"').strip("'")

    if os.path.isabs(raw):
        return raw

    if os.path.isdir("/data"):
        return os.path.join("/data", os.path.basename(raw))

    return raw


def _table_count(conn: sqlite3.Connection, table_name: str) -> int:
    try:
        row = conn.execute(f'SELECT COUNT(*) AS cnt FROM "{table_name}"').fetchone()
        return int(row[0] or 0) if row else 0
    except Exception:
        return -1


def _latest_scans(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    try:
        rows = conn.execute(
            f'''
            SELECT
                scan_id,
                scanned_at,
                employee_id,
                employee_code,
                event_id,
                country_code,
                ip_address,
                device_key,
                scan_status,
                point_decision,
                created_at
            FROM "{SHEET_SCANS_RAW}"
            ORDER BY _rowid DESC
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()

        result = []
        for row in rows:
            result.append(
                {
                    "scan_id": row["scan_id"],
                    "scanned_at": row["scanned_at"],
                    "employee_id": row["employee_id"],
                    "employee_code": row["employee_code"],
                    "event_id": row["event_id"],
                    "country_code": row["country_code"],
                    "ip_address": row["ip_address"],
                    "device_key": row["device_key"],
                    "scan_status": row["scan_status"],
                    "point_decision": row["point_decision"],
                    "created_at": row["created_at"],
                }
            )
        return result
    except Exception as e:
        return [{"error": str(e)}]


@router.get("/health")
async def health_check():
    sheets_ok = False
    backend = str(getattr(settings, "DB_BACKEND", "sqlite") or "sqlite").lower().strip()

    try:
        sheets = get_sheets()
        sheets.get_sheet(SHEET_META)
        sheets_ok = True
    except Exception:
        pass

    return {
        "ok": True,
        "service": "Jelly Follow API",
        "db_backend": backend,
        "storage_connected": sheets_ok,
    }


@router.get("/health/db")
async def health_db():
    backend = str(getattr(settings, "DB_BACKEND", "sqlite") or "sqlite").lower().strip()
    raw_path = str(getattr(settings, "SQLITE_PATH", "data/jelly_follow.db") or "data/jelly_follow.db")
    effective_path = _resolve_sqlite_path()

    db_exists = os.path.exists(effective_path)
    db_size_bytes = os.path.getsize(effective_path) if db_exists else 0
    data_dir_exists = os.path.isdir("/data")
    data_dir_writable = os.access("/data", os.W_OK) if data_dir_exists else False

    payload = {
        "ok": True,
        "service": "Jelly Follow API",
        "db_backend": backend,
        "sqlite": {
            "raw_path": raw_path,
            "effective_path": effective_path,
            "exists": db_exists,
            "size_bytes": db_size_bytes,
            "data_dir_exists": data_dir_exists,
            "data_dir_writable": data_dir_writable,
            "import_on_start": bool(getattr(settings, "SQLITE_IMPORT_ON_START", False)),
        },
    }

    if backend != "sqlite":
        payload["warning"] = "DB_BACKEND is not sqlite"
        return payload

    if not db_exists:
        payload["error"] = "SQLite file does not exist at effective_path"
        return payload

    try:
        conn = sqlite3.connect(effective_path, timeout=float(getattr(settings, "SQLITE_TIMEOUT", 30.0)))
        conn.row_factory = sqlite3.Row

        payload["counts"] = {
            "employees": _table_count(conn, SHEET_EMPLOYEES),
            "events": _table_count(conn, SHEET_EVENTS),
            "scans_raw": _table_count(conn, SHEET_SCANS_RAW),
            "point_transactions": _table_count(conn, SHEET_POINT_TRANSACTIONS),
            "admins": _table_count(conn, SHEET_ADMINS),
        }

        payload["latest_scans"] = _latest_scans(conn, limit=5)

        try:
            tables = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                ORDER BY name
                """
            ).fetchall()
            payload["tables"] = [row["name"] for row in tables]
        except Exception as e:
            payload["tables_error"] = str(e)

        conn.close()
        return payload

    except Exception as e:
        payload["error"] = str(e)
        return payload

@router.get("/health/db-files")
async def health_db_files():
    base = "/data/jelly_follow.db"
    items = {}
    for path in [base, base + "-wal", base + "-shm", "/data/jelly_follow.backup.db"]:
        items[path] = {
            "exists": os.path.exists(path),
            "size": os.path.getsize(path) if os.path.exists(path) else 0,
        }
    return {"ok": True, "files": items}
