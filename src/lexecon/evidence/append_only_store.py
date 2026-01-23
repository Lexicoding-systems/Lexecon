"""Append-only storage adapter for evidence artifacts.

Provides an optional layer that enforces append-only semantics,
preventing updates or deletes of evidence artifacts after creation.

Feature-flagged: Must be explicitly enabled. When disabled, behaves
as pass-through to underlying storage.
"""

from typing import Any, Dict


class AppendOnlyViolationError(Exception):
    """Raised when attempting to modify or delete in append-only mode."""


class AppendOnlyStore:
    """Append-only wrapper for evidence artifact storage.

    When enabled, prevents updates and deletes of existing artifacts.
    When disabled, acts as transparent pass-through.

    Usage:
        store = AppendOnlyStore(underlying_dict, enabled=True)
        store["key"] = "value"  # OK (create)
        store["key"] = "new"    # Raises AppendOnlyViolationError
        del store["key"]        # Raises AppendOnlyViolationError
    """

    def __init__(
        self,
        underlying_store: Dict[str, Any],
        enabled: bool = False,
    ):
        """Initialize append-only store wrapper.

        Args:
            underlying_store: The actual storage dictionary
            enabled: Whether append-only enforcement is active
        """
        self._store = underlying_store
        self._enabled = enabled
        # Track which keys existed at initialization
        self._initial_keys = set(underlying_store.keys()) if enabled else set()

    @property
    def enabled(self) -> bool:
        """Check if append-only mode is enabled."""
        return self._enabled

    def enable(self):
        """Enable append-only mode."""
        if not self._enabled:
            self._enabled = True
            self._initial_keys = set(self._store.keys())

    def disable(self):
        """Disable append-only mode (acts as pass-through)."""
        self._enabled = False
        self._initial_keys = set()

    def __setitem__(self, key: str, value: Any):
        """Set item in store.

        Args:
            key: Artifact ID
            value: EvidenceArtifact

        Raises:
            AppendOnlyViolationError: If key exists and append-only enabled
        """
        if self._enabled and key in self._store:
            raise AppendOnlyViolationError(
                f"Cannot update existing artifact '{key}' in append-only mode",
            )
        self._store[key] = value

    def __getitem__(self, key: str) -> Any:
        """Get item from store."""
        return self._store[key]

    def __delitem__(self, key: str):
        """Delete item from store.

        Raises:
            AppendOnlyViolationError: If append-only enabled
        """
        if self._enabled:
            raise AppendOnlyViolationError(
                f"Cannot delete artifact '{key}' in append-only mode",
            )
        del self._store[key]

    def __contains__(self, key: str) -> bool:
        """Check if key exists in store."""
        return key in self._store

    def __len__(self) -> int:
        """Get number of items in store."""
        return len(self._store)

    def get(self, key: str, default: Any = None) -> Any:
        """Get item with default."""
        return self._store.get(key, default)

    def keys(self):
        """Get all keys."""
        return self._store.keys()

    def values(self):
        """Get all values."""
        return self._store.values()

    def items(self):
        """Get all items."""
        return self._store.items()

    def update_allowed(self, key: str) -> bool:
        """Check if update is allowed for key.

        Args:
            key: Artifact ID

        Returns:
            True if update allowed, False otherwise
        """
        if not self._enabled:
            return True
        return key not in self._store

    def delete_allowed(self, key: str) -> bool:
        """Check if delete is allowed for key.

        Args:
            key: Artifact ID

        Returns:
            True if delete allowed, False otherwise
        """
        return not self._enabled


class AppendOnlyEvidenceStore:
    """Append-only wrapper specifically for EvidenceService.

    Wraps the artifact storage dictionary and indices to enforce
    append-only semantics when enabled.
    """

    def __init__(self, evidence_service, enabled: bool = False):
        """Initialize append-only wrapper for EvidenceService.

        Args:
            evidence_service: EvidenceService instance to wrap
            enabled: Whether append-only mode is enabled
        """
        self.service = evidence_service
        self._enabled = enabled

        # Wrap the internal storage if enabled
        if enabled:
            # Replace internal dict with append-only wrapper
            self.service._artifacts = AppendOnlyStore(
                self.service._artifacts,
                enabled=True,
            )

    @property
    def enabled(self) -> bool:
        """Check if append-only mode is enabled."""
        return self._enabled

    def enable(self):
        """Enable append-only mode."""
        if not self._enabled:
            self._enabled = True
            if not isinstance(self.service._artifacts, AppendOnlyStore):
                self.service._artifacts = AppendOnlyStore(
                    self.service._artifacts,
                    enabled=True,
                )
            else:
                self.service._artifacts.enable()

    def disable(self):
        """Disable append-only mode."""
        if self._enabled:
            self._enabled = False
            if isinstance(self.service._artifacts, AppendOnlyStore):
                self.service._artifacts.disable()

    def verify_integrity(self) -> bool:
        """Verify that no artifacts have been modified.

        Returns:
            True if all artifacts match their declared hashes
        """
        artifacts = (
            self.service._artifacts._store
            if isinstance(self.service._artifacts, AppendOnlyStore)
            else self.service._artifacts
        )

        for _artifact_id, artifact in artifacts.items():
            # Recompute hash
            if hasattr(artifact, "content") and hasattr(artifact, "sha256_hash"):
                from .service import compute_sha256
                actual_hash = compute_sha256(artifact.content)
                if actual_hash != artifact.sha256_hash:
                    return False

        return True
