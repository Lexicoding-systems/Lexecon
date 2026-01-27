"""
Caching module for Lexecon (Phase 8).

Provides multi-layer caching:
- In-memory LRU cache (L1)
- Redis distributed cache (L2)
- Cache decorators for easy use
"""

from lexecon.cache.memory_cache import MemoryCache, cached

__all__ = ["MemoryCache", "cached"]
