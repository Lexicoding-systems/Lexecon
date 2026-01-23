"""Tests for escalation service."""

from datetime import datetime, timezone

import pytest

from lexecon.escalation.service import (
    EscalationConfig,
    EscalationService,
    generate_escalation_id,
)

# Import canonical governance models
try:
    from model_governance_pack.models import (
        Escalation,
        EscalationPriority,
        EscalationStatus,
        EscalationTrigger,
        EvidenceArtifact,
        Resolution,
        ResolutionOutcome,
        Risk,
        RiskDimensions,
        RiskLevel,
    )

    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False
    pytestmark = pytest.mark.skip("Governance models not available")


class TestEscalationIdGeneration:
    """Tests for escalation ID generation."""

    def test_generate_escalation_id_format(self):
        """Test escalation ID format."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"
        escalation_id = generate_escalation_id(decision_id)

        assert escalation_id.startswith("esc_dec_")
        assert "01JQXYZ1234567890ABCDEFGH" in escalation_id

    def test_generate_escalation_id_uniqueness(self):
        """Test that escalation IDs are unique (allows re-escalation)."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Multiple escalations for same decision should have different IDs
        id1 = generate_escalation_id(decision_id)
        id2 = generate_escalation_id(decision_id)

        assert id1 != id2
        assert id1.startswith("esc_dec_")
        assert id2.startswith("esc_dec_")


class TestEscalationConfig:
    """Tests for escalation configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = EscalationConfig()

        assert config.AUTO_ESCALATE_RISK_SCORE == 80
        assert config.AUTO_ESCALATE_RISK_LEVEL == RiskLevel.CRITICAL
        assert len(config.SLA_DEADLINES) == 4
        assert config.SLA_WARNING_HOURS == 1

    def test_sla_deadlines_by_priority(self):
        """Test SLA deadlines are defined for all priorities."""
        config = EscalationConfig()

        assert EscalationPriority.CRITICAL in config.SLA_DEADLINES
        assert EscalationPriority.HIGH in config.SLA_DEADLINES
        assert EscalationPriority.MEDIUM in config.SLA_DEADLINES
        assert EscalationPriority.LOW in config.SLA_DEADLINES

        # Verify critical has shortest deadline
        assert (
            config.SLA_DEADLINES[EscalationPriority.CRITICAL]
            < config.SLA_DEADLINES[EscalationPriority.HIGH]
        )


class TestEscalationService:
    """Tests for escalation service."""

    @pytest.fixture
    def service(self):
        """Create an escalation service instance."""
        return EscalationService()

    @pytest.fixture
    def high_risk(self):
        """Create a high-risk assessment."""
        return Risk(
            risk_id="rsk_dec_01JQXYZ1234567890ABCDEFGH",
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            overall_score=85,
            timestamp=datetime.now(timezone.utc),
            risk_level=RiskLevel.CRITICAL,
            dimensions=RiskDimensions(
                security=90,
                privacy=80,
                compliance=85,
            ),
        )

    @pytest.fixture
    def low_risk(self):
        """Create a low-risk assessment."""
        return Risk(
            risk_id="rsk_dec_01JQXYZ1111111111111111111",
            decision_id="dec_01JQXYZ1111111111111111111",
            overall_score=25,
            timestamp=datetime.now(timezone.utc),
            risk_level=RiskLevel.LOW,
            dimensions=RiskDimensions(security=20, privacy=30),
        )

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service.config is not None
        assert service.emit_notifications is True
        assert service.store_evidence is True

    def test_should_auto_escalate_high_risk(self, service, high_risk):
        """Test that high risk triggers auto-escalation."""
        assert service.should_auto_escalate(high_risk) is True

    def test_should_auto_escalate_low_risk(self, service, low_risk):
        """Test that low risk does not trigger auto-escalation."""
        assert service.should_auto_escalate(low_risk) is False

    def test_should_auto_escalate_no_risk(self, service):
        """Test that no risk does not trigger auto-escalation."""
        assert service.should_auto_escalate(None) is False

    def test_create_escalation_valid(self, service):
        """Test creating a valid escalation."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
            priority=EscalationPriority.CRITICAL,
            context_summary="High-risk decision requires review",
        )

        # Validate against schema
        assert isinstance(escalation, Escalation)
        assert escalation.escalation_id.startswith("esc_dec_")
        assert escalation.decision_id == "dec_01JQXYZ1234567890ABCDEFGH"
        assert escalation.trigger == EscalationTrigger.RISK_THRESHOLD
        assert "act_human_user:reviewer1" in escalation.escalated_to
        assert escalation.status == EscalationStatus.PENDING
        assert escalation.priority == EscalationPriority.CRITICAL
        assert escalation.sla_deadline is not None

    def test_create_escalation_empty_recipients(self, service):
        """Test that empty recipient list fails."""
        with pytest.raises(ValueError, match="at least one escalation recipient"):
            service.create_escalation(
                decision_id="dec_01JQXYZ1234567890ABCDEFGH",
                trigger=EscalationTrigger.RISK_THRESHOLD,
                escalated_to=[],  # Empty list
            )

    def test_create_escalation_infers_priority(self, service):
        """Test that priority is inferred from trigger."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
            # No priority specified
        )

        # RISK_THRESHOLD should infer CRITICAL priority
        assert escalation.priority == EscalationPriority.CRITICAL

    def test_create_escalation_sets_sla_deadline(self, service):
        """Test that SLA deadline is set based on priority."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
            priority=EscalationPriority.CRITICAL,
        )

        # Deadline should be ~2 hours from now for critical
        now = datetime.now(timezone.utc)
        deadline = escalation.sla_deadline

        time_diff = (deadline - now).total_seconds() / 3600
        assert 1.9 <= time_diff <= 2.1  # ~2 hours

    def test_create_escalation_emits_notification(self, service):
        """Test that creating escalation emits notification."""
        service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        notifications = service.get_notifications()
        assert len(notifications) >= 1
        assert any(n.event_type == "escalation_created" for n in notifications)

    def test_create_escalation_generates_evidence(self, service):
        """Test that creating escalation generates evidence artifact."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        artifacts = service.get_evidence_artifacts(
            escalation_id=escalation.escalation_id,
        )
        assert len(artifacts) >= 1
        assert any(
            a.metadata.get("event_type") == "escalation_created" for a in artifacts
        )

    def test_auto_escalate_for_high_risk(self, service, high_risk):
        """Test auto-escalation for high-risk decision."""
        escalation = service.auto_escalate_for_risk(
            decision_id=high_risk.decision_id,
            risk=high_risk,
        )

        assert escalation is not None
        assert escalation.trigger == EscalationTrigger.RISK_THRESHOLD
        assert escalation.priority == EscalationPriority.CRITICAL
        assert escalation.metadata["auto_escalated"] is True
        assert escalation.metadata["risk_score"] == 85

    def test_auto_escalate_for_low_risk(self, service, low_risk):
        """Test that low risk does not auto-escalate."""
        escalation = service.auto_escalate_for_risk(
            decision_id=low_risk.decision_id,
            risk=low_risk,
        )

        assert escalation is None

    def test_auto_escalate_context_summary(self, service, high_risk):
        """Test that auto-escalation includes context summary."""
        escalation = service.auto_escalate_for_risk(
            decision_id=high_risk.decision_id,
            risk=high_risk,
        )

        assert escalation.context_summary is not None
        assert "critical risk" in escalation.context_summary.lower()
        assert "85/100" in escalation.context_summary

    def test_acknowledge_escalation(self, service):
        """Test acknowledging an escalation."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Acknowledge
        updated = service.acknowledge_escalation(
            escalation_id=escalation.escalation_id,
            acknowledged_by="act_human_user:reviewer1",
        )

        assert updated.status == EscalationStatus.ACKNOWLEDGED
        assert updated.acknowledged_by == "act_human_user:reviewer1"
        assert updated.acknowledged_at is not None

    def test_acknowledge_escalation_not_found(self, service):
        """Test acknowledging non-existent escalation."""
        with pytest.raises(ValueError, match="not found"):
            service.acknowledge_escalation(
                escalation_id="esc_dec_nonexistent",
                acknowledged_by="act_human_user:reviewer1",
            )

    def test_acknowledge_already_resolved(self, service):
        """Test cannot acknowledge already resolved escalation."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Resolve first
        service.resolve_escalation(
            escalation_id=escalation.escalation_id,
            resolved_by="act_human_user:reviewer1",
            outcome=ResolutionOutcome.APPROVED,
        )

        # Try to acknowledge
        with pytest.raises(ValueError, match="Cannot acknowledge"):
            service.acknowledge_escalation(
                escalation_id=escalation.escalation_id,
                acknowledged_by="act_human_user:reviewer1",
            )

    def test_resolve_escalation(self, service):
        """Test resolving an escalation."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Resolve
        updated = service.resolve_escalation(
            escalation_id=escalation.escalation_id,
            resolved_by="act_human_user:reviewer1",
            outcome=ResolutionOutcome.APPROVED,
            notes="Risk is acceptable with current mitigations",
        )

        assert updated.status == EscalationStatus.RESOLVED
        assert updated.resolved_at is not None
        assert updated.resolution is not None
        assert updated.resolution.outcome == ResolutionOutcome.APPROVED
        assert updated.resolution.resolved_by == "act_human_user:reviewer1"
        assert "acceptable" in updated.resolution.notes

    def test_resolve_escalation_requires_authorization(self, service):
        """Test that resolver must be authorized."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Try to resolve with unauthorized actor
        with pytest.raises(ValueError, match="not authorized"):
            service.resolve_escalation(
                escalation_id=escalation.escalation_id,
                resolved_by="act_human_user:unauthorized",
                outcome=ResolutionOutcome.APPROVED,
            )

    def test_resolve_escalation_after_acknowledge(self, service):
        """Test that acknowledger can resolve."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Acknowledge with reviewer2
        service.acknowledge_escalation(
            escalation_id=escalation.escalation_id,
            acknowledged_by="act_human_user:reviewer2",
        )

        # Reviewer2 can resolve even if not in escalated_to
        updated = service.resolve_escalation(
            escalation_id=escalation.escalation_id,
            resolved_by="act_human_user:reviewer2",
            outcome=ResolutionOutcome.APPROVED,
        )

        assert updated.status == EscalationStatus.RESOLVED

    def test_resolve_already_resolved(self, service):
        """Test cannot resolve already resolved escalation."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Resolve once
        service.resolve_escalation(
            escalation_id=escalation.escalation_id,
            resolved_by="act_human_user:reviewer1",
            outcome=ResolutionOutcome.APPROVED,
        )

        # Try to resolve again
        with pytest.raises(ValueError, match="already resolved"):
            service.resolve_escalation(
                escalation_id=escalation.escalation_id,
                resolved_by="act_human_user:reviewer1",
                outcome=ResolutionOutcome.DENIED,
            )

    def test_get_escalation(self, service):
        """Test retrieving escalation by ID."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        retrieved = service.get_escalation(escalation.escalation_id)
        assert retrieved is not None
        assert retrieved.escalation_id == escalation.escalation_id

    def test_list_escalations_no_filter(self, service):
        """Test listing all escalations."""
        # Create multiple escalations
        for i in range(3):
            service.create_escalation(
                decision_id=f"dec_01JQXYZ{i:022d}",
                trigger=EscalationTrigger.RISK_THRESHOLD,
                escalated_to=["act_human_user:reviewer1"],
            )

        escalations = service.list_escalations()
        assert len(escalations) == 3

    def test_list_escalations_by_status(self, service):
        """Test filtering escalations by status."""
        # Create and resolve one
        esc1 = service.create_escalation(
            decision_id="dec_01JQXYZ1111111111111111111",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )
        service.resolve_escalation(
            escalation_id=esc1.escalation_id,
            resolved_by="act_human_user:reviewer1",
            outcome=ResolutionOutcome.APPROVED,
        )

        # Create pending one
        service.create_escalation(
            decision_id="dec_01JQXYZ2222222222222222222",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Filter by pending
        pending = service.list_escalations(status=EscalationStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].decision_id == "dec_01JQXYZ2222222222222222222"

        # Filter by resolved
        resolved = service.list_escalations(status=EscalationStatus.RESOLVED)
        assert len(resolved) == 1
        assert resolved[0].decision_id == "dec_01JQXYZ1111111111111111111"

    def test_list_escalations_by_priority(self, service):
        """Test filtering escalations by priority."""
        service.create_escalation(
            decision_id="dec_01JQXYZ1111111111111111111",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
            priority=EscalationPriority.CRITICAL,
        )
        service.create_escalation(
            decision_id="dec_01JQXYZ2222222222222222222",
            trigger=EscalationTrigger.ACTOR_REQUEST,
            escalated_to=["act_human_user:reviewer1"],
            priority=EscalationPriority.LOW,
        )

        critical = service.list_escalations(priority=EscalationPriority.CRITICAL)
        assert len(critical) == 1
        assert critical[0].priority == EscalationPriority.CRITICAL

    def test_list_escalations_by_decision(self, service):
        """Test filtering escalations by decision ID."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Create two escalations for same decision (re-escalation)
        service.create_escalation(
            decision_id=decision_id,
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )
        service.create_escalation(
            decision_id=decision_id,
            trigger=EscalationTrigger.POLICY_CONFLICT,
            escalated_to=["act_human_user:reviewer2"],
        )

        # Different decision
        service.create_escalation(
            decision_id="dec_01JQXYZ9999999999999999999",
            trigger=EscalationTrigger.ACTOR_REQUEST,
            escalated_to=["act_human_user:reviewer1"],
        )

        escalations = service.list_escalations(decision_id=decision_id)
        assert len(escalations) == 2
        assert all(e.decision_id == decision_id for e in escalations)


class TestSLATracking:
    """Tests for SLA tracking and notifications."""

    @pytest.fixture
    def service(self):
        """Create service with short SLA for testing."""
        config = EscalationConfig()
        # Override SLA deadlines for testing
        config.SLA_DEADLINES = {
            EscalationPriority.CRITICAL: 0.001,  # ~3.6 seconds
            EscalationPriority.HIGH: 0.002,
            EscalationPriority.MEDIUM: 0.003,
            EscalationPriority.LOW: 0.004,
        }
        config.SLA_WARNING_HOURS = 0.0005  # ~1.8 seconds
        return EscalationService(config=config)

    def test_check_sla_status_no_breach(self, service):
        """Test SLA check when no breach."""
        service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Check immediately (no breach yet)
        notifications = service.check_sla_status()
        # Should only have warning if very close to deadline
        assert len([n for n in notifications if n.event_type == "sla_exceeded"]) == 0

    def test_check_sla_status_with_breach(self, service):
        """Test SLA check with breach."""
        import time

        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
            priority=EscalationPriority.CRITICAL,
        )

        # Wait for SLA to expire (~3.6 seconds)
        time.sleep(4)

        # Check SLA
        notifications = service.check_sla_status()

        # Should have SLA exceeded notification
        exceeded = [n for n in notifications if n.event_type == "sla_exceeded"]
        assert len(exceeded) >= 1

        # Escalation should be marked expired
        updated = service.get_escalation(escalation.escalation_id)
        assert updated.status == EscalationStatus.EXPIRED

    def test_sla_tracking_ignores_resolved(self, service):
        """Test that SLA tracking ignores resolved escalations."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Resolve immediately
        service.resolve_escalation(
            escalation_id=escalation.escalation_id,
            resolved_by="act_human_user:reviewer1",
            outcome=ResolutionOutcome.APPROVED,
        )

        # Check SLA (should not trigger for resolved)
        notifications = service.check_sla_status()
        assert len(notifications) == 0

    def test_notifications_only_for_sla_risk(self, service):
        """Test that notifications only emit when SLA risk exists."""
        # Create escalation with long deadline
        config = EscalationConfig()
        config.SLA_DEADLINES[EscalationPriority.LOW] = 72  # 3 days
        long_service = EscalationService(config=config)

        long_service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.ACTOR_REQUEST,
            escalated_to=["act_human_user:reviewer1"],
            priority=EscalationPriority.LOW,
        )

        # Check SLA immediately (no risk yet)
        notifications = long_service.check_sla_status()

        # Should not emit warning (not close to deadline)
        assert len(notifications) == 0


class TestEvidenceArtifacts:
    """Tests for evidence artifact generation."""

    @pytest.fixture
    def service(self):
        """Create service with evidence enabled."""
        return EscalationService(store_evidence=True)

    def test_evidence_for_escalation_created(self, service):
        """Test evidence artifact created for new escalation."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        artifacts = service.get_evidence_artifacts(
            escalation_id=escalation.escalation_id,
        )

        created_artifacts = [
            a for a in artifacts if a.metadata.get("event_type") == "escalation_created"
        ]
        assert len(created_artifacts) >= 1

        artifact = created_artifacts[0]
        assert isinstance(artifact, EvidenceArtifact)
        assert artifact.is_immutable is True
        assert len(artifact.sha256_hash) == 64  # SHA-256 hex

    def test_evidence_for_all_lifecycle_events(self, service):
        """Test evidence artifacts for full escalation lifecycle."""
        # Create
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Acknowledge
        service.acknowledge_escalation(
            escalation_id=escalation.escalation_id,
            acknowledged_by="act_human_user:reviewer1",
        )

        # Resolve
        service.resolve_escalation(
            escalation_id=escalation.escalation_id,
            resolved_by="act_human_user:reviewer1",
            outcome=ResolutionOutcome.APPROVED,
        )

        # Check artifacts
        artifacts = service.get_evidence_artifacts(
            escalation_id=escalation.escalation_id,
        )

        event_types = {a.metadata.get("event_type") for a in artifacts}
        assert "escalation_created" in event_types
        assert "escalation_acknowledged" in event_types
        assert "escalation_resolved" in event_types

    def test_notification_artifacts_created(self, service):
        """Test that notification events generate evidence artifacts."""
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Get all artifacts for this decision
        artifacts = service.get_evidence_artifacts(decision_id=escalation.decision_id)

        # Should have artifacts for notifications
        notification_artifacts = [
            a for a in artifacts if a.metadata.get("notification_type")
        ]
        assert len(notification_artifacts) >= 1

    def test_evidence_disabled(self):
        """Test that evidence generation can be disabled."""
        service = EscalationService(store_evidence=False)

        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:reviewer1"],
        )

        # Escalation should exist but no evidence
        assert escalation is not None
        artifacts = service.get_evidence_artifacts(
            escalation_id=escalation.escalation_id,
        )
        assert len(artifacts) == 0


class TestIntegrationWorkflows:
    """Integration tests for complete escalation workflows."""

    def test_complete_escalation_workflow(self):
        """Test complete workflow from creation to resolution."""
        service = EscalationService()

        # 1. Create escalation
        escalation = service.create_escalation(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=[
                "act_human_user:reviewer1",
                "act_human_user:reviewer2",
            ],
            priority=EscalationPriority.HIGH,
            context_summary="High-risk action requires approval",
        )

        assert escalation.status == EscalationStatus.PENDING

        # 2. Acknowledge
        acknowledged = service.acknowledge_escalation(
            escalation_id=escalation.escalation_id,
            acknowledged_by="act_human_user:reviewer1",
        )

        assert acknowledged.status == EscalationStatus.ACKNOWLEDGED
        assert acknowledged.acknowledged_by == "act_human_user:reviewer1"

        # 3. Resolve
        resolved = service.resolve_escalation(
            escalation_id=escalation.escalation_id,
            resolved_by="act_human_user:reviewer1",
            outcome=ResolutionOutcome.APPROVED,
            notes="Risk is acceptable with proposed mitigations",
        )

        assert resolved.status == EscalationStatus.RESOLVED
        assert resolved.resolution.outcome == ResolutionOutcome.APPROVED

        # 4. Verify evidence trail
        artifacts = service.get_evidence_artifacts(
            escalation_id=escalation.escalation_id,
        )
        assert len(artifacts) >= 3  # Created, acknowledged, resolved

    def test_auto_escalation_workflow(self):
        """Test auto-escalation workflow for high-risk decision."""
        service = EscalationService()

        # Create high-risk assessment
        high_risk = Risk(
            risk_id="rsk_dec_01JQXYZ1234567890ABCDEFGH",
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            overall_score=95,
            timestamp=datetime.now(timezone.utc),
            risk_level=RiskLevel.CRITICAL,
            dimensions=RiskDimensions(
                security=95,
                privacy=90,
                compliance=100,
            ),
        )

        # Auto-escalate
        escalation = service.auto_escalate_for_risk(
            decision_id=high_risk.decision_id,
            risk=high_risk,
        )

        assert escalation is not None
        assert escalation.trigger == EscalationTrigger.RISK_THRESHOLD
        assert escalation.priority == EscalationPriority.CRITICAL
        assert escalation.metadata["auto_escalated"] is True

        # Verify notifications
        notifications = service.get_notifications(
            escalation_id=escalation.escalation_id,
        )
        assert len(notifications) >= 1
