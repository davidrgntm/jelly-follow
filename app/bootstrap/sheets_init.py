"""
Google Sheets bootstrap module.
Creates all sheets, headers, and seeds initial data on startup.
"""
import logging
from datetime import datetime, timezone

import gspread

from app.integrations.google_sheets import (
    get_sheets, ALL_SHEETS, SHEET_HEADERS,
    SHEET_META, SHEET_DICT, SHEET_COUNTRIES, SHEET_SYSTEM_LOGS,
)
from app.utils.datetime_utils import now_str
from app.utils.ids import generate_log_id
from app.config import settings

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0.0"


def run_bootstrap():
    """Entry point: called on app startup."""
    logger.info("Starting Google Sheets bootstrap...")
    sheets = get_sheets()

    _ensure_all_sheets(sheets)
    _ensure_headers(sheets)
    _seed_meta(sheets)
    _seed_dictionaries(sheets)
    _seed_countries(sheets)
    _write_system_log(sheets, "bootstrap_complete", "Bootstrap completed successfully")
    logger.info("Bootstrap complete.")


def _ensure_all_sheets(sheets):
    for name in ALL_SHEETS:
        ws = sheets.get_sheet(name)
        logger.info(f"Sheet ready: {name}")


def _ensure_headers(sheets):
    for sheet_name, headers in SHEET_HEADERS.items():
        ws = sheets.get_sheet(sheet_name)
        existing = ws.row_values(1)
        if not existing:
            ws.insert_row(headers, 1)
            ws.freeze(rows=1)
            logger.info(f"Headers set for: {sheet_name}")
        else:
            # Add missing columns (schema migration)
            for i, h in enumerate(headers):
                if h not in existing:
                    ws.update_cell(1, len(existing) + 1, h)
                    existing.append(h)
                    logger.info(f"Added missing column '{h}' to {sheet_name}")


def _seed_meta(sheets):
    ws = sheets.get_sheet(SHEET_META)
    records = ws.get_all_records()
    existing_keys = {r["key"] for r in records}

    defaults = {
        "schema_version": SCHEMA_VERSION,
        "spreadsheet_name": settings.SPREADSHEET_NAME,
        "project_name": "Jelly Follow",
        "default_timezone": settings.DEFAULT_TIMEZONE,
        "created_at": now_str(),
    }

    for key, value in defaults.items():
        if key not in existing_keys:
            ws.append_row([key, value, now_str()], value_input_option="USER_ENTERED")
            logger.info(f"Meta seed: {key}={value}")


def _seed_dictionaries(sheets):
    ws = sheets.get_sheet(SHEET_DICT)
    records = ws.get_all_records()
    existing = {(r["dict_type"], r["code"]) for r in records}

    seeds = [
        # country_code
        ("country_code", "UZ", "O'zbekiston", 1),
        ("country_code", "RU", "Rossiya", 2),
        ("country_code", "KG", "Qirg'iz Respublikasi", 3),
        ("country_code", "AZ", "Ozarbayjon", 4),
        # language_code
        ("language_code", "uz", "O'zbekcha", 1),
        ("language_code", "ru", "Русский", 2),
        ("language_code", "en", "English", 3),
        ("language_code", "kg", "Кыргызча", 4),
        ("language_code", "az", "Azərbaycanca", 5),
        # role_code
        ("role_code", "employee", "Xodim", 1),
        ("role_code", "ga", "GA", 2),
        ("role_code", "super_admin", "Super Admin", 3),
        # employee_status
        ("employee_status", "active", "Faol", 1),
        ("employee_status", "inactive", "Nofaol", 2),
        ("employee_status", "blocked", "Bloklangan", 3),
        # event_status
        ("event_status", "draft", "Qoralama", 1),
        ("event_status", "active", "Faol", 2),
        ("event_status", "paused", "To'xtatilgan", 3),
        ("event_status", "finished", "Tugagan", 4),
        # participant_status
        ("participant_status", "pending", "Kutmoqda", 1),
        ("participant_status", "accepted", "Qabul qildi", 2),
        ("participant_status", "declined", "Rad etdi", 3),
        # point_reason
        ("point_reason", "first_unique_device", "Yangi qurilma", 1),
        ("point_reason", "duplicate_device", "Takror qurilma", 2),
        ("point_reason", "manual_bonus", "Qo'lda bonus", 3),
        ("point_reason", "manual_penalty", "Qo'lda jarima", 4),
        # scan_status
        ("scan_status", "opened", "Ochildi", 1),
        ("scan_status", "redirected", "Yo'naltirildi", 2),
        ("scan_status", "failed", "Xatolik", 3),
        ("scan_status", "suspicious", "Shubhali", 4),
        # device_status
        ("device_status", "clean", "Tozа", 1),
        ("device_status", "duplicate", "Takror", 2),
        ("device_status", "blocked", "Bloklangan", 3),
        ("device_status", "suspicious", "Shubhali", 4),
    ]

    for dict_type, code, label, sort_order in seeds:
        if (dict_type, code) not in existing:
            ws.append_row(
                [dict_type, code, label, sort_order, "yes"],
                value_input_option="USER_ENTERED"
            )
            logger.info(f"Dict seed: {dict_type}/{code}")


def _seed_countries(sheets):
    ws = sheets.get_sheet(SHEET_COUNTRIES)
    records = ws.get_all_records()
    existing_codes = {r["country_code"] for r in records}

    countries = [
        {
            "country_code": "UZ",
            "country_name": "O'zbekiston",
            "instagram_username": settings.INSTAGRAM_UZ_USERNAME,
            "instagram_app_link": f"instagram://user?username={settings.INSTAGRAM_UZ_USERNAME}",
            "instagram_web_link": f"https://www.instagram.com/{settings.INSTAGRAM_UZ_USERNAME}/",
        },
        {
            "country_code": "RU",
            "country_name": "Rossiya",
            "instagram_username": settings.INSTAGRAM_RU_USERNAME,
            "instagram_app_link": f"instagram://user?username={settings.INSTAGRAM_RU_USERNAME}",
            "instagram_web_link": f"https://www.instagram.com/{settings.INSTAGRAM_RU_USERNAME}/",
        },
        {
            "country_code": "KG",
            "country_name": "Qirg'iz Respublikasi",
            "instagram_username": settings.INSTAGRAM_KG_USERNAME,
            "instagram_app_link": f"instagram://user?username={settings.INSTAGRAM_KG_USERNAME}",
            "instagram_web_link": f"https://www.instagram.com/{settings.INSTAGRAM_KG_USERNAME}/",
        },
        {
            "country_code": "AZ",
            "country_name": "Ozarbayjon",
            "instagram_username": settings.INSTAGRAM_AZ_USERNAME,
            "instagram_app_link": f"instagram://user?username={settings.INSTAGRAM_AZ_USERNAME}",
            "instagram_web_link": f"https://www.instagram.com/{settings.INSTAGRAM_AZ_USERNAME}/",
        },
    ]

    for c in countries:
        if c["country_code"] not in existing_codes:
            ws.append_row(
                [
                    c["country_code"], c["country_name"],
                    c["instagram_username"], c["instagram_app_link"],
                    c["instagram_web_link"], "yes", now_str(), now_str()
                ],
                value_input_option="USER_ENTERED"
            )
            logger.info(f"Country seed: {c['country_code']}")


def _write_system_log(sheets, action: str, message: str):
    ws = sheets.get_sheet(SHEET_SYSTEM_LOGS)
    seq = sheets.count_records(SHEET_SYSTEM_LOGS) + 1
    ws.append_row(
        [generate_log_id(seq), now_str(), "INFO", action, "system", "", message],
        value_input_option="USER_ENTERED"
    )
