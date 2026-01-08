"""Tests for capability tokens."""

from datetime import datetime, timedelta

import pytest

from lexecon.capability.tokens import CapabilityToken, CapabilityTokenStore


class TestCapabilityToken:
    """Tests for CapabilityToken class."""

    def test_create_token(self):
        """Test creating a capability token."""
        token = CapabilityToken.create(
            action="search", tool="web_search", policy_version_hash="abc123"
        )

        assert token.token_id.startswith("tok_")
        assert len(token.token_id) == 20  # "tok_" + 16 hex chars
        assert token.scope["action"] == "search"
        assert token.scope["tool"] == "web_search"
        assert token.policy_version_hash == "abc123"
        assert token.granted_at is not None
        assert token.expiry > token.granted_at

    def test_create_token_with_custom_ttl(self):
        """Test creating token with custom TTL."""
        token = CapabilityToken.create(
            action="write", tool="database", policy_version_hash="xyz789", ttl_minutes=10
        )

        # Token should expire in 10 minutes
        expected_expiry = datetime.utcnow() + timedelta(minutes=10)
        time_diff = abs((token.expiry - expected_expiry).total_seconds())
        assert time_diff < 2  # Allow 2 seconds tolerance

    def test_token_is_valid_when_not_expired(self):
        """Test that non-expired token is valid."""
        token = CapabilityToken.create(
            action="read", tool="file_system", policy_version_hash="hash1", ttl_minutes=5
        )

        assert token.is_valid() is True

    def test_token_is_invalid_when_expired(self):
        """Test that expired token is invalid."""
        # Create token that expires immediately
        now = datetime.utcnow()
        token = CapabilityToken(
            token_id="tok_expired123",
            scope={"action": "read", "tool": "file_system"},
            expiry=now - timedelta(minutes=1),  # Already expired
            policy_version_hash="hash1",
            granted_at=now - timedelta(minutes=10),
        )

        assert token.is_valid() is False

    def test_token_is_authorized_for_matching_action_and_tool(self):
        """Test authorization check with matching action and tool."""
        token = CapabilityToken.create(
            action="search", tool="web_search", policy_version_hash="hash1"
        )

        assert token.is_authorized_for("search", "web_search") is True

    def test_token_not_authorized_for_different_action(self):
        """Test authorization check fails with different action."""
        token = CapabilityToken.create(
            action="search", tool="web_search", policy_version_hash="hash1"
        )

        assert token.is_authorized_for("write", "web_search") is False

    def test_token_not_authorized_for_different_tool(self):
        """Test authorization check fails with different tool."""
        token = CapabilityToken.create(
            action="search", tool="web_search", policy_version_hash="hash1"
        )

        assert token.is_authorized_for("search", "database") is False

    def test_expired_token_not_authorized(self):
        """Test that expired token is not authorized even with correct scope."""
        now = datetime.utcnow()
        token = CapabilityToken(
            token_id="tok_expired456",
            scope={"action": "read", "tool": "file_system"},
            expiry=now - timedelta(minutes=1),  # Expired
            policy_version_hash="hash1",
            granted_at=now - timedelta(minutes=10),
        )

        assert token.is_authorized_for("read", "file_system") is False

    def test_token_serialization(self):
        """Test token serialization to dict."""
        token = CapabilityToken.create(
            action="delete", tool="admin_panel", policy_version_hash="hash123"
        )
        token.signature = "test_signature"

        data = token.to_dict()

        assert data["token_id"] == token.token_id
        assert data["scope"]["action"] == "delete"
        assert data["scope"]["tool"] == "admin_panel"
        assert data["policy_version_hash"] == "hash123"
        assert data["signature"] == "test_signature"
        assert "expiry" in data
        assert "granted_at" in data

    def test_token_deserialization(self):
        """Test token deserialization from dict."""
        now = datetime.utcnow()
        expiry = now + timedelta(minutes=5)

        data = {
            "token_id": "tok_test123456789",
            "scope": {"action": "update", "tool": "config"},
            "expiry": expiry.isoformat(),
            "policy_version_hash": "hash999",
            "granted_at": now.isoformat(),
            "signature": "sig_abc",
        }

        token = CapabilityToken.from_dict(data)

        assert token.token_id == "tok_test123456789"
        assert token.scope["action"] == "update"
        assert token.scope["tool"] == "config"
        assert token.policy_version_hash == "hash999"
        assert token.signature == "sig_abc"
        assert isinstance(token.expiry, datetime)
        assert isinstance(token.granted_at, datetime)

    def test_token_serialization_roundtrip(self):
        """Test that serialization and deserialization preserve token data."""
        original = CapabilityToken.create(
            action="execute", tool="script_runner", policy_version_hash="hashABC"
        )
        original.signature = "test_sig_123"

        # Serialize and deserialize
        data = original.to_dict()
        restored = CapabilityToken.from_dict(data)

        assert restored.token_id == original.token_id
        assert restored.scope == original.scope
        assert restored.policy_version_hash == original.policy_version_hash
        assert restored.signature == original.signature
        # Time comparison with tolerance
        assert abs((restored.expiry - original.expiry).total_seconds()) < 1
        assert abs((restored.granted_at - original.granted_at).total_seconds()) < 1

    def test_token_deserialization_without_signature(self):
        """Test deserialization when signature is not present."""
        now = datetime.utcnow()
        data = {
            "token_id": "tok_nosig",
            "scope": {"action": "read", "tool": "api"},
            "expiry": (now + timedelta(minutes=5)).isoformat(),
            "policy_version_hash": "hash1",
            "granted_at": now.isoformat(),
        }

        token = CapabilityToken.from_dict(data)
        assert token.signature is None

    def test_different_tokens_have_unique_ids(self):
        """Test that multiple tokens get unique IDs."""
        tokens = [CapabilityToken.create("action", "tool", "hash") for _ in range(100)]

        token_ids = [t.token_id for t in tokens]
        assert len(token_ids) == len(set(token_ids))  # All unique


class TestCapabilityTokenStore:
    """Tests for CapabilityTokenStore class."""

    def test_store_initialization(self):
        """Test token store initialization."""
        store = CapabilityTokenStore()
        assert len(store.tokens) == 0

    def test_store_token(self):
        """Test storing a token."""
        store = CapabilityTokenStore()
        token = CapabilityToken.create("read", "api", "hash1")

        store.store(token)

        assert len(store.tokens) == 1
        assert token.token_id in store.tokens

    def test_get_existing_token(self):
        """Test retrieving an existing token."""
        store = CapabilityTokenStore()
        token = CapabilityToken.create("write", "database", "hash2")
        store.store(token)

        retrieved = store.get(token.token_id)

        assert retrieved is not None
        assert retrieved.token_id == token.token_id
        assert retrieved.scope == token.scope

    def test_get_nonexistent_token(self):
        """Test retrieving a token that doesn't exist."""
        store = CapabilityTokenStore()

        result = store.get("tok_nonexistent")

        assert result is None

    def test_verify_valid_token(self):
        """Test verifying a valid token with correct scope."""
        store = CapabilityTokenStore()
        token = CapabilityToken.create("search", "web_search", "hash3")
        store.store(token)

        is_valid = store.verify(token.token_id, "search", "web_search")

        assert is_valid is True

    def test_verify_token_wrong_action(self):
        """Test verification fails with wrong action."""
        store = CapabilityTokenStore()
        token = CapabilityToken.create("read", "file", "hash4")
        store.store(token)

        is_valid = store.verify(token.token_id, "write", "file")

        assert is_valid is False

    def test_verify_token_wrong_tool(self):
        """Test verification fails with wrong tool."""
        store = CapabilityTokenStore()
        token = CapabilityToken.create("execute", "script", "hash5")
        store.store(token)

        is_valid = store.verify(token.token_id, "execute", "command")

        assert is_valid is False

    def test_verify_nonexistent_token(self):
        """Test verification fails for non-existent token."""
        store = CapabilityTokenStore()

        is_valid = store.verify("tok_fake123", "any", "any")

        assert is_valid is False

    def test_verify_expired_token(self):
        """Test verification fails for expired token."""
        store = CapabilityTokenStore()
        now = datetime.utcnow()
        expired_token = CapabilityToken(
            token_id="tok_expired999",
            scope={"action": "read", "tool": "api"},
            expiry=now - timedelta(minutes=1),
            policy_version_hash="hash6",
            granted_at=now - timedelta(minutes=10),
        )
        store.store(expired_token)

        is_valid = store.verify(expired_token.token_id, "read", "api")

        assert is_valid is False

    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        store = CapabilityTokenStore()
        now = datetime.utcnow()

        # Create valid token
        valid_token = CapabilityToken.create("read", "api", "hash7")
        store.store(valid_token)

        # Create expired tokens
        for i in range(3):
            expired = CapabilityToken(
                token_id=f"tok_exp{i}",
                scope={"action": "write", "tool": "db"},
                expiry=now - timedelta(minutes=i + 1),
                policy_version_hash="hash8",
                granted_at=now - timedelta(minutes=10),
            )
            store.store(expired)

        # Should have 4 tokens total
        assert len(store.tokens) == 4

        # Cleanup expired
        removed_count = store.cleanup_expired()

        # Should remove 3 expired tokens
        assert removed_count == 3
        assert len(store.tokens) == 1
        assert valid_token.token_id in store.tokens

    def test_cleanup_with_no_expired_tokens(self):
        """Test cleanup when there are no expired tokens."""
        store = CapabilityTokenStore()

        # Create only valid tokens
        for i in range(5):
            token = CapabilityToken.create(f"action{i}", "tool", f"hash{i}")
            store.store(token)

        removed_count = store.cleanup_expired()

        assert removed_count == 0
        assert len(store.tokens) == 5

    def test_cleanup_empty_store(self):
        """Test cleanup on empty store."""
        store = CapabilityTokenStore()

        removed_count = store.cleanup_expired()

        assert removed_count == 0

    def test_store_multiple_tokens(self):
        """Test storing multiple tokens."""
        store = CapabilityTokenStore()
        tokens = []

        for i in range(10):
            token = CapabilityToken.create(f"action{i}", f"tool{i}", f"hash{i}")
            tokens.append(token)
            store.store(token)

        assert len(store.tokens) == 10

        # Verify all can be retrieved
        for token in tokens:
            retrieved = store.get(token.token_id)
            assert retrieved is not None
            assert retrieved.token_id == token.token_id

    def test_store_overwrites_existing_token(self):
        """Test that storing same token ID overwrites."""
        store = CapabilityTokenStore()
        token1 = CapabilityToken.create("read", "api", "hash1")
        store.store(token1)

        # Create new token with same ID
        now = datetime.utcnow()
        token2 = CapabilityToken(
            token_id=token1.token_id,
            scope={"action": "write", "tool": "db"},
            expiry=now + timedelta(minutes=10),
            policy_version_hash="hash2",
            granted_at=now,
        )
        store.store(token2)

        # Should only have 1 token
        assert len(store.tokens) == 1

        # Should have the new token's scope
        retrieved = store.get(token1.token_id)
        assert retrieved.scope["action"] == "write"
        assert retrieved.policy_version_hash == "hash2"


class TestTokenEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_token_with_zero_ttl(self):
        """Test token creation with zero TTL."""
        token = CapabilityToken.create("action", "tool", "hash", ttl_minutes=0)

        # Should be expired immediately
        assert token.is_valid() is False

    def test_token_with_negative_ttl(self):
        """Test token creation with negative TTL."""
        token = CapabilityToken.create("action", "tool", "hash", ttl_minutes=-5)

        # Should be expired
        assert token.is_valid() is False

    def test_token_scope_with_additional_fields(self):
        """Test token scope can contain additional fields."""
        now = datetime.utcnow()
        token = CapabilityToken(
            token_id="tok_extra",
            scope={
                "action": "read",
                "tool": "api",
                "resource": "/users/123",
                "method": "GET",
            },
            expiry=now + timedelta(minutes=5),
            policy_version_hash="hash1",
            granted_at=now,
        )

        # Basic authorization should still work
        assert token.is_authorized_for("read", "api") is True
        # Extra fields preserved
        assert token.scope["resource"] == "/users/123"
        assert token.scope["method"] == "GET"

    def test_token_with_empty_scope(self):
        """Test token with minimal scope."""
        now = datetime.utcnow()
        token = CapabilityToken(
            token_id="tok_empty",
            scope={},
            expiry=now + timedelta(minutes=5),
            policy_version_hash="hash1",
            granted_at=now,
        )

        # Should not authorize anything
        assert token.is_authorized_for("action", "tool") is False

    def test_very_long_ttl(self):
        """Test token with very long TTL."""
        token = CapabilityToken.create("action", "tool", "hash", ttl_minutes=525600)  # 1 year

        assert token.is_valid() is True

        # Expiry should be about 1 year from now
        expected = datetime.utcnow() + timedelta(days=365)
        time_diff = abs((token.expiry - expected).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance
