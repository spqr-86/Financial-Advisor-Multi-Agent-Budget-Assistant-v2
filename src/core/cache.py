"""Simple TTL cache for performance optimization."""

from datetime import datetime, timedelta
from typing import Any


class TTLCache:
    """Thread-safe TTL cache with automatic expiration."""

    def __init__(self, ttl_seconds: int = 60):
        """Initialize cache with TTL in seconds."""
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return value
            # Expired - remove
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp."""
        self._cache[key] = (value, datetime.now())

    def invalidate(self, key: str) -> None:
        """Remove specific key from cache."""
        if key in self._cache:
            del self._cache[key]

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove all keys starting with prefix."""
        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


# Global cache instances
limits_cache = TTLCache(ttl_seconds=60)  # Limits rarely change
stats_cache = TTLCache(ttl_seconds=30)   # Stats can be cached briefly
