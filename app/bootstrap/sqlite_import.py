"""One-time import from Google Sheets into local SQLite DB."""
import logging
import sqlite3
from google.oauth2.service_account import Credentials
import gspread

from app.config import settings
from app.integrations.google_sheets import ALL_SHEETS, SHEET_HEADERS, get_sheets

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _open_google_spreadsheet():
    creds_data = settings.get_google_credentials()
    creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
    gc = gspread.authorize(creds)
    if settings.SPREADSHEET_ID:
        return gc.open_by_key(settings.SPREADSHEET_ID)
    return gc.open(settings.SPREADSHEET_NAME)


def import_all_from_google_sheets():
    logger.info("Starting one-time import from Google Sheets to SQLite...")
    ss = _open_google_spreadsheet()
    sqlite_client = get_sheets()

    for sheet_name in ALL_SHEETS:
        headers = SHEET_HEADERS[sheet_name]
        try:
            ws = ss.worksheet(sheet_name)
            values = ws.get_all_values()
        except Exception as e:
            logger.warning("Skip %s: %s", sheet_name, e)
            continue

        if not values:
            sqlite_client.replace_records(sheet_name, [])
            logger.info("Imported %s: 0 rows", sheet_name)
            continue

        source_headers = values[0]
        data_rows = values[1:] if len(values) > 1 else []
        records = []
        for raw in data_rows:
            if not any(str(cell).strip() for cell in raw):
                continue
            row_map = {source_headers[i]: raw[i] if i < len(raw) else "" for i in range(len(source_headers))}
            record = {h: row_map.get(h, "") for h in headers}
            records.append(record)

        sqlite_client.replace_records(sheet_name, records)
        logger.info("Imported %s: %s rows", sheet_name, len(records))

    logger.info("Google Sheets -> SQLite import finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    import_all_from_google_sheets()
