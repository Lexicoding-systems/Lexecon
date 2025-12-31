"""Tests for ledger chain."""

import pytest
from lexecon.ledger.chain import LedgerChain, LedgerEntry


class TestLedgerEntry:
    """Tests for LedgerEntry."""

    def test_create_entry(self):
        """Test creating a ledger entry."""
        entry = LedgerEntry(
            entry_id="test_1",
            event_type="test_event",
            data={"key": "value"},
            timestamp="2025-01-01T00:00:00",
            previous_hash="0" * 64
        )
        assert entry.entry_id == "test_1"
        assert len(entry.entry_hash) == 64

    def test_hash_calculation(self):
        """Test hash calculation is deterministic."""
        entry1 = LedgerEntry(
            entry_id="test_1",
            event_type="test",
            data={"a": 1},
            timestamp="2025-01-01T00:00:00",
            previous_hash="0" * 64
        )
        entry2 = LedgerEntry(
            entry_id="test_1",
            event_type="test",
            data={"a": 1},
            timestamp="2025-01-01T00:00:00",
            previous_hash="0" * 64
        )
        assert entry1.entry_hash == entry2.entry_hash

    def test_different_data_different_hash(self):
        """Test different data produces different hash."""
        entry1 = LedgerEntry(
            entry_id="test_1",
            event_type="test",
            data={"a": 1},
            timestamp="2025-01-01T00:00:00",
            previous_hash="0" * 64
        )
        entry2 = LedgerEntry(
            entry_id="test_1",
            event_type="test",
            data={"a": 2},
            timestamp="2025-01-01T00:00:00",
            previous_hash="0" * 64
        )
        assert entry1.entry_hash != entry2.entry_hash


class TestLedgerChain:
    """Tests for LedgerChain."""

    def test_init(self):
        """Test ledger initialization."""
        ledger = LedgerChain()
        assert len(ledger.entries) == 1  # Genesis entry
        assert ledger.entries[0].event_type == "genesis"

    def test_append(self):
        """Test appending entries."""
        ledger = LedgerChain()
        entry = ledger.append("test_event", {"key": "value"})

        assert len(ledger.entries) == 2
        assert entry.event_type == "test_event"
        assert entry.data["key"] == "value"

    def test_chain_linkage(self):
        """Test entries are properly linked."""
        ledger = LedgerChain()

        entry1 = ledger.append("event1", {"data": 1})
        entry2 = ledger.append("event2", {"data": 2})

        # Entry2's previous_hash should equal entry1's entry_hash
        assert entry2.previous_hash == entry1.entry_hash

    def test_verify_integrity_valid(self):
        """Test integrity verification on valid chain."""
        ledger = LedgerChain()
        ledger.append("event1", {"data": 1})
        ledger.append("event2", {"data": 2})

        result = ledger.verify_integrity()
        assert result["valid"] is True
        assert result["entries_verified"] == 3  # Genesis + 2 entries

    def test_verify_integrity_tampered(self):
        """Test integrity verification detects tampering."""
        ledger = LedgerChain()
        ledger.append("event1", {"data": 1})
        entry2 = ledger.append("event2", {"data": 2})

        # Tamper with entry data
        entry2.data["data"] = 999

        result = ledger.verify_integrity()
        assert result["valid"] is False
        assert "Hash mismatch" in result["error"]

    def test_get_entry(self):
        """Test getting entry by ID."""
        ledger = LedgerChain()
        ledger.append("event1", {"data": 1})

        entry = ledger.get_entry("entry_1")
        assert entry is not None
        assert entry.event_type == "event1"

    def test_get_entries_by_type(self):
        """Test getting entries by type."""
        ledger = LedgerChain()
        ledger.append("typeA", {"data": 1})
        ledger.append("typeB", {"data": 2})
        ledger.append("typeA", {"data": 3})

        entries = ledger.get_entries_by_type("typeA")
        assert len(entries) == 2

    def test_audit_report(self):
        """Test generating audit report."""
        ledger = LedgerChain()
        ledger.append("decision", {"data": 1})
        ledger.append("policy_load", {"data": 2})

        report = ledger.generate_audit_report()
        assert report["total_entries"] == 3  # Genesis + 2
        assert report["integrity_valid"] is True
        assert "decision" in report["event_type_counts"]
        assert report["event_type_counts"]["decision"] == 1

    def test_serialization(self):
        """Test serialization and deserialization."""
        ledger1 = LedgerChain()
        ledger1.append("event1", {"data": 1})
        ledger1.append("event2", {"data": 2})

        # Serialize
        data = ledger1.to_dict()

        # Deserialize
        ledger2 = LedgerChain.from_dict(data)

        assert len(ledger2.entries) == len(ledger1.entries)
        assert ledger2.entries[-1].entry_hash == ledger1.entries[-1].entry_hash
