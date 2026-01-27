"""
Tests for caching module (Phase 8).
"""

import time
import pytest
from lexecon.cache.memory_cache import MemoryCache, cached


class TestMemoryCache:
    """Tests for MemoryCache."""

    def test_cache_basic_operations(self):
        """Test basic cache set/get operations."""
        cache = MemoryCache(max_size=100, ttl=300)

        # Set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Get non-existent key
        assert cache.get("nonexistent") is None

    def test_cache_ttl_expiration(self):
        """Test TTL expiration."""
        cache = MemoryCache(max_size=100, ttl=1)  # 1 second TTL

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for TTL to expire
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_max_size_eviction(self):
        """Test LRU eviction when max size reached."""
        cache = MemoryCache(max_size=3, ttl=300)

        # Fill cache to max
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.size() == 3

        # Add one more - should evict oldest
        cache.set("key4", "value4")

        assert cache.size() == 3
        assert cache.get("key1") is None  # Oldest evicted
        assert cache.get("key4") == "value4"  # Newest exists

    def test_cache_delete(self):
        """Test cache deletion."""
        cache = MemoryCache(max_size=100, ttl=300)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_cache_clear(self):
        """Test cache clear."""
        cache = MemoryCache(max_size=100, ttl=300)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = MemoryCache(max_size=100, ttl=300)

        cache.set("key1", "value1")
        stats = cache.get_stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 100
        assert stats["ttl"] == 300
        assert stats["oldest_entry_age"] >= 0


class TestCachedDecorator:
    """Tests for @cached decorator."""

    def test_cached_decorator_basic(self):
        """Test basic cached decorator functionality."""
        call_count = 0

        @cached(ttl=300)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - cache miss
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - cache hit
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented

        # Different argument - cache miss
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_cached_decorator_ttl(self):
        """Test cached decorator TTL expiration."""
        call_count = 0

        @cached(ttl=1)  # 1 second TTL
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Wait for TTL
        time.sleep(1.1)

        # Second call after TTL - cache miss
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 2

    def test_cached_decorator_with_kwargs(self):
        """Test cached decorator with keyword arguments."""
        call_count = 0

        @cached(ttl=300)
        def expensive_function(x: int, y: int = 10) -> int:
            nonlocal call_count
            call_count += 1
            return x + y

        # Test with different kwargs
        result1 = expensive_function(5, y=10)
        assert result1 == 15
        assert call_count == 1

        result2 = expensive_function(5, y=10)
        assert result2 == 15
        assert call_count == 1  # Cache hit

        result3 = expensive_function(5, y=20)
        assert result3 == 25
        assert call_count == 2  # Different args

    def test_cached_decorator_custom_cache(self):
        """Test cached decorator with custom cache instance."""
        custom_cache = MemoryCache(max_size=10, ttl=60)
        call_count = 0

        @cached(cache_instance=custom_cache)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result = expensive_function(5)
        assert result == 10
        assert call_count == 1
        assert custom_cache.size() == 1

    def test_cached_decorator_with_key_prefix(self):
        """Test cached decorator with key prefix."""

        @cached(ttl=300, key_prefix="test:")
        def function1(x: int) -> int:
            return x * 2

        @cached(ttl=300, key_prefix="other:")
        def function2(x: int) -> int:
            return x * 3

        # Different prefixes should not collide
        result1 = function1(5)
        result2 = function2(5)

        assert result1 == 10
        assert result2 == 15


class TestCachePerformance:
    """Performance tests for cache."""

    def test_cache_performance_baseline(self):
        """Baseline performance test for cache operations."""
        cache = MemoryCache(max_size=10000, ttl=300)

        # Measure set performance
        start = time.time()
        for i in range(1000):
            cache.set(f"key{i}", f"value{i}")
        set_duration = time.time() - start

        # Measure get performance
        start = time.time()
        for i in range(1000):
            cache.get(f"key{i}")
        get_duration = time.time() - start

        print(f"\n  Set 1000 items: {set_duration*1000:.2f}ms")
        print(f"  Get 1000 items: {get_duration*1000:.2f}ms")

        # Performance assertions
        assert set_duration < 0.1  # <100ms for 1000 sets
        assert get_duration < 0.05  # <50ms for 1000 gets

    def test_cache_hit_rate(self):
        """Test cache hit rate calculation."""
        cache = MemoryCache(max_size=100, ttl=300)

        # Populate cache
        for i in range(50):
            cache.set(f"key{i}", f"value{i}")

        # Test hit rate (50% hits, 50% misses)
        hits = 0
        misses = 0

        for i in range(100):
            result = cache.get(f"key{i}")
            if result is not None:
                hits += 1
            else:
                misses += 1

        hit_rate = hits / (hits + misses)
        print(f"\n  Cache hit rate: {hit_rate*100:.1f}%")

        assert hit_rate == 0.5  # 50% hit rate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
