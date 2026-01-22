"""Tests for Decision Responsibility Tracker."""

from datetime import datetime, timezone

import pytest

from lexecon.responsibility.tracker import (
    DecisionMaker,
    ResponsibilityLevel,
    ResponsibilityRecord,
    ResponsibilityTracker,
)


class TestDecisionMaker:
    """Tests for DecisionMaker enum."""

    def test_decision_maker_values(self):
        """Test that all decision maker types are defined."""
        assert DecisionMaker.AI_SYSTEM.value == "ai_system"
        assert DecisionMaker.HUMAN_OPERATOR.value == "human_operator"
        assert DecisionMaker.HUMAN_SUPERVISOR.value == "human_supervisor"
        assert DecisionMaker.HUMAN_EXECUTIVE.value == "human_executive"
        assert DecisionMaker.DELEGATED.value == "delegated"
        assert DecisionMaker.EMERGENCY_OVERRIDE.value == "emergency_override"


class TestResponsibilityLevel:
    """Tests for ResponsibilityLevel enum."""

    def test_responsibility_levels(self):
        """Test that all responsibility levels are defined."""
        assert ResponsibilityLevel.FULL.value == "full"
        assert ResponsibilityLevel.SHARED.value == "shared"
        assert ResponsibilityLevel.SUPERVISED.value == "supervised"
        assert ResponsibilityLevel.AUTOMATED.value == "automated"


class TestResponsibilityRecord:
    """Tests for ResponsibilityRecord dataclass."""

    def test_create_responsibility_record(self):
        """Test creating responsibility record."""
        record = ResponsibilityRecord(
            record_id="rec_123",
            decision_id="dec_456",
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_maker=DecisionMaker.HUMAN_OPERATOR,
            responsible_party="alice@example.com",
            role="Security Analyst",
            reasoning="Suspicious activity detected",
            confidence=0.95,
            responsibility_level=ResponsibilityLevel.FULL,
        )

        assert record.record_id == "rec_123"
        assert record.decision_id == "dec_456"
        assert record.decision_maker == DecisionMaker.HUMAN_OPERATOR
        assert record.responsible_party == "alice@example.com"
        assert record.confidence == 0.95

    def test_record_with_delegation(self):
        """Test record with delegation information."""
        record = ResponsibilityRecord(
            record_id="rec_1",
            decision_id="dec_1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_maker=DecisionMaker.DELEGATED,
            responsible_party="bob@example.com",
            role="Operator",
            reasoning="Delegated authority",
            confidence=0.9,
            responsibility_level=ResponsibilityLevel.SHARED,
            delegated_from="manager@example.com",
        )

        assert record.delegated_from == "manager@example.com"
        assert record.responsibility_level == ResponsibilityLevel.SHARED

    def test_record_with_ai_override(self):
        """Test record where human overrode AI."""
        record = ResponsibilityRecord(
            record_id="rec_2",
            decision_id="dec_2",
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_maker=DecisionMaker.HUMAN_SUPERVISOR,
            responsible_party="supervisor@example.com",
            role="Supervisor",
            reasoning="AI recommendation too strict",
            confidence=0.85,
            responsibility_level=ResponsibilityLevel.FULL,
            override_ai=True,
            ai_recommendation="deny",
        )

        assert record.override_ai is True
        assert record.ai_recommendation == "deny"

    def test_record_to_dict(self):
        """Test converting record to dictionary."""
        record = ResponsibilityRecord(
            record_id="rec_3",
            decision_id="dec_3",
            timestamp="2025-01-01T00:00:00Z",
            decision_maker=DecisionMaker.AI_SYSTEM,
            responsible_party="system",
            role="Automated System",
            reasoning="Policy match",
            confidence=0.99,
            responsibility_level=ResponsibilityLevel.AUTOMATED,
        )

        data = record.to_dict()
        assert data["record_id"] == "rec_3"
        assert data["decision_maker"] == "ai_system"
        assert data["responsibility_level"] == "automated"


class TestResponsibilityTracker:
    """Tests for ResponsibilityTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create responsibility tracker."""
        return ResponsibilityTracker()

    def test_initialization(self, tracker):
        """Test tracker initialization."""
        assert isinstance(tracker.records, list)
        assert len(tracker.records) == 0
        assert tracker.storage is None

    def test_record_decision(self, tracker):
        """Test recording a decision."""
        record = tracker.record_decision(
            decision_id="dec_test_1",
            decision_maker=DecisionMaker.HUMAN_OPERATOR,
            responsible_party="alice@example.com",
            role="Analyst",
            reasoning="Security threat detected",
            confidence=0.95,
            responsibility_level=ResponsibilityLevel.FULL,
        )

        assert record.decision_id == "dec_test_1"
        assert record.responsible_party == "alice@example.com"
        assert len(tracker.records) == 1

    def test_record_with_delegation(self, tracker):
        """Test recording decision with delegation."""
        record = tracker.record_decision(
            decision_id="dec_del",
            decision_maker=DecisionMaker.DELEGATED,
            responsible_party="operator@example.com",
            role="Operator",
            reasoning="Delegated decision",
            confidence=0.8,
            responsibility_level=ResponsibilityLevel.SHARED,
            delegated_from="manager@example.com",
        )

        assert record.delegated_from == "manager@example.com"
        assert record.decision_maker == DecisionMaker.DELEGATED

    def test_record_with_ai_override(self, tracker):
        """Test recording decision with AI override."""
        record = tracker.record_decision(
            decision_id="dec_override",
            decision_maker=DecisionMaker.HUMAN_SUPERVISOR,
            responsible_party="supervisor@example.com",
            role="Supervisor",
            reasoning="Override needed",
            confidence=0.9,
            responsibility_level=ResponsibilityLevel.FULL,
            override_ai=True,
            ai_recommendation="deny",
        )

        assert record.override_ai is True
        assert record.ai_recommendation == "deny"

    def test_record_requiring_review(self, tracker):
        """Test recording decision that requires review."""
        record = tracker.record_decision(
            decision_id="dec_review",
            decision_maker=DecisionMaker.AI_SYSTEM,
            responsible_party="system",
            role="AI System",
            reasoning="High-risk decision",
            confidence=0.75,
            responsibility_level=ResponsibilityLevel.SUPERVISED,
            review_required=True,
        )

        assert record.review_required is True
        assert record.reviewed_by is None

    def test_mark_reviewed(self, tracker):
        """Test marking decision as reviewed."""
        # Record decision
        record = tracker.record_decision(
            decision_id="dec_to_review",
            decision_maker=DecisionMaker.AI_SYSTEM,
            responsible_party="system",
            role="AI System",
            reasoning="Needs review",
            confidence=0.7,
            responsibility_level=ResponsibilityLevel.SUPERVISED,
            review_required=True,
        )

        # Mark as reviewed using record_id
        updated = tracker.mark_reviewed(
            record_id=record.record_id,
            reviewed_by="reviewer@example.com",
        )

        assert updated is True
        # Verify it was updated
        assert record.reviewed_by == "reviewer@example.com"
        assert record.reviewed_at is not None

    def test_get_responsibility_chain(self, tracker):
        """Test getting responsibility chain for a decision."""
        # Record decision and escalation
        tracker.record_decision(
            decision_id="dec_chain",
            decision_maker=DecisionMaker.HUMAN_OPERATOR,
            responsible_party="operator@example.com",
            role="Operator",
            reasoning="Initial decision",
            confidence=0.8,
            responsibility_level=ResponsibilityLevel.SUPERVISED,
        )

        tracker.record_decision(
            decision_id="dec_chain",
            decision_maker=DecisionMaker.HUMAN_SUPERVISOR,
            responsible_party="supervisor@example.com",
            role="Supervisor",
            reasoning="Escalation required",
            confidence=0.9,
            responsibility_level=ResponsibilityLevel.FULL,
            escalated_to="executive@example.com",
        )

        chain = tracker.get_responsibility_chain("dec_chain")
        assert len(chain) == 2

    def test_get_by_responsible_party(self, tracker):
        """Test getting records by responsible party."""
        # Record multiple decisions
        tracker.record_decision(
            decision_id="dec_1",
            decision_maker=DecisionMaker.HUMAN_OPERATOR,
            responsible_party="alice@example.com",
            role="Analyst",
            reasoning="Decision 1",
            confidence=0.9,
            responsibility_level=ResponsibilityLevel.FULL,
        )

        tracker.record_decision(
            decision_id="dec_2",
            decision_maker=DecisionMaker.HUMAN_OPERATOR,
            responsible_party="alice@example.com",
            role="Analyst",
            reasoning="Decision 2",
            confidence=0.85,
            responsibility_level=ResponsibilityLevel.FULL,
        )

        tracker.record_decision(
            decision_id="dec_3",
            decision_maker=DecisionMaker.HUMAN_OPERATOR,
            responsible_party="bob@example.com",
            role="Analyst",
            reasoning="Decision 3",
            confidence=0.8,
            responsibility_level=ResponsibilityLevel.FULL,
        )

        alice_records = tracker.get_by_responsible_party("alice@example.com")
        assert len(alice_records) == 2

    def test_get_ai_overrides(self, tracker):
        """Test getting AI override records."""
        # Record some with and without overrides
        tracker.record_decision(
            decision_id="dec_no_override",
            decision_maker=DecisionMaker.AI_SYSTEM,
            responsible_party="system",
            role="AI",
            reasoning="Normal decision",
            confidence=0.95,
            responsibility_level=ResponsibilityLevel.AUTOMATED,
        )

        tracker.record_decision(
            decision_id="dec_with_override",
            decision_maker=DecisionMaker.HUMAN_SUPERVISOR,
            responsible_party="supervisor@example.com",
            role="Supervisor",
            reasoning="Override needed",
            confidence=0.9,
            responsibility_level=ResponsibilityLevel.FULL,
            override_ai=True,
            ai_recommendation="allow",
        )

        overrides = tracker.get_ai_overrides()
        assert len(overrides) == 1
        assert overrides[0].override_ai is True

    def test_get_pending_reviews(self, tracker):
        """Test getting pending review records."""
        # Record decisions with and without review
        tracker.record_decision(
            decision_id="dec_no_review",
            decision_maker=DecisionMaker.HUMAN_OPERATOR,
            responsible_party="operator@example.com",
            role="Operator",
            reasoning="Standard decision",
            confidence=0.95,
            responsibility_level=ResponsibilityLevel.FULL,
        )

        tracker.record_decision(
            decision_id="dec_needs_review",
            decision_maker=DecisionMaker.AI_SYSTEM,
            responsible_party="system",
            role="AI",
            reasoning="High risk",
            confidence=0.7,
            responsibility_level=ResponsibilityLevel.SUPERVISED,
            review_required=True,
        )

        pending = tracker.get_pending_reviews()
        assert len(pending) == 1
        assert pending[0].review_required is True
        assert pending[0].reviewed_by is None

    def test_generate_accountability_report(self, tracker):
        """Test generating accountability report."""
        # Record some decisions
        tracker.record_decision(
            decision_id="dec_1",
            decision_maker=DecisionMaker.AI_SYSTEM,
            responsible_party="system",
            role="AI",
            reasoning="Automated",
            confidence=0.95,
            responsibility_level=ResponsibilityLevel.AUTOMATED,
        )

        tracker.record_decision(
            decision_id="dec_2",
            decision_maker=DecisionMaker.HUMAN_SUPERVISOR,
            responsible_party="supervisor@example.com",
            role="Supervisor",
            reasoning="Override",
            confidence=0.9,
            responsibility_level=ResponsibilityLevel.FULL,
            override_ai=True,
            ai_recommendation="deny",
        )

        report = tracker.generate_accountability_report()

        assert "summary" in report
        assert "summary" in report
        assert report["summary"]["total_decisions"] == 2
        assert "by_decision_maker" in report["summary"]
        assert "by_responsibility_level" in report["summary"]

    def test_report_includes_override_stats(self, tracker):
        """Test that report includes AI override statistics."""
        # Record overrides
        tracker.record_decision(
            decision_id="dec_override_1",
            decision_maker=DecisionMaker.HUMAN_SUPERVISOR,
            responsible_party="supervisor@example.com",
            role="Supervisor",
            reasoning="Override",
            confidence=0.9,
            responsibility_level=ResponsibilityLevel.FULL,
            override_ai=True,
            ai_recommendation="deny",
        )

        report = tracker.generate_accountability_report()

        assert "summary" in report
        assert "ai_overrides" in report["summary"]
        assert report["summary"]["ai_overrides"] == 1

    def test_export_for_legal(self, tracker):
        """Test exporting decision for legal review."""
        # Record decision
        tracker.record_decision(
            decision_id="dec_legal",
            decision_maker=DecisionMaker.HUMAN_EXECUTIVE,
            responsible_party="executive@example.com",
            role="Executive",
            reasoning="High-stakes decision",
            confidence=0.95,
            responsibility_level=ResponsibilityLevel.FULL,
            liability_accepted=True,
        )

        export = tracker.export_for_legal("dec_legal")

        assert "decision_id" in export
        assert "responsibility_records" in export
        assert "final_responsible_party" in export

    def test_tracker_to_dict(self, tracker):
        """Test converting tracker to dictionary."""
        # Record some decisions
        tracker.record_decision(
            decision_id="dec_1",
            decision_maker=DecisionMaker.AI_SYSTEM,
            responsible_party="system",
            role="AI",
            reasoning="Test",
            confidence=0.9,
            responsibility_level=ResponsibilityLevel.AUTOMATED,
        )

        data = tracker.to_dict()

        assert "records" in data
        assert len(data["records"]) == 1


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_mark_reviewed_nonexistent_decision(self):
        """Test marking nonexistent record as reviewed."""
        tracker = ResponsibilityTracker()

        result = tracker.mark_reviewed(
            record_id="nonexistent",
            reviewed_by="reviewer@example.com",
        )

        assert result is False

    def test_get_empty_responsibility_chain(self):
        """Test getting chain for nonexistent decision."""
        tracker = ResponsibilityTracker()

        chain = tracker.get_responsibility_chain("nonexistent")
        assert chain == []

    def test_export_legal_nonexistent_decision(self):
        """Test exporting nonexistent decision."""
        tracker = ResponsibilityTracker()

        export = tracker.export_for_legal("nonexistent")
        assert export["decision_id"] == "nonexistent"
        assert export["responsibility_records"] == []

    def test_multiple_records_same_decision(self):
        """Test recording multiple responsibility records for same decision."""
        tracker = ResponsibilityTracker()

        # Initial decision
        tracker.record_decision(
            decision_id="dec_multi",
            decision_maker=DecisionMaker.AI_SYSTEM,
            responsible_party="system",
            role="AI",
            reasoning="Initial automated decision",
            confidence=0.8,
            responsibility_level=ResponsibilityLevel.SUPERVISED,
        )

        # Human review
        tracker.record_decision(
            decision_id="dec_multi",
            decision_maker=DecisionMaker.HUMAN_OPERATOR,
            responsible_party="operator@example.com",
            role="Operator",
            reasoning="Reviewed and confirmed",
            confidence=0.95,
            responsibility_level=ResponsibilityLevel.FULL,
        )

        chain = tracker.get_responsibility_chain("dec_multi")
        assert len(chain) == 2

    def test_low_confidence_decision(self):
        """Test recording low confidence decision."""
        tracker = ResponsibilityTracker()

        record = tracker.record_decision(
            decision_id="dec_low_conf",
            decision_maker=DecisionMaker.AI_SYSTEM,
            responsible_party="system",
            role="AI",
            reasoning="Uncertain classification",
            confidence=0.4,
            responsibility_level=ResponsibilityLevel.SUPERVISED,
            review_required=True,
        )

        assert record.confidence == 0.4
        assert record.review_required is True
