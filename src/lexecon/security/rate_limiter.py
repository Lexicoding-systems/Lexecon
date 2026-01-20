"""
Rate Limiting Service for API protection.

Implements token bucket algorithm for rate limiting API requests
to prevent abuse and ensure fair resource usage.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Allows burst traffic while maintaining average rate limit.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens in bucket (burst size)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self.lock = Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))
        self.last_refill = now

    def get_tokens(self) -> float:
        """Get current token count."""
        with self.lock:
            self._refill()
            return self.tokens


class RateLimiter:
    """
    Rate limiting service using token bucket algorithm.

    Tracks rate limits per client identifier (IP, user ID, API key).
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limiting configuration
        """
        self.config = config or RateLimitConfig()

        # Per-minute buckets
        self.minute_buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                capacity=self.config.burst_size,
                refill_rate=self.config.requests_per_minute / 60.0,
            )
        )

        # Per-hour buckets
        self.hour_buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                capacity=self.config.requests_per_hour,
                refill_rate=self.config.requests_per_hour / 3600.0,
            )
        )

        self.lock = Lock()

    def check_rate_limit(self, client_id: str) -> tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limits.

        Args:
            client_id: Identifier for client (IP, user ID, etc.)

        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        with self.lock:
            minute_bucket = self.minute_buckets[client_id]
            hour_bucket = self.hour_buckets[client_id]

            # Check both limits
            minute_allowed = minute_bucket.consume(1)
            hour_allowed = hour_bucket.consume(1) if minute_allowed else False

            allowed = minute_allowed and hour_allowed

            # If not allowed, rollback minute bucket consumption
            if not allowed and minute_allowed:
                minute_bucket.tokens += 1

            info = {
                "allowed": allowed,
                "remaining_minute": int(minute_bucket.get_tokens()),
                "remaining_hour": int(hour_bucket.get_tokens()),
                "limit_minute": self.config.requests_per_minute,
                "limit_hour": self.config.requests_per_hour,
            }

            if not allowed:
                if not minute_allowed:
                    info["retry_after_seconds"] = 60
                else:
                    info["retry_after_seconds"] = 3600

            return allowed, info

    def reset_client(self, client_id: str):
        """
        Reset rate limits for a client.

        Args:
            client_id: Client identifier to reset
        """
        with self.lock:
            if client_id in self.minute_buckets:
                del self.minute_buckets[client_id]
            if client_id in self.hour_buckets:
                del self.hour_buckets[client_id]

    def get_stats(self) -> Dict[str, any]:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            return {
                "tracked_clients": len(self.minute_buckets),
                "config": {
                    "requests_per_minute": self.config.requests_per_minute,
                    "requests_per_hour": self.config.requests_per_hour,
                    "burst_size": self.config.burst_size,
                },
            }
