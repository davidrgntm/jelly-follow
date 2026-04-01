"""
In-memory TTL cache for frequently accessed Google Sheets data.
Reduces API calls and speeds up tracking/leaderboard operations.
"""
import time
import threading
import logging
from typing import Any, Optional, Callable

logger = logging.getLogger(__name__)

_lock = threading.Lock()


class TTLCache:
    """Simple thread-safe TTL cache."""

    def __init__(self, ttl_seconds: int = 30, max_size: int = 5000):
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        with _lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with _lock:
            if len(self._store) >= self._max_size:
                self._evict()
            self._store[key] = (value, time.time() + self._ttl)

    def delete(self, key: str) -> None:
        with _lock:
            self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        with _lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]

    def clear(self) -> None:
        with _lock:
            self._store.clear()

    def _evict(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        if len(self._store) >= self._max_size:
            oldest = sorted(self._store.items(), key=lambda x: x[1][1])
            for k, _ in oldest[: len(oldest) // 4]:
                del self._store[k]


# ── Global caches ─────────────────────────────────────────────────────────────
employees_cache = TTLCache(ttl_seconds=60, max_size=2000)
device_cache = TTLCache(ttl_seconds=45, max_size=10000)
countries_cache = TTLCache(ttl_seconds=300, max_size=20)
events_cache = TTLCache(ttl_seconds=30, max_size=200)
leaderboard_cache = TTLCache(ttl_seconds=15, max_size=100)


def invalidate_employee(employee_id: str = "", telegram_user_id: str = "",
                        employee_code: str = ""):
    """Invalidate all employee-related caches."""
    if employee_id:
        employees_cache.delete(f"id:{employee_id}")
    if telegram_user_id:
        employees_cache.delete(f"tg:{telegram_user_id}")
    if employee_code:
        employees_cache.delete(f"code:{employee_code}")
    employees_cache.invalidate_prefix("all:")
    leaderboard_cache.clear()


def invalidate_events():
    events_cache.clear()
    leaderboard_cache.clear()
