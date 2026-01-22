"""Tests for Ledger Storage Persistence."""

import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from lexecon.ledger.chain import LedgerChain, LedgerEntry
from lexecon.storage.persistence import LedgerStorage


class TestLedgerStorage:
    """Tests for LedgerStorage class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def storage(self, temp_db):
        """Create storage instance."""
        return LedgerStorage(temp_db)

    def test_initialization(self, temp_db):
        """Test storage initialization creates database."""
        storage = LedgerStorage(temp_db)
        assert os.path.exists(temp_db)
        assert storage.db_path == temp_db

    def test_save_and_load_entry(self, storage):
        """Test saving and loading a single entry."""
        # Create a ledger and add an entry
        ledger = LedgerChain()
        entry = ledger.append("test_event", {"key": "value"})

        # Save entry
        storage.save_entry(entry)

        # Load all entries
        loaded = storage.load_all_entries()
        assert len(loaded) >= 1

        # Find our entry
        found = None
        for e in loaded:
            if e.entry_id == entry.entry_id:
                found = e
                break

        assert found is not None
        assert found.event_type == "test_event"
        assert found.data == {"key": "value"}

    def test_save_multiple_entries(self, storage):
        """Test saving multiple entries."""
        ledger = LedgerChain()

        entries = []
        for i in range(5):
            entry = ledger.append(f"event_{i}", {"index": i})
            storage.save_entry(entry)
            entries.append(entry)

        loaded = storage.load_all_entries()
        # Should have genesis + 5 entries = 6 total
        assert len(loaded) >= 5

    def test_get_entries_by_type(self, storage):
        """Test querying entries by event type."""
        ledger = LedgerChain()

        # Add different types
        ledger.append("decision", {"action": "allow"})
        storage.save_entry(ledger.entries[-1])

        ledger.append("policy_loaded", {"policy": "test"})
        storage.save_entry(ledger.entries[-1])

        ledger.append("decision", {"action": "deny"})
        storage.save_entry(ledger.entries[-1])

        # Query by type
        decisions = storage.get_entries_by_type("decision")
        assert len(decisions) == 2

        policies = storage.get_entries_by_type("policy_loaded")
        assert len(policies) == 1

    def test_get_entry_count(self, storage):
        """Test getting total entry count."""
        ledger = LedgerChain()

        initial_count = storage.get_entry_count()

        # Add entries
        for i in range(3):
            entry = ledger.append("test", {"i": i})
            storage.save_entry(entry)

        final_count = storage.get_entry_count()
        assert final_count == initial_count + 3

    def test_get_latest_hash(self, storage):
        """Test getting latest entry hash."""
        ledger = LedgerChain()

        # Save first entry
        entry1 = ledger.append("test1", {})
        storage.save_entry(entry1)

        latest1 = storage.get_latest_hash()
        assert latest1 == entry1.entry_hash

        # Save second entry
        entry2 = ledger.append("test2", {})
        storage.save_entry(entry2)

        latest2 = storage.get_latest_hash()
        assert latest2 == entry2.entry_hash

    def test_verify_chain_integrity(self, storage):
        """Test verifying chain integrity."""
        ledger = LedgerChain()

        # Add and save entries
        for i in range(5):
            entry = ledger.append("test", {"i": i})
            storage.save_entry(entry)

        # Verify integrity
        is_valid = storage.verify_chain_integrity()
        assert is_valid is True

    def test_export_to_json(self, storage, temp_db):
        """Test exporting ledger to JSON."""
        ledger = LedgerChain()

        # Add entries
        for i in range(3):
            entry = ledger.append("test", {"index": i})
            storage.save_entry(entry)

        # Export
        export_path = temp_db + ".json"
        try:
            storage.export_to_json(export_path)

            assert os.path.exists(export_path)

            # Verify JSON is valid
            with open(export_path, "r") as f:
                data = json.load(f)
                assert "entries" in data or "ledger_entries" in data or isinstance(data, list)
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_get_statistics(self, storage):
        """Test getting storage statistics."""
        ledger = LedgerChain()

        # Add various entries
        ledger.append("decision", {"action": "allow"})
        storage.save_entry(ledger.entries[-1])

        ledger.append("policy_loaded", {"policy": "test"})
        storage.save_entry(ledger.entries[-1])

        ledger.append("decision", {"action": "deny"})
        storage.save_entry(ledger.entries[-1])

        stats = storage.get_statistics()

        assert "total_entries" in stats
        assert stats["total_entries"] >= 3


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_load_from_empty_database(self, temp_db):
        """Test loading from empty database."""
        storage = LedgerStorage(temp_db)
        entries = storage.load_all_entries()
        assert entries == []

    def test_get_entries_by_nonexistent_type(self, temp_db):
        """Test querying nonexistent event type."""
        storage = LedgerStorage(temp_db)
        entries = storage.get_entries_by_type("nonexistent_type")
        assert entries == []

    def test_get_latest_hash_empty_database(self, temp_db):
        """Test getting latest hash from empty database."""
        storage = LedgerStorage(temp_db)
        latest = storage.get_latest_hash()
        assert latest is None

    def test_entry_count_empty_database(self, temp_db):
        """Test entry count on empty database."""
        storage = LedgerStorage(temp_db)
        count = storage.get_entry_count()
        assert count == 0

    def test_verify_integrity_empty_database(self, temp_db):
        """Test verifying integrity of empty database."""
        storage = LedgerStorage(temp_db)
        is_valid = storage.verify_chain_integrity()
        # Empty chain should be valid
        assert is_valid is True

    def test_reopen_database(self, temp_db):
        """Test reopening database preserves data."""
        # Create and populate
        storage1 = LedgerStorage(temp_db)
        ledger = LedgerChain()
        entry = ledger.append("test", {"data": "value"})
        storage1.save_entry(entry)

        # Close and reopen
        del storage1
        storage2 = LedgerStorage(temp_db)

        # Verify data persisted
        loaded = storage2.load_all_entries()
        assert len(loaded) >= 1

    def test_save_entry_with_complex_data(self, temp_db):
        """Test saving entry with complex nested data."""
        storage = LedgerStorage(temp_db)
        ledger = LedgerChain()

        complex_data = {
            "nested": {
                "level1": {
                    "level2": ["a", "b", "c"],
                },
            },
            "list": [1, 2, 3],
            "bool": True,
            "null": None,
        }

        entry = ledger.append("complex_test", complex_data)
        storage.save_entry(entry)

        loaded = storage.load_all_entries()
        found = None
        for e in loaded:
            if e.entry_id == entry.entry_id:
                found = e
                break

        assert found is not None
        assert found.data == complex_data
