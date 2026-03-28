"""
Leaderboard service.
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


def _calc_employee_points(employee_id: str, txs: list[dict], event_id: str = None) -> int:
    total = 0
    for t in txs:
        if t.get("employee_id") != employee_id:
            continue
        if event_id and t.get("event_id") != event_id:
            continue
        total += int(t.get("points_delta", 0) or 0)
    return total


def _get_first_awarded_at(employee_id: str, txs: list[dict], event_id: str = None) -> str:
    relevant = [
        t
        for t in txs
        if t.get("employee_id") == employee_id
        and t.get("reason_code") == "first_unique_device"
        and (not event_id or t.get("event_id") == event_id)
    ]
    if not relevant:
        return "9999"
    return min(t.get("created_at", "9999") for t in relevant)


def _filter_period(all_txs: list[dict], period: str) -> list[dict]:
    period_filter = ""
    if period == "today":
        period_filter = start_of_day_utc().strftime("%Y-%m-%d")
    elif period == "week":
        period_filter = start_of_week_utc().strftime("%Y-%m-%d")
    elif period == "month":
        period_filter = start_of_month_utc().strftime("%Y-%m-%d")

    if not period_filter:
        return all_txs
    return [t for t in all_txs if t.get("created_at", "") >= period_filter]


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
