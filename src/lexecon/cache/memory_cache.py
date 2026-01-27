"""
In-memory LRU cache implementation (Phase 8).

Thread-safe in-memory cache with TTL support.
"""

import hashlib
import json
import threading
import time
from functools import wraps
from typing import Any, Callable, Optional


class MemoryCache:
    """Thread-safe in-memory LRU cache with TTL."""

    def __init__(self, max_size: int = 10000, ttl: int = 300) -> None:
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of items in cache
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: dict[str, Any] = {}
        self._timestamps: dict[str, float] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            # Check TTL
            if time.time() - self._timestamps[key] > self.ttl:
                self._delete_unsafe(key)
                return None

            return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest_key = min(self._timestamps, key=self._timestamps.get)
                self._delete_unsafe(oldest_key)

            self._cache[key] = value
            self._timestamps[key] = time.time()

    def delete(self, key: str) -> None:
        """
        Remove key from cache.

        Args:
            key: Cache key to delete
        """
        with self._lock:
            self._delete_unsafe(key)

    def _delete_unsafe(self, key: str) -> None:
        """Delete key without acquiring lock (internal use)."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def size(self) -> int:
        """
        Get current cache size.

        Returns:
            Number of items in cache
        """
        with self._lock:
            return len(self._cache)

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "oldest_entry_age": (
                    time.time() - min(self._timestamps.values())
                    if self._timestamps
                    else 0
                ),
            }


def cached(
    ttl: int = 300, cache_instance: Optional[MemoryCache] = None, key_prefix: str = ""
) -> Callable:
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        cache_instance: Cache instance to use (creates new if None)
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function

    Example:
        @cached(ttl=300)
        def get_active_policies():
            return db.query("SELECT * FROM policies WHERE active = true")
    """
    if cache_instance is None:
        cache_instance = MemoryCache(ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key from function name and arguments
            args_str = json.dumps([args, kwargs], sort_keys=True, default=str)
            cache_key_hash = hashlib.md5(args_str.encode()).hexdigest()
            cache_key = f"{key_prefix}{func.__name__}:{cache_key_hash}"

            # Try cache first
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Cache miss - execute function
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result)

            return result

        # Attach cache instance for testing/inspection
        wrapper.cache = cache_instance  # type: ignore
        return wrapper

    return decorator
