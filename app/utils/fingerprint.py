"""
Device fingerprinting and device_key generation.
Used to enforce 1 unique device = 1 ball rule.
"""
import hashlib
import re
from typing import Optional


def compute_device_key(
    fingerprint_id: Optional[str],
    os_name: Optional[str],
    browser_name: Optional[str],
    platform: Optional[str],
    screen_width: Optional[int],
    screen_height: Optional[int],
    timezone: Optional[str],
    user_agent: Optional[str],
) -> str:
    """
    Creates a stable hash from device signals.
    Deterministic: same device = same key.
    """
    parts = [
        (fingerprint_id or "").strip().lower(),
        (os_name or "").strip().lower(),
        (browser_name or "").strip().lower(),
        (platform or "").strip().lower(),
        str(screen_width or 0),
        str(screen_height or 0),
        (timezone or "").strip(),
        _normalize_ua(user_agent or ""),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _normalize_ua(ua: str) -> str:
    """Strip version numbers for more stable matching."""
    # Remove version numbers like /1.2.3 or (Version 10)
    ua = re.sub(r"/[\d.]+", "", ua)
    ua = re.sub(r"\(.*?\)", "", ua)
    return ua.strip().lower()[:200]


def is_suspicious_ua(user_agent: str) -> bool:
    """Detect likely bot/scraper user agents."""
    if not user_agent:
        return True
    ua_lower = user_agent.lower()
    bot_signals = [
        "bot", "crawler", "spider", "scraper", "headless",
        "python-requests", "curl", "wget", "java/", "go-http",
        "apache-httpclient", "okhttp", "postman",
    ]
    return any(sig in ua_lower for sig in bot_signals)
