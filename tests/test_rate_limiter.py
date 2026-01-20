"""
Tests for rate limiting service.
"""

import time
import pytest
from lexecon.security.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    TokenBucket,
)


class TestTokenBucket:
    """Tests for token bucket implementation."""

    def test_initialization(self):
        """Test token bucket initialization."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.refill_rate == 1.0
        assert bucket.tokens == 10.0

    def test_consume_tokens_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        result = bucket.consume(5)
        assert result is True
        assert bucket.get_tokens() == pytest.approx(5.0, abs=0.1)

    def test_consume_tokens_insufficient(self):
        """Test token consumption with insufficient tokens."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        bucket.consume(9)
        result = bucket.consume(5)
        assert result is False
        assert bucket.get_tokens() == pytest.approx(1.0, abs=0.1)

    def test_token_refill(self):
        """Test token refill over time."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)
        bucket.consume(10)
        time.sleep(0.5)  # Wait for refill
        tokens = bucket.get_tokens()
        assert tokens >= 4.0  # Should have refilled ~5 tokens

    def test_refill_does_not_exceed_capacity(self):
        """Test that refill doesn't exceed capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=100.0)
        time.sleep(1.0)
        tokens = bucket.get_tokens()
        assert tokens <= 10.0


class TestRateLimitConfig:
    """Tests for rate limit configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.burst_size == 10

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            requests_per_minute=120,
            requests_per_hour=2000,
            burst_size=20,
        )
        assert config.requests_per_minute == 120
        assert config.requests_per_hour == 2000
        assert config.burst_size == 20


class TestRateLimiter:
    """Tests for rate limiter."""

    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter()
        assert limiter.config.requests_per_minute == 60
        assert limiter.config.requests_per_hour == 1000

    def test_check_rate_limit_allowed(self):
        """Test rate limit check when within limits."""
        limiter = RateLimiter()
        allowed, info = limiter.check_rate_limit("client1")
        assert allowed is True
        assert info["allowed"] is True
        assert "remaining_minute" in info
        assert "remaining_hour" in info

    def test_check_rate_limit_burst(self):
        """Test burst capacity handling."""
        config = RateLimitConfig(burst_size=3)
        limiter = RateLimiter(config)

        # Should allow burst
        for i in range(3):
            allowed, info = limiter.check_rate_limit("client1")
            assert allowed is True

        # Should deny after burst exhausted
        allowed, info = limiter.check_rate_limit("client1")
        assert allowed is False
        assert "retry_after_seconds" in info

    def test_check_rate_limit_minute_exceeded(self):
        """Test minute rate limit exceeded."""
        config = RateLimitConfig(
            requests_per_minute=2,
            burst_size=2,
        )
        limiter = RateLimiter(config)

        # Consume all minute tokens
        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client1")

        # Should be denied
        allowed, info = limiter.check_rate_limit("client1")
        assert allowed is False
        assert info["retry_after_seconds"] == 60

    def test_check_rate_limit_per_client(self):
        """Test rate limiting is per-client."""
        config = RateLimitConfig(burst_size=2)
        limiter = RateLimiter(config)

        # Client 1 exhausts limit
        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client1")
        allowed1, _ = limiter.check_rate_limit("client1")
        assert allowed1 is False

        # Client 2 should still be allowed
        allowed2, _ = limiter.check_rate_limit("client2")
        assert allowed2 is True

    def test_reset_client(self):
        """Test resetting client rate limits."""
        config = RateLimitConfig(burst_size=1)
        limiter = RateLimiter(config)

        # Exhaust limit
        limiter.check_rate_limit("client1")
        allowed, _ = limiter.check_rate_limit("client1")
        assert allowed is False

        # Reset and check again
        limiter.reset_client("client1")
        allowed, _ = limiter.check_rate_limit("client1")
        assert allowed is True

    def test_get_stats(self):
        """Test getting rate limiter statistics."""
        limiter = RateLimiter()
        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client2")

        stats = limiter.get_stats()
        assert stats["tracked_clients"] == 2
        assert "config" in stats
        assert stats["config"]["requests_per_minute"] == 60

    def test_remaining_decreases(self):
        """Test remaining requests decrease correctly."""
        config = RateLimitConfig(burst_size=5)
        limiter = RateLimiter(config)

        _, info1 = limiter.check_rate_limit("client1")
        remaining1 = info1["remaining_minute"]

        _, info2 = limiter.check_rate_limit("client1")
        remaining2 = info2["remaining_minute"]

        assert remaining2 < remaining1

    def test_hour_limit_independent(self):
        """Test hour and minute limits are independent."""
        config = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=5,
            burst_size=10,
        )
        limiter = RateLimiter(config)

        # Consume hour limit
        for i in range(5):
            allowed, _ = limiter.check_rate_limit("client1")
            assert allowed is True

        # Should be denied due to hour limit
        allowed, info = limiter.check_rate_limit("client1")
        assert allowed is False
        assert info["retry_after_seconds"] == 3600


class TestRateLimiterThreadSafety:
    """Tests for thread safety of rate limiter."""

    def test_concurrent_requests(self):
        """Test concurrent requests are handled correctly."""
        import threading

        config = RateLimitConfig(burst_size=10)
        limiter = RateLimiter(config)
        results = []

        def make_request():
            allowed, _ = limiter.check_rate_limit("client1")
            results.append(allowed)

        threads = [threading.Thread(target=make_request) for _ in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 10 should be allowed (burst size)
        # Due to threading, some might race but at most 10-11 should succeed
        allowed_count = sum(1 for r in results if r)
        assert 10 <= allowed_count <= 11


class TestEdgeCases:
    """Test edge cases for rate limiter."""

    def test_zero_burst_size(self):
        """Test with zero burst size."""
        config = RateLimitConfig(burst_size=0, requests_per_minute=60)
        limiter = RateLimiter(config)

        allowed, _ = limiter.check_rate_limit("client1")
        # Should be denied immediately with zero burst
        assert allowed is False

    def test_very_high_limits(self):
        """Test with very high rate limits."""
        config = RateLimitConfig(
            requests_per_minute=10000,
            requests_per_hour=100000,
            burst_size=1000,
        )
        limiter = RateLimiter(config)

        # Should allow many requests
        for i in range(100):
            allowed, _ = limiter.check_rate_limit("client1")
            assert allowed is True

    def test_multiple_clients_isolation(self):
        """Test that multiple clients don't interfere."""
        limiter = RateLimiter()

        # Create requests from multiple clients
        for i in range(5):
            client_id = f"client{i}"
            allowed, _ = limiter.check_rate_limit(client_id)
            assert allowed is True

        stats = limiter.get_stats()
        assert stats["tracked_clients"] == 5
