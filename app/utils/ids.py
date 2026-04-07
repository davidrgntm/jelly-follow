"""Centralized ID generator module."""
from datetime import datetime, timezone

def _date_str():
    return datetime.now(timezone.utc).strftime("%Y%m%d")

def _pad(n, width=4):
    return str(n).zfill(width)

def generate_admin_id(seq):
    return f"ADM-{_pad(seq)}"

def generate_employee_id(seq):
    return f"EMP-{_pad(seq)}"

def generate_employee_code(country_code, seq):
    return f"{country_code.upper()}-{_pad(seq)}"

def generate_event_id(seq):
    return f"EVT-{_date_str()}-{_pad(seq, 3)}"

def generate_event_code(seq):
    return generate_event_id(seq)

def generate_reward_id(seq):
    return f"RWD-{_pad(seq)}"

def generate_participant_id(seq):
    return f"PAR-{_pad(seq)}"

def generate_qr_id(seq):
    return f"QR-{_pad(seq, 6)}"

def generate_scan_id(seq):
    return f"SCN-{_date_str()}-{_pad(seq, 6)}"

def generate_point_tx_id(seq):
    return f"PTX-{_date_str()}-{_pad(seq, 6)}"

def generate_log_id(seq):
    return f"LOG-{_date_str()}-{_pad(seq, 6)}"


def generate_bonus_rule_id(seq):
    return f"EBR-{_date_str()}-{_pad(seq, 4)}"


def generate_bonus_submission_id(seq):
    return f"EBS-{_date_str()}-{_pad(seq, 6)}"
