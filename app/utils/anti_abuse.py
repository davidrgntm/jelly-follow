"""
Anti-abuse module for tracking endpoint.
Detects suspicious patterns: rapid requests, IP flooding, etc.
"""
import time
import threading
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

_lock = threading.Lock()

_ip_hits: dict[str, list[float]] = defaultdict(list)
_device_hits: dict[str, list[float]] = defaultdict(list)

WINDOW_SECONDS = 60
MAX_IP_REQUESTS = 15
MAX_DEVICE_REQUESTS = 5
RAPID_THRESHOLD_SECONDS = 2
RAPID_MAX_COUNT = 3


def _cleanup(hits: dict[str, list[float]], now: float):
    expired_keys = []
    for key, timestamps in hits.items():
        hits[key] = [ts for ts in timestamps if now - ts < WINDOW_SECONDS]
        if not hits[key]:
            expired_keys.append(key)
    for k in expired_keys:
        del hits[k]


def check_abuse(ip_address: str, device_key: str = "") -> dict:
    """
    Returns abuse check result:
    {
        "suspicious": bool,
        "reasons": list[str],
        "ip_count": int,
        "device_count": int,
    }
    """
    now = time.time()
    reasons = []

    with _lock:
        if len(_ip_hits) > 50000:
            _cleanup(_ip_hits, now)
        if len(_device_hits) > 50000:
            _cleanup(_device_hits, now)

        ip_times = _ip_hits[ip_address]
        ip_times = [ts for ts in ip_times if now - ts < WINDOW_SECONDS]
        ip_times.append(now)
        _ip_hits[ip_address] = ip_times

        if len(ip_times) > MAX_IP_REQUESTS:
            reasons.append(f"ip_flood:{len(ip_times)}_in_{WINDOW_SECONDS}s")

        if len(ip_times) >= RAPID_MAX_COUNT:
            recent = ip_times[-RAPID_MAX_COUNT:]
            if recent[-1] - recent[0] < RAPID_THRESHOLD_SECONDS:
                reasons.append("rapid_ip_requests")

        device_count = 0
        if device_key:
            dev_times = _device_hits[device_key]
            dev_times = [ts for ts in dev_times if now - ts < WINDOW_SECONDS]
            dev_times.append(now)
            _device_hits[device_key] = dev_times
            device_count = len(dev_times)

            if device_count > MAX_DEVICE_REQUESTS:
                reasons.append(f"device_flood:{device_count}_in_{WINDOW_SECONDS}s")

    return {
        "suspicious": len(reasons) > 0,
        "reasons": reasons,
        "ip_count": len(ip_times),
        "device_count": device_count,
    }
