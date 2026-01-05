"""
Tests for append-only storage adapter.
"""

import pytest
from src.lexecon.evidence.append_only_store import (
    AppendOnlyStore,
    AppendOnlyViolationError,
    AppendOnlyEvidenceStore,
)


class TestAppendOnlyStore:
    """Tests for AppendOnlyStore wrapper."""

    def test_disabled_allows_all_operations(self):
        """When disabled, store allows all operations."""
        store = AppendOnlyStore({}, enabled=False)

        # Create
        store["key1"] = "value1"
        assert store["key1"] == "value1"

        # Update
        store["key1"] = "value2"
        assert store["key1"] == "value2"

        # Delete
        del store["key1"]
        assert "key1" not in store

    def test_enabled_allows_create(self):
        """When enabled, store allows creating new keys."""
        store = AppendOnlyStore({}, enabled=True)

        store["key1"] = "value1"
        assert store["key1"] == "value1"

        store["key2"] = "value2"
        assert store["key2"] == "value2"

    def test_enabled_blocks_update(self):
        """When enabled, store blocks updates to existing keys."""
        store = AppendOnlyStore({}, enabled=True)

        store["key1"] = "value1"

        with pytest.raises(AppendOnlyViolationError) as exc:
            store["key1"] = "value2"

        assert "Cannot update" in str(exc.value)
        assert store["key1"] == "value1"  # Original value preserved

    def test_enabled_blocks_delete(self):
        """When enabled, store blocks deletes."""
        store = AppendOnlyStore({}, enabled=True)

        store["key1"] = "value1"

        with pytest.raises(AppendOnlyViolationError) as exc:
            del store["key1"]

        assert "Cannot delete" in str(exc.value)
        assert store["key1"] == "value1"  # Still exists

    def test_initial_keys_tracked(self):
        """Store tracks keys that existed at initialization."""
        underlying = {"existing": "value"}
        store = AppendOnlyStore(underlying, enabled=True)

        # Can't update existing key
        with pytest.raises(AppendOnlyViolationError):
            store["existing"] = "new_value"

        # Can create new key
        store["new"] = "new_value"
        assert store["new"] == "new_value"

    def test_enable_disableToggle(self):
        """Store can toggle append-only mode."""
        store = AppendOnlyStore({}, enabled=False)

        # Works when disabled
        store["key1"] = "value1"
        store["key1"] = "value2"

        # Enable append-only
        store.enable()
        assert store.enabled

        # Now blocks updates
        with pytest.raises(AppendOnlyViolationError):
            store["key1"] = "value3"

        # Disable again
        store.disable()
        assert not store.enabled

        # Updates work again
        store["key1"] = "value4"
        assert store["key1"] == "value4"

    def test_dict_like_methods(self):
        """Store supports dict-like methods."""
        store = AppendOnlyStore({}, enabled=True)

        store["key1"] = "value1"
        store["key2"] = "value2"

        assert len(store) == 2
        assert "key1" in store
        assert "key3" not in store
        assert store.get("key1") == "value1"
        assert store.get("key3", "default") == "default"

        assert set(store.keys()) == {"key1", "key2"}
        assert set(store.values()) == {"value1", "value2"}
        assert set(store.items()) == {("key1", "value1"), ("key2", "value2")}

    def test_update_allowed_check(self):
        """update_allowed() correctly reports permissions."""
        store = AppendOnlyStore({}, enabled=False)

        # Disabled: all updates allowed
        assert store.update_allowed("key1")

        store["key1"] = "value1"
        assert store.update_allowed("key1")

        # Enable
        store.enable()

        # Existing key not allowed
        assert not store.update_allowed("key1")

        # New key allowed
        assert store.update_allowed("key2")

    def test_delete_allowed_check(self):
        """delete_allowed() correctly reports permissions."""
        store = AppendOnlyStore({}, enabled=False)

        store["key1"] = "value1"

        # Disabled: deletes allowed
        assert store.delete_allowed("key1")

        # Enable
        store.enable()

        # Deletes not allowed
        assert not store.delete_allowed("key1")


class TestAppendOnlyEvidenceStore:
    """Tests for AppendOnlyEvidenceStore wrapper."""

    def test_wrap_evidence_service(self):
        """Can wrap an EvidenceService."""
        # Mock a simple service
        class MockEvidenceService:
            def __init__(self):
                self._artifacts = {}

        service = MockEvidenceService()
        wrapper = AppendOnlyEvidenceStore(service, enabled=False)

        assert not wrapper.enabled
        assert service._artifacts == {}

    def test_enabled_wraps_storage(self):
        """When enabled, wraps service's internal storage."""
        class MockEvidenceService:
            def __init__(self):
                self._artifacts = {}

        service = MockEvidenceService()
        wrapper = AppendOnlyEvidenceStore(service, enabled=True)

        assert wrapper.enabled
        assert isinstance(service._artifacts, AppendOnlyStore)

    def test_enable_after_init(self):
        """Can enable append-only mode after initialization."""
        class MockEvidenceService:
            def __init__(self):
                self._artifacts = {"existing": "artifact"}

        service = MockEvidenceService()
        wrapper = AppendOnlyEvidenceStore(service, enabled=False)

        # Add artifact while disabled
        service._artifacts["new"] = "artifact"

        # Enable
        wrapper.enable()
        assert wrapper.enabled

        # Now can't update existing
        artifacts_store = service._artifacts
        with pytest.raises(AppendOnlyViolationError):
            artifacts_store["new"] = "modified"

    def test_disable_after_enable(self):
        """Can disable append-only mode after enabling."""
        class MockEvidenceService:
            def __init__(self):
                self._artifacts = {}

        service = MockEvidenceService()
        wrapper = AppendOnlyEvidenceStore(service, enabled=True)

        service._artifacts["key"] = "value"

        # Disable
        wrapper.disable()
        assert not wrapper.enabled

        # Can now update
        service._artifacts["key"] = "new_value"
        assert service._artifacts["key"] == "new_value"

    def test_verify_integrity(self):
        """verify_integrity() checks artifact hashes."""

        class MockArtifact:
            def __init__(self, content, sha256_hash):
                self.content = content
                self.sha256_hash = sha256_hash

        class MockEvidenceService:
            def __init__(self):
                self._artifacts = {}

        service = MockEvidenceService()
        wrapper = AppendOnlyEvidenceStore(service, enabled=True)

        # Add artifact with correct hash
        from src.lexecon.evidence.service import compute_sha256

        content = "test content"
        correct_hash = compute_sha256(content)
        service._artifacts._store["artifact1"] = MockArtifact(content, correct_hash)

        # Integrity should pass
        assert wrapper.verify_integrity()

        # Add artifact with incorrect hash
        service._artifacts._store["artifact2"] = MockArtifact(
            "different content",
            "0" * 64  # Wrong hash
        )

        # Integrity should fail
        assert not wrapper.verify_integrity()
