"""Ledger Chain - Tamper-evident audit log using hash chaining.

Each entry is cryptographically linked to previous entries.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LedgerEntry:
    """A single entry in the ledger chain."""

    entry_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    previous_hash: str
    entry_hash: str = field(init=False)

    def __post_init__(self):
        """Calculate entry hash after initialization."""
        self.entry_hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calculate deterministic hash of this entry."""
        entry_data = {
            "entry_id": self.entry_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
        }
        canonical_json = json.dumps(entry_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entry to dictionary."""
        return {
            "entry_id": self.entry_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


class LedgerChain:
    """Tamper-evident ledger using hash chaining.

    Each entry contains a hash of the previous entry, making modifications detectable.

    Supports optional persistence to SQLite for EU AI Act compliance.
    """

    def __init__(self, storage=None):
        """Initialize ledger chain.

        Args:
            storage: Optional LedgerStorage instance for persistence.
                     If provided, ledger will auto-load and auto-save.
        """
        self.storage = storage
        self.entries: List[LedgerEntry] = []

        # Load from storage if available
        if self.storage:
            loaded_entries = self.storage.load_all_entries()
            if loaded_entries:
                self.entries = loaded_entries
            else:
                self._initialize_genesis()
        else:
            self._initialize_genesis()

    def _initialize_genesis(self) -> None:
        """Create genesis entry (first entry in chain)."""
        genesis = LedgerEntry(
            entry_id="genesis",
            event_type="genesis",
            data={"message": "Lexecon ledger initialized"},
            timestamp=datetime.utcnow().isoformat(),
            previous_hash="0" * 64,  # No previous hash
        )
        self.entries.append(genesis)

        # Save to storage if available
        if self.storage:
            self.storage.save_entry(genesis)

    def append(self, event_type: str, data: Dict[str, Any]) -> LedgerEntry:
        """Append a new entry to the ledger.

        Automatically saves to storage if configured.

        Returns the created entry with its hash.
        """
        entry_id = f"entry_{len(self.entries)}"
        previous_hash = self.entries[-1].entry_hash if self.entries else "0" * 64

        entry = LedgerEntry(
            entry_id=entry_id,
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
            previous_hash=previous_hash,
        )

        self.entries.append(entry)

        # Auto-save to storage if available
        if self.storage:
            self.storage.save_entry(entry)

        return entry

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify the integrity of the entire chain.

        Returns verification result with details of any corruption.
        """
        if not self.entries:
            return {
                "valid": False,
                "error": "Empty ledger",
                "entries_checked": 0,
                "entries_verified": 0,
                "chain_intact": False,
            }

        for i, entry in enumerate(self.entries):
            # Verify entry hash
            expected_hash = entry.calculate_hash()
            if entry.entry_hash != expected_hash:
                return {
                    "valid": False,
                    "error": f"Hash mismatch at entry {i}",
                    "entry_id": entry.entry_id,
                    "entries_checked": i + 1,
                    "entries_verified": i,
                    "chain_intact": False,
                }

            # Verify chain linkage (skip genesis)
            if i > 0:
                previous_entry = self.entries[i - 1]
                if entry.previous_hash != previous_entry.entry_hash:
                    return {
                        "valid": False,
                        "error": f"Chain break at entry {i}",
                        "entry_id": entry.entry_id,
                        "entries_checked": i + 1,
                        "entries_verified": i,
                        "chain_intact": False,
                    }

        return {
            "valid": True,
            "entries_checked": len(self.entries),
            "entries_verified": len(self.entries),
            "chain_intact": True,
            "chain_head_hash": self.entries[-1].entry_hash,
        }

    def get_entry(self, entry_id_or_hash: str) -> Optional[LedgerEntry]:
        """Get entry by ID or hash."""
        for entry in self.entries:
            if entry_id_or_hash in (entry.entry_id, entry.entry_hash):
                return entry
        return None

    def get_entries_by_type(self, event_type: str) -> List[LedgerEntry]:
        """Get all entries of a specific event type."""
        return [e for e in self.entries if e.event_type == event_type]

    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate a comprehensive audit report."""
        integrity_check = self.verify_integrity()

        event_types = {}
        for entry in self.entries:
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1

        return {
            "total_entries": len(self.entries),
            "integrity_valid": integrity_check["valid"],
            "event_type_counts": event_types,
            "first_entry_timestamp": self.entries[0].timestamp if self.entries else None,
            "last_entry_timestamp": self.entries[-1].timestamp if self.entries else None,
            "chain_head_hash": self.entries[-1].entry_hash if self.entries else None,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ledger to dictionary."""
        return {"entries": [entry.to_dict() for entry in self.entries]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LedgerChain":
        """Deserialize ledger from dictionary."""
        ledger = cls.__new__(cls)
        ledger.entries = []

        for entry_data in data.get("entries", []):
            entry = LedgerEntry(
                entry_id=entry_data["entry_id"],
                event_type=entry_data["event_type"],
                data=entry_data["data"],
                timestamp=entry_data["timestamp"],
                previous_hash=entry_data["previous_hash"],
            )
            # Verify the stored hash matches calculated hash
            if entry.entry_hash != entry_data["entry_hash"]:
                raise ValueError(f"Hash mismatch in entry {entry.entry_id}")
            ledger.entries.append(entry)

        return ledger
