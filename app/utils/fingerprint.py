"""Device fingerprinting and device_key generation."""
import hashlib
import re


def compute_device_key(client_device_id=None, fingerprint_id=None, os_name=None, browser_name=None,
                       platform=None, screen_width=None, screen_height=None,
                       timezone=None, user_agent=None):
    client_device_id = (client_device_id or "").strip().lower()
    if client_device_id:
        return hashlib.sha256(("cdid|" + client_device_id).encode("utf-8")).hexdigest()

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


def _normalize_ua(ua):
    ua = re.sub(r"/[\d.]+", "", ua)
    ua = re.sub(r"\(.*?\)", "", ua)
    return ua.strip().lower()[:200]


def is_suspicious_ua(user_agent):
    if not user_agent:
        return True
    ua_lower = user_agent.lower()
    bot_signals = [
        "bot", "crawler", "spider", "scraper", "headless",
        "python-requests", "curl", "wget", "java/", "go-http",
        "apache-httpclient", "okhttp", "postman",
    ]
    return any(sig in ua_lower for sig in bot_signals)
