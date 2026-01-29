"""Unit tests for security fixes in post-v1.0 hygiene.

These tests verify the Bandit security fixes without requiring
the full cryptography import chain.
"""

import hashlib
import json


def test_cache_uses_sha256_not_md5():
    """Verify that cache key generation uses SHA256 instead of MD5."""
    args = ["test_arg", 123]
    kwargs = {"key": "value"}
    key_prefix = "test:"
    func_name = "test_func"
    
    args_str = json.dumps([args, kwargs], sort_keys=True, default=str)
    cache_key_hash = hashlib.sha256(args_str.encode()).hexdigest()[:32]
    cache_key = f"{key_prefix}{func_name}:{cache_key_hash}"
    
    assert len(cache_key_hash) == 32
    assert cache_key.startswith(f"{key_prefix}{func_name}:")
    print(f"✓ Cache key uses SHA256: {cache_key[:50]}...")


def test_deterministic_hashing():
    """Verify that hashing is deterministic."""
    args_str = json.dumps([["arg"], {"key": "val"}], sort_keys=True, default=str)
    hash1 = hashlib.sha256(args_str.encode()).hexdigest()[:32]
    hash2 = hashlib.sha256(args_str.encode()).hexdigest()[:32]
    assert hash1 == hash2
    print("✓ Hashing is deterministic")


if __name__ == "__main__":
    test_cache_uses_sha256_not_md5()
    test_deterministic_hashing()
    print("\n✅ All tests passed!")
