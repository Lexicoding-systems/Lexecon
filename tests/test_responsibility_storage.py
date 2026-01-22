"""Tests for Responsibility Storage."""

import os
import tempfile
from datetime import datetime, timezone

import pytest

from lexecon.responsibility.storage import ResponsibilityStorage
from lexecon.responsibility.tracker import (
    DecisionMaker,
    ResponsibilityLevel,
    ResponsibilityRecord,
)


class TestResponsibilityStorage:
    """Tests for ResponsibilityStorage class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def storage(self, temp_db):
        """Create storage instance."""
        return ResponsibilityStorage(temp_db)

    def test_initialization(self, storage, temp_db):
        """Test storage initialization."""
        assert storage.db_path == temp_db
        assert os.path.exists(temp_db)

    def test_save_and_load_record(self, storage):
        """Test saving and loading a record."""
        record = ResponsibilityRecord(
            record_id="rec_1",
            decision_id="dec_1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_maker=DecisionMaker.HUMAN_OPERATOR,
            responsible_party="alice@example.com",
            role="Operator",
            reasoning="Test decision",
            confidence=0.9,
            responsibility_level=ResponsibilityLevel.FULL,
        )

        storage.save_record(record)

        loaded = storage.get_record("rec_1")
        assert loaded is not None
        assert loaded["responsible_party"] == "alice@example.com"

    def test_get_records_by_decision(self, storage):
        """Test getting all records for a decision."""
        # Save multiple records for same decision
        for i in range(3):
            record = ResponsibilityRecord(
                record_id=f"rec_{i}",
                decision_id="dec_shared",
                timestamp=datetime.now(timezone.utc).isoformat(),
                decision_maker=DecisionMaker.HUMAN_OPERATOR,
                responsible_party=f"user{i}@example.com",
                role="Operator",
                reasoning=f"Decision {i}",
                confidence=0.9,
                responsibility_level=ResponsibilityLevel.FULL,
            )
            storage.save_record(record)

        records = storage.get_records_by_decision("dec_shared")
        assert len(records) == 3

    def test_get_records_by_party(self, storage):
        """Test getting records by responsible party."""
        record = ResponsibilityRecord(
            record_id="rec_party",
            decision_id="dec_party",
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_maker=DecisionMaker.HUMAN_SUPERVISOR,
            responsible_party="supervisor@example.com",
            role="Supervisor",
            reasoning="Supervised decision",
            confidence=0.95,
            responsibility_level=ResponsibilityLevel.FULL,
        )

        storage.save_record(record)

        records = storage.get_records_by_party("supervisor@example.com")
        assert len(records) >= 1

    def test_get_all_records(self, storage):
        """Test getting all records."""
        # Save some records
        for i in range(5):
            record = ResponsibilityRecord(
                record_id=f"rec_all_{i}",
                decision_id=f"dec_{i}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                decision_maker=DecisionMaker.AI_SYSTEM,
                responsible_party="system",
                role="AI",
                reasoning=f"Decision {i}",
                confidence=0.9,
                responsibility_level=ResponsibilityLevel.AUTOMATED,
            )
            storage.save_record(record)

        all_records = storage.get_all_records()
        assert len(all_records) >= 5


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

    def test_get_nonexistent_record(self, temp_db):
        """Test getting record that doesn't exist."""
        storage = ResponsibilityStorage(temp_db)
        record = storage.get_record("nonexistent")
        assert record is None

    def test_get_records_empty_database(self, temp_db):
        """Test getting records from empty database."""
        storage = ResponsibilityStorage(temp_db)
        records = storage.get_all_records()
        assert records == []

    def test_get_records_by_nonexistent_decision(self, temp_db):
        """Test querying nonexistent decision."""
        storage = ResponsibilityStorage(temp_db)
        records = storage.get_records_by_decision("nonexistent")
        assert records == []
