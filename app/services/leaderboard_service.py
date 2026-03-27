"""
Leaderboard service.
"""
from app.integrations.google_sheets import (
    get_sheets, SHEET_EMPLOYEES, SHEET_POINT_TRANSACTIONS,
)
from app.utils.datetime_utils import (
    start_of_day_utc, start_of_week_utc, start_of_month_utc,
)


def _calc_employee_points(employee_id: str, txs: list[dict], event_id: str = None) -> int:
    total = 0
    for t in txs:
        if t.get("employee_id") != employee_id:
            continue
        if event_id and t.get("event_id") != event_id:
            continue
        total += int(t.get("points_delta", 0))
    return total


def _get_first_awarded_at(employee_id: str, txs: list[dict], event_id: str = None) -> str:
    """For tiebreaker: earliest point transaction."""
    relevant = [
        t for t in txs
        if t.get("employee_id") == employee_id
        and t.get("reason_code") == "first_unique_device"
        and (not event_id or t.get("event_id") == event_id)
    ]
    if not relevant:
        return "9999"
    return min(t.get("created_at", "9999") for t in relevant)


def build_leaderboard(
    country_code: str = None,
    event_id: str = None,
    period: str = "all",  # all | today | week | month
    top_n: int = 50,
) -> list[dict]:
    sheets = get_sheets()
    employees = sheets.get_all_records(SHEET_EMPLOYEES)
    all_txs = sheets.get_all_records(SHEET_POINT_TRANSACTIONS)

    # Filter by period
    period_filter = ""
    if period == "today":
        period_filter = start_of_day_utc().strftime("%Y-%m-%d")
    elif period == "week":
        period_filter = start_of_week_utc().strftime("%Y-%m-%d")
    elif period == "month":
        period_filter = start_of_month_utc().strftime("%Y-%m-%d")

    if period_filter:
        all_txs = [t for t in all_txs if t.get("created_at", "") >= period_filter]

    # Filter by event if needed
    if event_id:
        employees = [e for e in employees]  # all employees (filter by participation)

    # Filter by country
    if country_code:
        employees = [e for e in employees if e.get("country_code", "").upper() == country_code.upper()]

    # Only active employees
    employees = [e for e in employees if e.get("status") == "active"]

    results = []
    for emp in employees:
        eid = emp.get("employee_id")
        points = _calc_employee_points(eid, all_txs, event_id)
        first_at = _get_first_awarded_at(eid, all_txs, event_id)
        results.append({
            "employee_id": eid,
            "employee_code": emp.get("employee_code"),
            "full_name": emp.get("full_name"),
            "country_code": emp.get("country_code"),
            "points": points,
            "_first_at": first_at,
        })

    # Sort: points DESC, then earliest first_at ASC (tiebreaker)
    results.sort(key=lambda x: (-x["points"], x["_first_at"]))

    # Add rank
    for i, r in enumerate(results[:top_n], 1):
        r["rank"] = i
        del r["_first_at"]

    return results[:top_n]


def get_employee_rank(employee_id: str, country_code: str = None, event_id: str = None) -> int:
    lb = build_leaderboard(country_code=country_code, event_id=event_id)
    for entry in lb:
        if entry["employee_id"] == employee_id:
            return entry["rank"]
    return -1
