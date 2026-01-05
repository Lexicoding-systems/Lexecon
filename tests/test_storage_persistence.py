"""Tests for ledger persistence storage."""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from lexecon.ledger.chain import LedgerChain, LedgerEntry
from lexecon.storage.persistence import LedgerStorage


@pytest.fixture
def temp_db():
    """Create temporary database for tests."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def storage(temp_db):
    """Create storage instance with temp database."""
    return LedgerStorage(db_path=temp_db)


@pytest.fixture
def sample_entry():
    """Create a sample ledger entry."""
    return LedgerEntry(
        entry_id="entry_test_123",
        event_type="test_event",
        data={"key": "value"},
        previous_hash="prev_hash_abc",
        timestamp=datetime.now(timezone.utc).isoformat()
    )


class TestLedgerStorage:
    """Tests for LedgerStorage class."""

    def test_init_creates_database(self, temp_db):
        """Test storage initialization creates database."""
        storage = LedgerStorage(db_path=temp_db)

        # Database file should exist
        assert os.path.exists(temp_db)

        # Tables should be created
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "ledger_entries" in tables
        assert "ledger_metadata" in tables

        conn.close()

    def test_save_entry(self, storage, sample_entry):
        """Test saving a ledger entry."""
        storage.save_entry(sample_entry)

        # Entry should be saved
        import sqlite3
        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ledger_entries WHERE entry_id = ?", (sample_entry.entry_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == sample_entry.entry_id  # entry_id
        assert row[1] == sample_entry.event_type  # event_type

        conn.close()

    def test_load_all_entries(self, storage):
        """Test retrieving all entries."""
        # Create multiple entries
        for i in range(3):
            entry = LedgerEntry(
                entry_id=f"entry_{i}",
                event_type="test",
                data={"index": i},
                previous_hash=f"prev_{i}",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            storage.save_entry(entry)

        entries = storage.load_all_entries()

        assert len(entries) == 3
        assert all(isinstance(e, LedgerEntry) for e in entries)

    def test_get_entries_by_type(self, storage):
        """Test filtering entries by event type."""
        # Create entries with different types
        storage.save_entry(LedgerEntry(
            entry_id="e1",
            event_type="decision",
            data={},
            previous_hash="prev",
            timestamp=datetime.now(timezone.utc).isoformat()
        ))
        storage.save_entry(LedgerEntry(
            entry_id="e2",
            event_type="policy",
            data={},
            previous_hash="prev",
            timestamp=datetime.now(timezone.utc).isoformat()
        ))
        storage.save_entry(LedgerEntry(
            entry_id="e3",
            event_type="decision",
            data={},
            previous_hash="prev",
            timestamp=datetime.now(timezone.utc).isoformat()
        ))

        decisions = storage.get_entries_by_type("decision")

        assert len(decisions) == 2
        assert all(e.event_type == "decision" for e in decisions)

    def test_get_entry_count(self, storage):
        """Test counting total entries."""
        assert storage.get_entry_count() == 0

        # Add some entries
        for i in range(5):
            storage.save_entry(LedgerEntry(
                entry_id=f"e{i}",
                event_type="test",
                data={},
                previous_hash="prev",
                timestamp=datetime.now(timezone.utc).isoformat()
            ))

        assert storage.get_entry_count() == 5

    def test_get_latest_hash(self, storage, sample_entry):
        """Test getting the latest hash."""
        # Initially None
        assert storage.get_latest_hash() is None

        # Save entry
        storage.save_entry(sample_entry)

        # Should return the entry hash
        latest_hash = storage.get_latest_hash()
        assert latest_hash is not None

    def test_verify_chain_integrity_empty(self, storage):
        """Test verifying empty chain integrity."""
        # Empty chain should be valid
        assert storage.verify_chain_integrity() is True

    def test_get_statistics(self, storage):
        """Test getting storage statistics."""
        # Add some entries
        for i in range(5):
            storage.save_entry(LedgerEntry(
                entry_id=f"e{i}",
                event_type="test" if i % 2 == 0 else "other",
                data={},
                previous_hash="prev",
                timestamp=datetime.now(timezone.utc).isoformat()
            ))

        stats = storage.get_statistics()

        assert "total_entries" in stats
        assert stats["total_entries"] == 5

    def test_integration_with_ledger_chain(self, temp_db):
        """Test integration with LedgerChain."""
        # Create ledger and append entries
        ledger = LedgerChain()
        ledger.append("event1", {"data": 1})
        ledger.append("event2", {"data": 2})

        # Save to storage
        storage = LedgerStorage(db_path=temp_db)
        for entry in ledger.entries:
            storage.save_entry(entry)

        # Verify retrieval
        assert storage.get_entry_count() == len(ledger.entries)

        # Verify we can reconstruct the chain
        loaded_entries = storage.load_all_entries()
        assert len(loaded_entries) == len(ledger.entries)

    def test_empty_database(self, storage):
        """Test operations on empty database."""
        assert storage.get_entry_count() == 0
        assert storage.load_all_entries() == []
        assert storage.get_latest_hash() is None
        assert storage.get_entries_by_type("any") == []

    def test_hash_mismatch_detection_on_load(self, storage, temp_db):
        """Test that hash mismatches are detected when loading entries."""
        import sqlite3

        # Create an entry with incorrect hash
        entry = LedgerEntry(
            entry_id="tampered",
            event_type="test",
            data={"test": "data"},
            previous_hash="prev",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Save entry normally
        storage.save_entry(entry)

        # Tamper with the stored hash directly in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ledger_entries
            SET entry_hash = 'tampered_hash'
            WHERE entry_id = ?
        """, (entry.entry_id,))
        conn.commit()
        conn.close()

        # Loading should detect mismatch
        with pytest.raises(ValueError, match="Hash mismatch"):
            storage.load_all_entries()

    def test_hash_mismatch_detection_by_type(self, storage, temp_db):
        """Test that hash mismatches are detected when loading by type."""
        import sqlite3

        # Create an entry
        entry = LedgerEntry(
            entry_id="tampered2",
            event_type="testtype",
            data={"test": "data"},
            previous_hash="prev",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Save entry normally
        storage.save_entry(entry)

        # Tamper with the stored hash
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ledger_entries
            SET entry_hash = 'bad_hash'
            WHERE entry_id = ?
        """, (entry.entry_id,))
        conn.commit()
        conn.close()

        # Loading by type should detect mismatch
        with pytest.raises(ValueError, match="Hash mismatch"):
            storage.get_entries_by_type("testtype")

    def test_verify_chain_integrity_with_corruption(self, storage, temp_db):
        """Test integrity verification detects corruption."""
        import sqlite3

        # Add entries
        for i in range(3):
            entry = LedgerEntry(
                entry_id=f"entry_{i}",
                event_type="test",
                data={"index": i},
                previous_hash=f"prev_{i}",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            storage.save_entry(entry)

        # Corrupt one entry's hash
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ledger_entries
            SET entry_hash = 'corrupted'
            WHERE entry_id = 'entry_1'
        """)
        conn.commit()
        conn.close()

        # Integrity check should fail
        is_valid = storage.verify_chain_integrity()
        assert is_valid is False

    def test_export_to_json(self, storage, temp_db):
        """Test exporting ledger to JSON file."""
        import json
        import os

        # Add some entries
        for i in range(3):
            entry = LedgerEntry(
                entry_id=f"export_entry_{i}",
                event_type="test",
                data={"index": i},
                previous_hash=f"prev_{i}",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            storage.save_entry(entry)

        # Export to JSON
        output_path = os.path.join(os.path.dirname(temp_db), "export.json")
        storage.export_to_json(output_path)

        # Verify export file exists and has correct structure
        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert "exported_at" in data
        assert "total_entries" in data
        assert data["total_entries"] == 3
        assert "entries" in data
        assert len(data["entries"]) == 3

        # Cleanup
        os.unlink(output_path)
