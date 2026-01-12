"""
Rate Limiting Service with Token Bucket Algorithm.

Provides in-memory rate limiting for Lexecon authentication and API endpoints.
Supports per-IP, per-user, and per-endpoint rate limits.

Security Features:
- Token bucket algorithm for smooth rate limiting
- Configurable limits per context
- Thread-safe implementation
- Automatic bucket cleanup to prevent memory leaks
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    The token bucket algorithm allows bursts while maintaining an average rate.
    Tokens are added to the bucket at a constant rate up to a maximum capacity.
    Each request consumes one token. If no tokens are available, the request is rate limited.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens (burst size)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed successfully, False if rate limited
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def get_retry_after(self) -> int:
        """
        Calculate seconds until next token is available.

        Returns:
            Seconds to wait before retry
        """
        with self.lock:
            self._refill()

            if self.tokens >= 1:
                return 0

            # Calculate time needed to refill 1 token
            tokens_needed = 1 - self.tokens
            seconds_needed = tokens_needed / self.refill_rate
            return int(seconds_needed) + 1


class RateLimiter:
    """
    In-memory rate limiter with token bucket algorithm.

    Supports multiple rate limit configurations:
    - Global per-IP limits
    - Per-endpoint per-IP limits
    - Per-user limits
    - Custom limits by key

    Thread-safe for concurrent requests.
    """

    def __init__(self):
        """Initialize rate limiter with default configurations."""
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = threading.Lock()

        # Rate limit configurations
        # Format: (capacity, window_seconds)
        self.limits = {
            # Global limits
            "global_per_ip": (100, 60),  # 100 requests per 60 seconds

            # Auth endpoint limits (stricter)
            "auth_login_per_ip": (5, 300),  # 5 attempts per 5 minutes
            "auth_login_per_user": (5, 300),  # 5 attempts per username per 5 minutes
            "auth_mfa_per_challenge": (3, 300),  # 3 MFA attempts per challenge
            "auth_register_per_ip": (3, 3600),  # 3 registrations per hour

            # API endpoint limits
            "api_per_user": (1000, 3600),  # 1000 requests per hour per user
            "api_export_per_user": (10, 86400),  # 10 exports per day per user
            "api_create_user_per_ip": (3, 3600),  # 3 user creations per hour

            # Password management
            "password_change_per_user": (5, 3600),  # 5 password changes per hour
            "password_reset_per_email": (3, 3600),  # 3 reset requests per hour
        }

        # Track bucket creation times for cleanup
        self.bucket_created: Dict[str, datetime] = {}

        # Start cleanup thread
        self._start_cleanup_thread()

    def _get_or_create_bucket(self, key: str, limit_type: str) -> TokenBucket:
        """
        Get existing bucket or create new one.

        Args:
            key: Unique identifier (e.g., "ip:192.168.1.1")
            limit_type: Type of limit (e.g., "global_per_ip")

        Returns:
            TokenBucket instance
        """
        bucket_key = f"{limit_type}:{key}"

        with self.lock:
            if bucket_key not in self.buckets:
                capacity, window = self.limits.get(limit_type, (100, 60))
                refill_rate = capacity / window

                self.buckets[bucket_key] = TokenBucket(capacity, refill_rate)
                self.bucket_created[bucket_key] = datetime.now()

            return self.buckets[bucket_key]

    def check_rate_limit(self, key: str, limit_type: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit WITHOUT consuming a token.

        Args:
            key: Unique identifier for rate limit context
            limit_type: Type of rate limit to check

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        if limit_type not in self.limits:
            # Unknown limit type, allow by default
            return True, None

        bucket = self._get_or_create_bucket(key, limit_type)

        # Check without consuming
        with bucket.lock:
            bucket._refill()
            if bucket.tokens >= 1:
                return True, None
            else:
                retry_after = bucket.get_retry_after()
                return False, retry_after

    def consume(self, key: str, limit_type: str, tokens: int = 1) -> bool:
        """
        Consume tokens from rate limit bucket.

        Args:
            key: Unique identifier for rate limit context
            limit_type: Type of rate limit
            tokens: Number of tokens to consume (default: 1)

        Returns:
            True if tokens consumed successfully, False if rate limited
        """
        if limit_type not in self.limits:
            # Unknown limit type, allow by default
            return True

        bucket = self._get_or_create_bucket(key, limit_type)
        return bucket.consume(tokens)

    def get_retry_after(self, key: str, limit_type: str) -> int:
        """
        Get seconds until rate limit resets.

        Args:
            key: Unique identifier for rate limit context
            limit_type: Type of rate limit

        Returns:
            Seconds until next token is available
        """
        if limit_type not in self.limits:
            return 0

        bucket = self._get_or_create_bucket(key, limit_type)
        return bucket.get_retry_after()

    def reset(self, key: str, limit_type: str):
        """
        Reset rate limit for a specific key.

        Useful for administrative overrides or after successful login.

        Args:
            key: Unique identifier for rate limit context
            limit_type: Type of rate limit
        """
        bucket_key = f"{limit_type}:{key}"

        with self.lock:
            if bucket_key in self.buckets:
                capacity, window = self.limits[limit_type]
                refill_rate = capacity / window
                self.buckets[bucket_key] = TokenBucket(capacity, refill_rate)

    def get_remaining(self, key: str, limit_type: str) -> int:
        """
        Get remaining tokens for a key.

        Args:
            key: Unique identifier for rate limit context
            limit_type: Type of rate limit

        Returns:
            Number of remaining tokens
        """
        if limit_type not in self.limits:
            return -1  # Unlimited

        bucket = self._get_or_create_bucket(key, limit_type)

        with bucket.lock:
            bucket._refill()
            return int(bucket.tokens)

    def cleanup_expired_buckets(self, max_age_hours: int = 24):
        """
        Remove expired buckets to prevent memory leak.

        Args:
            max_age_hours: Remove buckets older than this many hours
        """
        now = datetime.now()
        cutoff = now - timedelta(hours=max_age_hours)

        with self.lock:
            expired_keys = [
                key for key, created in self.bucket_created.items()
                if created < cutoff
            ]

            for key in expired_keys:
                del self.buckets[key]
                del self.bucket_created[key]

            if expired_keys:
                print(f"Rate limiter: Cleaned up {len(expired_keys)} expired buckets")

    def _start_cleanup_thread(self):
        """Start background thread for bucket cleanup."""
        def cleanup_loop():
            while True:
                time.sleep(3600)  # Run every hour
                self.cleanup_expired_buckets(max_age_hours=24)

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

    def get_stats(self) -> Dict[str, int]:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            return {
                "total_buckets": len(self.buckets),
                "configured_limits": len(self.limits)
            }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get global rate limiter instance.

    Returns:
        Global RateLimiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        _rate_limiter = RateLimiter()

    return _rate_limiter
