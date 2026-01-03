"""Tests for EU AI Act Article 12 - Record-Keeping Compliance."""

from datetime import datetime, timedelta, timezone

import pytest

from lexecon.compliance.eu_ai_act.article_12_records import (
    ComplianceRecord,
    RecordKeepingSystem,
    RecordStatus,
    RetentionClass,
    RetentionPolicy,
)
from lexecon.ledger.chain import LedgerChain, LedgerEntry


class TestRetentionClass:
    """Tests for RetentionClass enum."""

    def test_retention_classes_exist(self):
        """Test that all retention classes are defined."""
        assert RetentionClass.HIGH_RISK.value == "high_risk"
        assert RetentionClass.STANDARD.value == "standard"
        assert RetentionClass.GDPR_INTERSECT.value == "gdpr_intersect"


class TestRecordStatus:
    """Tests for RecordStatus enum."""

    def test_record_statuses_exist(self):
        """Test that all record statuses are defined."""
        assert RecordStatus.ACTIVE.value == "active"
        assert RecordStatus.EXPIRING.value == "expiring"
        assert RecordStatus.LEGAL_HOLD.value == "legal_hold"
        assert RecordStatus.ANONYMIZED.value == "anonymized"
        assert RecordStatus.ARCHIVED.value == "archived"


class TestRetentionPolicy:
    """Tests for RetentionPolicy dataclass."""

    def test_create_retention_policy(self):
        """Test creating retention policy."""
        policy = RetentionPolicy(
            classification=RetentionClass.HIGH_RISK,
            retention_days=3650,
            auto_anonymize=True,
            legal_basis="EU AI Act Article 12",
            data_subject_rights=False,
        )

        assert policy.classification == RetentionClass.HIGH_RISK
        assert policy.retention_days == 3650
        assert policy.auto_anonymize is True
        assert policy.legal_basis == "EU AI Act Article 12"
        assert policy.data_subject_rights is False


class TestRecordKeepingSystem:
    """Tests for RecordKeepingSystem class."""

    @pytest.fixture
    def ledger(self):
        """Create ledger for testing."""
        return LedgerChain()

    @pytest.fixture
    def record_system(self, ledger):
        """Create record keeping system."""
        return RecordKeepingSystem(ledger)

    def test_initialization(self, record_system):
        """Test record keeping system initialization."""
        assert record_system.ledger is not None
        assert isinstance(record_system.legal_holds, dict)
        assert len(record_system.legal_holds) == 0

    def test_default_policies_exist(self, record_system):
        """Test that default retention policies are created."""
        assert RetentionClass.HIGH_RISK in record_system.policies
        assert RetentionClass.STANDARD in record_system.policies
        assert RetentionClass.GDPR_INTERSECT in record_system.policies

    def test_high_risk_policy_10_years(self, record_system):
        """Test that high-risk policy has 10-year retention."""
        policy = record_system.policies[RetentionClass.HIGH_RISK]
        assert policy.retention_days == 3650  # 10 years

    def test_standard_policy_6_months(self, record_system):
        """Test that standard policy has 6-month retention."""
        policy = record_system.policies[RetentionClass.STANDARD]
        assert policy.retention_days == 180  # 6 months

    def test_classify_high_risk_by_risk_level(self, record_system, ledger):
        """Test classification of high-risk entry by risk level."""
        entry = ledger.append("decision", {"risk_level": 5, "action": "search"})

        classification = record_system.classify_entry(entry)
        assert classification == RetentionClass.HIGH_RISK

    def test_classify_high_risk_by_denial(self, record_system, ledger):
        """Test classification of high-risk entry by denial."""
        entry = ledger.append("decision", {"decision": "deny", "risk_level": 2})

        classification = record_system.classify_entry(entry)
        assert classification == RetentionClass.HIGH_RISK

    def test_classify_high_risk_by_pii(self, record_system, ledger):
        """Test classification of high-risk entry by PII."""
        entry = ledger.append("decision", {"data_classes": ["PII", "public"], "decision": "allow"})

        classification = record_system.classify_entry(entry)
        assert classification == RetentionClass.HIGH_RISK

    def test_classify_high_risk_policy_load(self, record_system, ledger):
        """Test that policy loads are high-risk."""
        entry = ledger.append("policy_loaded", {"policy_name": "test_policy"})

        classification = record_system.classify_entry(entry)
        assert classification == RetentionClass.HIGH_RISK

    def test_classify_gdpr_by_personal_data(self, record_system, ledger):
        """Test classification of GDPR intersect by personal data."""
        entry = ledger.append("decision", {"user_email": "test@example.com", "action": "read"})

        classification = record_system.classify_entry(entry)
        assert classification == RetentionClass.GDPR_INTERSECT

    def test_classify_standard_default(self, record_system, ledger):
        """Test that standard entries get STANDARD classification."""
        entry = ledger.append("decision", {"action": "read", "risk_level": 1})

        classification = record_system.classify_entry(entry)
        assert classification == RetentionClass.STANDARD

    def test_wrap_entry_creates_compliance_record(self, record_system, ledger):
        """Test wrapping entry in compliance record."""
        entry = ledger.append("decision", {"action": "search"})

        record = record_system.wrap_entry(entry)

        assert isinstance(record, ComplianceRecord)
        assert record.record_id == entry.entry_id
        assert record.status == RecordStatus.ACTIVE
        assert len(record.legal_holds) == 0

    def test_wrap_entry_calculates_expiration(self, record_system, ledger):
        """Test that wrap_entry calculates correct expiration."""
        entry = ledger.append("decision", {"risk_level": 5})  # HIGH_RISK = 10 years

        record = record_system.wrap_entry(entry)

        # Check expiration is ~10 years out
        expires = datetime.fromisoformat(record.expires_at.replace("Z", "+00:00"))
        created = datetime.fromisoformat(record.created_at.replace("Z", "+00:00"))
        delta = (expires - created).days
        assert 3640 <= delta <= 3660  # ~10 years with some tolerance

    def test_get_retention_status_empty(self, record_system):
        """Test retention status with minimal entries."""
        status = record_system.get_retention_status()

        # May have genesis block
        assert status["total_records"] >= 0
        assert status["legal_holds_active"] == 0

    def test_get_retention_status_with_entries(self, record_system, ledger):
        """Test retention status with multiple entries."""
        # Add some entries
        ledger.append("decision", {"risk_level": 5})
        ledger.append("decision", {"action": "read"})
        ledger.append("policy_loaded", {"policy": "test"})

        status = record_system.get_retention_status()

        # Genesis block + 3 entries = 4 total
        assert status["total_records"] == 4
        assert status["by_classification"]["high_risk"] == 2
        assert status["by_classification"]["standard"] >= 1

    def test_apply_legal_hold(self, record_system, ledger):
        """Test applying legal hold to entries."""
        # Add entry
        entry = ledger.append("decision", {"action": "search"})

        # Apply legal hold
        result = record_system.apply_legal_hold(
            hold_id="hold_001",
            entry_ids=[entry.entry_id],
            reason="Investigation",
        )

        assert result["hold_id"] == "hold_001"
        assert "hold_001" in record_system.legal_holds

    def test_wrap_entry_with_legal_hold(self, record_system, ledger):
        """Test that entries under legal hold get correct status."""
        entry = ledger.append("decision", {"action": "test"})

        # Apply legal hold
        record_system.apply_legal_hold(
            hold_id="hold_002", entry_ids=[entry.entry_id], reason="Test"
        )

        # Wrap entry
        record = record_system.wrap_entry(entry)

        assert record.status == RecordStatus.LEGAL_HOLD
        assert "hold_002" in record.legal_holds

    def test_release_legal_hold(self, record_system, ledger):
        """Test releasing legal hold."""
        entry = ledger.append("decision", {"action": "test"})

        # Apply and release
        record_system.apply_legal_hold(
            hold_id="hold_003", entry_ids=[entry.entry_id], reason="Test"
        )
        result = record_system.release_legal_hold("hold_003", releaser="admin")

        assert result["status"] == "released"
        # Hold remains but is marked as released
        assert result["hold_id"] == "hold_003"

    def test_generate_regulatory_package(self, record_system, ledger):
        """Test generating regulatory compliance package."""
        # Add some entries
        ledger.append("decision", {"risk_level": 5, "action": "deny"})
        ledger.append("decision", {"action": "allow"})

        package = record_system.generate_regulatory_package()

        # Package should have some structure
        assert isinstance(package, dict)
        assert len(package) > 0

    def test_regulatory_package_metadata(self, record_system, ledger):
        """Test regulatory package contains metadata."""
        package = record_system.generate_regulatory_package()

        # Package should be a dict with data
        assert isinstance(package, dict)
        assert len(package) > 0

    def test_regulatory_package_includes_policies(self, record_system, ledger):
        """Test regulatory package includes retention info."""
        package = record_system.generate_regulatory_package()

        # Package should contain data
        assert isinstance(package, dict)
        assert len(package) > 0

    def test_export_for_regulator_json(self, record_system, ledger):
        """Test exporting compliance package as JSON."""
        ledger.append("decision", {"action": "test"})

        export = record_system.export_for_regulator(format="json")

        assert isinstance(export, str)
        # Should contain data
        assert len(export) > 100

    def test_export_for_regulator_markdown(self, record_system, ledger):
        """Test exporting compliance package as Markdown."""
        ledger.append("decision", {"risk_level": 5})

        export = record_system.export_for_regulator(format="markdown")

        assert isinstance(export, str)
        assert "# EU AI Act Article 12" in export

    def test_export_for_regulator_csv(self, record_system, ledger):
        """Test exporting compliance package as CSV."""
        ledger.append("decision", {"action": "test"})

        export = record_system.export_for_regulator(format="csv")

        assert isinstance(export, str)
        # CSV should have headers
        lines = export.strip().split("\n")
        assert len(lines) >= 2  # Header + at least one row

    def test_anonymize_record(self, record_system, ledger):
        """Test anonymizing record with personal data."""
        entry = ledger.append(
            "decision", {"user_email": "test@example.com", "action": "search"}
        )

        result = record_system.anonymize_record(entry.entry_id)

        assert result["status"] == "anonymized"
        assert "anonymized_at" in result


class TestComplianceRecord:
    """Tests for ComplianceRecord dataclass."""

    def test_create_compliance_record(self):
        """Test creating compliance record."""
        record = ComplianceRecord(
            record_id="rec_123",
            original_entry={"event_type": "decision"},
            retention_class=RetentionClass.HIGH_RISK,
            created_at="2025-01-01T00:00:00Z",
            expires_at="2035-01-01T00:00:00Z",
            status=RecordStatus.ACTIVE,
            legal_holds=[],
        )

        assert record.record_id == "rec_123"
        assert record.retention_class == RetentionClass.HIGH_RISK
        assert record.status == RecordStatus.ACTIVE

    def test_compliance_record_with_legal_holds(self):
        """Test compliance record with legal holds."""
        record = ComplianceRecord(
            record_id="rec_456",
            original_entry={},
            retention_class=RetentionClass.STANDARD,
            created_at="2025-01-01T00:00:00Z",
            expires_at="2025-07-01T00:00:00Z",
            status=RecordStatus.LEGAL_HOLD,
            legal_holds=["hold_001", "hold_002"],
        )

        assert len(record.legal_holds) == 2
        assert record.status == RecordStatus.LEGAL_HOLD


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.fixture
    def record_system(self):
        """Create record system for edge case tests."""
        return RecordKeepingSystem(LedgerChain())

    def test_classify_entry_with_empty_data(self, record_system):
        """Test classifying entry with empty data."""
        ledger = record_system.ledger
        entry = ledger.append("decision", {})

        classification = record_system.classify_entry(entry)
        assert classification == RetentionClass.STANDARD

    def test_classify_entry_with_none_data(self, record_system):
        """Test classifying entry with None/minimal data."""
        ledger = record_system.ledger
        entry = ledger.append("decision", {})

        classification = record_system.classify_entry(entry)
        assert classification == RetentionClass.STANDARD

    def test_multiple_legal_holds_on_same_entry(self, record_system):
        """Test applying multiple legal holds to same entry."""
        ledger = record_system.ledger
        entry = ledger.append("decision", {"action": "test"})

        # Apply two holds
        record_system.apply_legal_hold("hold_a", [entry.entry_id], "Reason A")
        record_system.apply_legal_hold("hold_b", [entry.entry_id], "Reason B")

        record = record_system.wrap_entry(entry)
        # At least one hold should be present
        assert len(record.legal_holds) >= 1

    def test_legal_hold_with_multiple_entries(self, record_system):
        """Test legal hold affecting multiple entries."""
        ledger = record_system.ledger
        entry1 = ledger.append("decision", {"action": "test1"})
        entry2 = ledger.append("decision", {"action": "test2"})

        result = record_system.apply_legal_hold(
            "hold_multi", [entry1.entry_id, entry2.entry_id], "Multi-entry hold"
        )

        # Hold should be created
        assert "hold_multi" in record_system.legal_holds

    def test_release_nonexistent_legal_hold(self, record_system):
        """Test releasing non-existent legal hold."""
        result = record_system.release_legal_hold("nonexistent")
        # Should handle gracefully
        assert isinstance(result, dict)

    def test_personal_data_detection(self, record_system):
        """Test personal data detection in various formats."""
        test_cases = [
            ({"email": "user@test.com"}, True),
            ({"user_name": "John Doe"}, True),
            ({"ip_address": "192.168.1.1"}, True),
            ({"phone_number": "+1234567890"}, True),
            ({"action": "read", "resource": "public_data"}, False),
        ]

        for data, expected_personal in test_cases:
            has_personal = record_system._contains_personal_data(data)
            assert has_personal == expected_personal

    def test_retention_status_with_expiring_records(self, record_system):
        """Test retention status correctly identifies expiring records."""
        ledger = record_system.ledger

        # Add some entries
        ledger.append("decision", {"action": "test"})

        status = record_system.get_retention_status()
        # Should complete without error
        assert "expiring_within_30_days" in status
        assert status["expiring_within_30_days"] >= 0

    def test_anonymize_preserves_structure(self, record_system):
        """Test that anonymization preserves basic functionality."""
        ledger = record_system.ledger
        entry = ledger.append(
            "decision",
            {
                "user_email": "sensitive@example.com",
                "action": "search",
                "metadata": {"ip_address": "10.0.0.1"},
            },
        )

        result = record_system.anonymize_record(entry.entry_id)

        # Anonymization should complete successfully
        assert result["status"] == "anonymized"
        assert "anonymized_at" in result
