"""
Centralized ID generator module.
All IDs are generated here to avoid collisions.
"""
import re
from datetime import datetime, timezone


def _date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _pad(n: int, width: int = 4) -> str:
    return str(n).zfill(width)


def generate_admin_id(seq: int) -> str:
    """ADM-0001"""
    return f"ADM-{_pad(seq)}"


def generate_employee_id(seq: int) -> str:
    """EMP-0001"""
    return f"EMP-{_pad(seq)}"


def generate_employee_code(country_code: str, seq: int) -> str:
    """UZ-0001, RU-0001, KG-0001, AZ-0001"""
    return f"{country_code.upper()}-{_pad(seq)}"


def generate_event_id(seq: int) -> str:
    """EVT-20260401-001"""
    return f"EVT-{_date_str()}-{_pad(seq, 3)}"


def generate_event_code(seq: int) -> str:
    """EVT-20260401-001"""
    return generate_event_id(seq)


def generate_reward_id(seq: int) -> str:
    """RWD-0001"""
    return f"RWD-{_pad(seq)}"


def generate_participant_id(seq: int) -> str:
    """PAR-0001"""
    return f"PAR-{_pad(seq)}"


def generate_qr_id(seq: int) -> str:
    """QR-000001"""
    return f"QR-{_pad(seq, 6)}"


def generate_scan_id(seq: int) -> str:
    """SCN-20260401-000001"""
    return f"SCN-{_date_str()}-{_pad(seq, 6)}"


def generate_point_tx_id(seq: int) -> str:
    """PTX-20260401-000001"""
    return f"PTX-{_date_str()}-{_pad(seq, 6)}"


def generate_log_id(seq: int) -> str:
    """LOG-20260401-000001"""
    return f"LOG-{_date_str()}-{_pad(seq, 6)}"
