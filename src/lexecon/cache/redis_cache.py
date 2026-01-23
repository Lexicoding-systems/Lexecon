"""Redis Cache Implementation.

Provides Redis-based caching with TTL support for Lexecon services.
"""

import hashlib
import json
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional, Union

import redis


class RedisCache:
    """Redis cache service with connection management."""

    def __init__(self, url: Optional[str] = None):
        """Initialize Redis cache."""
        self.url = url or self._get_redis_url()
        self.client = self._create_client()
        self._test_connection()

    def _get_redis_url(self) -> str:
        """Get Redis URL from environment or use default."""
        import os
        return os.getenv("LEXECON_REDIS_URL", "redis://localhost:6379/0")

    def _create_client(self) -> redis.Redis:
        """Create Redis client with connection pooling."""
        return redis.from_url(
            self.url,
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )

    def _test_connection(self) -> None:
        """Test Redis connection on initialization."""
        try:
            self.client.ping()
        except redis.ConnectionError as e:
            print(f"Redis connection failed: {e}. Cache will be disabled.")
            self.client = None

    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self.client is not None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_available():
            return None

        try:
            value = self.client.get(key)
            if value is None:
                return None

            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except redis.RedisError:
            return None

    def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set value in cache."""
        if not self.is_available():
            return False

        try:
            serialized = json.dumps(value) if isinstance(value, (dict, list, tuple)) else str(value)

            if ttl:
                ttl_seconds = int(ttl.total_seconds()) if isinstance(ttl, timedelta) else int(ttl)
                return self.client.setex(key, ttl_seconds, serialized)
            return self.client.set(key, serialized)
        except redis.RedisError:
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_available():
            return False

        try:
            return bool(self.client.delete(key))
        except redis.RedisError:
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.is_available():
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except redis.RedisError:
            return 0

    def cache_key(self, prefix: str, *args) -> str:
        """Generate cache key from prefix and args."""
        key_data = ":".join([str(arg) for arg in args])
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Get global Redis cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


def redis_cache(prefix: str, ttl: int = 300):
    """Decorator for caching function results in Redis."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_redis_cache()

            if not cache.is_available():
                return func(*args, **kwargs)

            cache_key = cache.cache_key(prefix, *args, *sorted(kwargs.items()))
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def cache_policy_eval(ttl: int = 600):
    """Cache policy evaluation results."""
    return redis_cache("policy_eval", ttl)


def cache_decision(ttl: int = 300):
    """Cache decision results."""
    return redis_cache("decision", ttl)


def cache_compliance_mapping(ttl: int = 900):
    """Cache compliance mappings."""
    return redis_cache("compliance_map", ttl)


def cache_api_response(ttl: int = 60):
    """Cache API responses."""
    return redis_cache("api_response", ttl)
