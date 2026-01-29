"""
Caching module for Lexecon (Phase 8).

Provides multi-layer caching:
- In-memory LRU cache (L1)
- Redis distributed cache (L2)
- Cache decorators for easy use
"""

from lexecon.cache.memory_cache import MemoryCache, cached
from lexecon.cache.redis_cache import (
    cache_api_response,
    cache_compliance_mapping,
    cache_decision,
    cache_policy_eval,
)

__all__ = [
    "MemoryCache",
    "cached",
    "cache_api_response",
    "cache_compliance_mapping",
    "cache_decision",
    "cache_policy_eval",
]
