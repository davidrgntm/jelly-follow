"""
Leaderboard service.
Event leaderboard counts only points earned after the event start time.
"""
from app.integrations.google_sheets import (
    get_sheets,
    SHEET_EMPLOYEES,
    SHEET_POINT_TRANSACTIONS,
    SHEET_EVENT_PARTICIPANTS,
)
from app.utils.datetime_utils import (
    start_of_day_utc,
    start_of_week_utc,
    start_of_month_utc,
)
from app.services.events_service import get_event_by_id


def _norm_ts(ts: str) -> str:
    ts = (ts or "").strip()
    if len(ts) == 16:
        return ts + ":00"
    return ts


def _event_start_ts(event_id: str) -> str:
    event = get_event_by_id(event_id)
    if not event:
        return ""
    return _norm_ts(event.get("started_at") or event.get("start_at") or "")


def _calc_employee_points(employee_id: str, txs: list[dict], event_id: str = None) -> int:
    total = 0
    event_start = _event_start_ts(event_id) if event_id else ""
    for t in txs:
        if t.get("employee_id") != employee_id:
            continue
        if event_id and t.get("event_id") != event_id:
            continue
        if event_start and _norm_ts(t.get("created_at", "")) < event_start:
            continue
        total += int(t.get("points_delta", 0) or 0)
    return total


def _get_first_awarded_at(employee_id: str, txs: list[dict], event_id: str = None) -> str:
    event_start = _event_start_ts(event_id) if event_id else ""
    relevant = []
    for t in txs:
        if t.get("employee_id") != employee_id:
            continue
        if t.get("reason_code") != "first_unique_device":
            continue
        if event_id and t.get("event_id") != event_id:
            continue
        created_at = _norm_ts(t.get("created_at", "9999"))
        if event_start and created_at < event_start:
            continue
        relevant.append(created_at)
    if not relevant:
        return "9999"
    return min(relevant)


def _filter_period(all_txs: list[dict], period: str) -> list[dict]:
    period_filter = ""
    if period == "today":
        period_filter = start_of_day_utc().strftime("%Y-%m-%d")
    elif period == "week":
        period_filter = start_of_week_utc().strftime("%Y-%m-%d")
    elif period == "month":
        period_filter = start_of_month_utc().strftime("%Y-%m-%d %H:%M:%S")

    if not period_filter:
        return all_txs
    return [t for t in all_txs if _norm_ts(t.get("created_at", "")) >= period_filter]


def build_leaderboard(
    country_code: str = None,
    event_id: str = None,
    period: str = "all",
    top_n: int = 50,
) -> list[dict]:
    sheets = get_sheets()
    employees = sheets.get_all_records(SHEET_EMPLOYEES)
    all_txs = _filter_period(sheets.get_all_records(SHEET_POINT_TRANSACTIONS), period)

    if country_code:
        employees = [
            e for e in employees if e.get("country_code", "").upper() == country_code.upper()
        ]

    employees = [e for e in employees if e.get("status") == "active"]

    if event_id:
        participants = sheets.find_records(SHEET_EVENT_PARTICIPANTS, "event_id", event_id)
        accepted_ids = {
            p.get("employee_id")
            for p in participants
            if p.get("participant_status") in {"accepted", "pending", ""}
        }
        point_ids = {t.get("employee_id") for t in all_txs if t.get("event_id") == event_id}
        scope_ids = accepted_ids | point_ids
        if scope_ids:
            employees = [e for e in employees if e.get("employee_id") in scope_ids]

    results = []
    for emp in employees:
        eid = emp.get("employee_id")
        points = _calc_employee_points(eid, all_txs, event_id)
        first_at = _get_first_awarded_at(eid, all_txs, event_id)
        results.append(
            {
                "employee_id": eid,
                "employee_code": emp.get("employee_code"),
                "full_name": emp.get("full_name"),
                "country_code": emp.get("country_code"),
                "points": points,
                "_first_at": first_at,
            }
        )

    results.sort(key=lambda x: (-x["points"], x["_first_at"], x["employee_code"] or ""))

    for i, r in enumerate(results[:top_n], 1):
        r["rank"] = i
        del r["_first_at"]

    return results[:top_n]


def get_employee_rank(
    employee_id: str,
    country_code: str = None,
    event_id: str = None,
    period: str = "all",
) -> int:
    lb = build_leaderboard(
        country_code=country_code,
        event_id=event_id,
        period=period,
        top_n=100000,
    )
    for entry in lb:
        if entry["employee_id"] == employee_id:
            return entry["rank"]
    return -1
