from datetime import datetime, timezone, timedelta
from app.config import settings
import pytz


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_str() -> str:
    return now_utc().strftime("%Y-%m-%d %H:%M:%S")


def to_local(dt: datetime) -> datetime:
    tz = pytz.timezone(settings.DEFAULT_TIMEZONE)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


def start_of_day_utc() -> datetime:
    now = now_utc()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def start_of_week_utc() -> datetime:
    now = now_utc()
    start = now - timedelta(days=now.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0)


def start_of_month_utc() -> datetime:
    now = now_utc()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
