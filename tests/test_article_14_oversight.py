"""Tests for EU AI Act Article 14 - Human Oversight Evidence System."""

from datetime import datetime

import pytest

from lexecon.compliance.eu_ai_act.article_14_oversight import (
    EscalationPath,
    HumanIntervention,
    HumanOversightEvidence,
    InterventionType,
    OversightRole,
)
from lexecon.identity.signing import KeyManager


class TestInterventionType:
    """Tests for InterventionType enum."""

    def test_intervention_types_exist(self):
        """Test that all intervention types are defined."""
        assert InterventionType.APPROVAL.value == "approval"
        assert InterventionType.OVERRIDE.value == "override"
        assert InterventionType.ESCALATION.value == "escalation"
        assert InterventionType.EMERGENCY_STOP.value == "emergency_stop"
        assert InterventionType.POLICY_EXCEPTION.value == "policy_exception"
        assert InterventionType.MANUAL_REVIEW.value == "manual_review"


class TestOversightRole:
    """Tests for OversightRole enum."""

    def test_oversight_roles_exist(self):
        """Test that all oversight roles are defined."""
        assert OversightRole.COMPLIANCE_OFFICER.value == "compliance_officer"
        assert OversightRole.SECURITY_LEAD.value == "security_lead"
        assert OversightRole.LEGAL_COUNSEL.value == "legal_counsel"
        assert OversightRole.RISK_MANAGER.value == "risk_manager"
        assert OversightRole.EXECUTIVE.value == "executive"
        assert OversightRole.SOC_ANALYST.value == "soc_analyst"


class TestHumanOversightEvidence:
    """Tests for HumanOversightEvidence class."""

    @pytest.fixture
    def oversight(self):
        """Create oversight evidence system."""
        return HumanOversightEvidence()

    @pytest.fixture
    def oversight_with_km(self):
        """Create oversight system with specific key manager."""
        km = KeyManager.generate()
        return HumanOversightEvidence(key_manager=km)

    def test_initialization(self, oversight):
        """Test oversight system initialization."""
        assert oversight.key_manager is not None
        assert isinstance(oversight.interventions, list)
        assert len(oversight.interventions) == 0
        assert isinstance(oversight.escalation_paths, dict)

    def test_default_escalation_paths(self, oversight):
        """Test that default escalation paths are created."""
        assert "high_risk" in oversight.escalation_paths
        assert "financial" in oversight.escalation_paths
        assert "legal" in oversight.escalation_paths
        assert "operational" in oversight.escalation_paths

    def test_high_risk_escalation_path(self, oversight):
        """Test high risk escalation path configuration."""
        path = oversight.escalation_paths["high_risk"]

        assert path.decision_class == "high_risk"
        assert OversightRole.SOC_ANALYST in path.roles
        assert OversightRole.SECURITY_LEAD in path.roles
        assert OversightRole.EXECUTIVE in path.roles
        assert path.max_response_time_minutes == 15
        assert path.requires_approval_from == OversightRole.SECURITY_LEAD

    def test_log_intervention_approval(self, oversight):
        """Test logging an approval intervention."""
        ai_rec = {"action": "allow", "confidence": 0.95}
        human_dec = {"action": "allow", "approved": True}

        intervention = oversight.log_intervention(
            intervention_type=InterventionType.APPROVAL,
            ai_recommendation=ai_rec,
            human_decision=human_dec,
            human_role=OversightRole.COMPLIANCE_OFFICER,
            reason="AI recommendation aligns with policy",
        )

        assert intervention.intervention_type == InterventionType.APPROVAL
        assert intervention.ai_recommendation == ai_rec
        assert intervention.human_decision == human_dec
        assert intervention.human_role == OversightRole.COMPLIANCE_OFFICER
        assert intervention.ai_confidence == 0.95
        assert intervention.signature is not None

    def test_log_intervention_override(self, oversight):
        """Test logging an override intervention."""
        ai_rec = {"action": "deny", "confidence": 0.85}
        human_dec = {"action": "allow", "overridden": True}

        intervention = oversight.log_intervention(
            intervention_type=InterventionType.OVERRIDE,
            ai_recommendation=ai_rec,
            human_decision=human_dec,
            human_role=OversightRole.SECURITY_LEAD,
            reason="Business context requires exception",
        )

        assert intervention.intervention_type == InterventionType.OVERRIDE
        assert intervention.ai_recommendation["action"] != intervention.human_decision["action"]

    def test_log_intervention_with_context(self, oversight):
        """Test logging intervention with request context."""
        context = {"user_id": "user123", "request_id": "req456"}

        intervention = oversight.log_intervention(
            intervention_type=InterventionType.MANUAL_REVIEW,
            ai_recommendation={"action": "allow"},
            human_decision={"action": "allow"},
            human_role=OversightRole.RISK_MANAGER,
            reason="Required review completed",
            request_context=context,
        )

        assert intervention.request_context == context

    def test_log_intervention_with_response_time(self, oversight):
        """Test logging intervention with response time."""
        intervention = oversight.log_intervention(
            intervention_type=InterventionType.APPROVAL,
            ai_recommendation={"action": "allow"},
            human_decision={"action": "allow"},
            human_role=OversightRole.SOC_ANALYST,
            reason="Approved",
            response_time_ms=1500,
        )

        assert intervention.response_time_ms == 1500

    def test_intervention_has_unique_id(self, oversight):
        """Test that interventions get unique IDs."""
        int1 = oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Reason 1",
        )

        int2 = oversight.log_intervention(
            InterventionType.OVERRIDE,
            {"action": "deny"},
            {"action": "allow"},
            OversightRole.SECURITY_LEAD,
            "Reason 2",
        )

        assert int1.intervention_id != int2.intervention_id

    def test_intervention_has_timestamp(self, oversight):
        """Test that interventions have timestamps."""
        intervention = oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
        )

        assert intervention.timestamp is not None
        # Should be ISO format with Z suffix
        assert intervention.timestamp.endswith("Z")

        # Should be parseable
        dt = datetime.fromisoformat(intervention.timestamp.replace("Z", "+00:00"))
        assert isinstance(dt, datetime)

    def test_intervention_is_signed_by_default(self, oversight):
        """Test that interventions are signed by default."""
        intervention = oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
        )

        assert intervention.signature is not None
        assert len(intervention.signature) > 0

    def test_intervention_can_be_unsigned(self, oversight):
        """Test that interventions can be created without signatures."""
        intervention = oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
            sign=False,
        )

        assert intervention.signature is None

    def test_verify_intervention_valid(self, oversight):
        """Test verifying a valid intervention."""
        intervention = oversight.log_intervention(
            InterventionType.OVERRIDE,
            {"action": "deny"},
            {"action": "allow"},
            OversightRole.SECURITY_LEAD,
            "Override required",
        )

        is_valid = oversight.verify_intervention(intervention)
        assert is_valid is True

    def test_verify_intervention_invalid_signature(self, oversight):
        """Test that tampered intervention fails verification."""
        intervention = oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
        )

        # Tamper with the intervention
        intervention.reason = "TAMPERED"

        is_valid = oversight.verify_intervention(intervention)
        assert is_valid is False

    def test_verify_intervention_no_signature(self, oversight):
        """Test verifying intervention without signature."""
        intervention = oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
            sign=False,
        )

        is_valid = oversight.verify_intervention(intervention)
        assert is_valid is False

    def test_multiple_interventions_stored(self, oversight):
        """Test that multiple interventions are stored."""
        for i in range(5):
            oversight.log_intervention(
                InterventionType.APPROVAL,
                {"action": "allow", "index": i},
                {"action": "allow"},
                OversightRole.COMPLIANCE_OFFICER,
                f"Approved {i}",
            )

        assert len(oversight.interventions) == 5

    def test_generate_oversight_effectiveness_report(self, oversight):
        """Test generating oversight effectiveness report."""
        # Log some interventions with decision fields for override detection
        oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow", "confidence": 0.9, "decision": "allow"},
            {"action": "allow", "decision": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
            response_time_ms=1000,
        )

        oversight.log_intervention(
            InterventionType.OVERRIDE,
            {"action": "deny", "confidence": 0.8, "decision": "deny"},
            {"action": "allow", "decision": "allow"},
            OversightRole.SECURITY_LEAD,
            "Override needed",
            response_time_ms=2000,
        )

        report = oversight.generate_oversight_effectiveness_report(time_period_days=30)

        assert "total_interventions" in report
        assert "intervention_breakdown" in report
        assert "effectiveness_metrics" in report
        assert "response_time_metrics" in report
        assert "compliance_assessment" in report

    def test_effectiveness_report_calculates_override_rate(self, oversight):
        """Test that report calculates override rate correctly."""
        # 3 approvals, 2 overrides = 40% override rate
        for _ in range(3):
            oversight.log_intervention(
                InterventionType.APPROVAL,
                {"action": "allow", "decision": "allow"},
                {"action": "allow", "decision": "allow"},
                OversightRole.COMPLIANCE_OFFICER,
                "Approved",
            )

        for _ in range(2):
            oversight.log_intervention(
                InterventionType.OVERRIDE,
                {"action": "deny", "decision": "deny"},
                {"action": "allow", "decision": "allow"},
                OversightRole.SECURITY_LEAD,
                "Override",
            )

        report = oversight.generate_oversight_effectiveness_report()

        assert report["total_interventions"] == 5
        assert report["effectiveness_metrics"]["override_rate_percent"] == 40.0  # 2/5 = 40%

    def test_effectiveness_report_average_response_time(self, oversight):
        """Test that report calculates average response time."""
        oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
            response_time_ms=1000,
        )

        oversight.log_intervention(
            InterventionType.OVERRIDE,
            {"action": "deny"},
            {"action": "allow"},
            OversightRole.SECURITY_LEAD,
            "Override",
            response_time_ms=3000,
        )

        report = oversight.generate_oversight_effectiveness_report()

        # Average of 1000 and 3000 is 2000
        assert report["response_time_metrics"]["average_ms"] == 2000.0

    def test_effectiveness_report_intervention_breakdown(self, oversight):
        """Test that report breaks down interventions by type."""
        oversight.log_intervention(
            InterventionType.APPROVAL, {}, {}, OversightRole.COMPLIANCE_OFFICER, "A",
        )
        oversight.log_intervention(
            InterventionType.APPROVAL, {}, {}, OversightRole.COMPLIANCE_OFFICER, "B",
        )
        oversight.log_intervention(
            InterventionType.OVERRIDE, {}, {}, OversightRole.SECURITY_LEAD, "C",
        )
        oversight.log_intervention(
            InterventionType.EMERGENCY_STOP, {}, {}, OversightRole.EXECUTIVE, "D",
        )

        report = oversight.generate_oversight_effectiveness_report()

        breakdown = report["intervention_breakdown"]
        assert breakdown["by_type"][InterventionType.APPROVAL.value] == 2
        assert breakdown["by_type"][InterventionType.OVERRIDE.value] == 1
        assert breakdown["by_type"][InterventionType.EMERGENCY_STOP.value] == 1

    def test_get_escalation_path(self, oversight):
        """Test getting escalation path for decision class."""
        path = oversight.get_escalation_path("high_risk")

        assert path is not None
        assert path.decision_class == "high_risk"

    def test_get_escalation_path_nonexistent(self, oversight):
        """Test getting non-existent escalation path."""
        path = oversight.get_escalation_path("nonexistent")

        assert path is None

    def test_export_evidence_package(self, oversight):
        """Test exporting complete evidence package."""
        # Log some interventions
        oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
        )

        package = oversight.export_evidence_package()

        assert "summary" in package
        assert "interventions" in package
        assert "effectiveness_report" in package
        assert "compliance_attestation" in package

    def test_export_evidence_package_metadata(self, oversight):
        """Test evidence package metadata."""
        package = oversight.export_evidence_package()

        assert "generated_at" in package
        assert "period" in package
        assert "summary" in package
        assert package["summary"]["total_interventions"] >= 0

    def test_export_evidence_package_verification_proofs(self, oversight):
        """Test that evidence package includes verification evidence."""
        oversight.log_intervention(
            InterventionType.OVERRIDE,
            {"action": "deny"},
            {"action": "allow"},
            OversightRole.SECURITY_LEAD,
            "Override",
        )

        package = oversight.export_evidence_package()

        # Verification info is in the effectiveness report
        evidence_integrity = package["effectiveness_report"]["evidence_integrity"]
        assert evidence_integrity["all_signed"] is True
        assert evidence_integrity["verification_rate"] == 100.0

    def test_export_markdown(self, oversight):
        """Test exporting evidence package as markdown."""
        oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
        )

        package = oversight.export_evidence_package()
        markdown = oversight.export_markdown(package)

        assert isinstance(markdown, str)
        assert "# EU AI Act Article 14" in markdown
        assert "Human Oversight Evidence" in markdown

    def test_export_markdown_includes_interventions(self, oversight):
        """Test that markdown export includes intervention details."""
        oversight.log_intervention(
            InterventionType.OVERRIDE,
            {"action": "deny"},
            {"action": "allow"},
            OversightRole.SECURITY_LEAD,
            "Override required for business context",
        )

        package = oversight.export_evidence_package()
        markdown = oversight.export_markdown(package)

        assert "override:" in markdown
        assert "security_lead:" in markdown

    def test_simulate_escalation(self, oversight):
        """Test escalation simulation."""
        result = oversight.simulate_escalation(
            decision_class="high_risk",
            current_role=OversightRole.SOC_ANALYST,
        )

        assert "full_escalation_chain" in result
        assert "current_role" in result
        assert "can_approve" in result

    def test_simulate_escalation_chain(self, oversight):
        """Test that escalation follows correct chain."""
        result = oversight.simulate_escalation(
            decision_class="high_risk",
            current_role=OversightRole.SOC_ANALYST,
        )

        # High risk escalates: SOC -> Security Lead -> Executive
        chain = result["full_escalation_chain"]
        assert OversightRole.SOC_ANALYST.value in chain
        assert OversightRole.SECURITY_LEAD.value in chain
        assert OversightRole.EXECUTIVE.value in chain

    def test_simulate_escalation_approval_authority(self, oversight):
        """Test that escalation identifies who can approve."""
        # SOC analyst cannot approve high risk decisions
        result1 = oversight.simulate_escalation(
            decision_class="high_risk",
            current_role=OversightRole.SOC_ANALYST,
        )
        assert result1["can_approve"] is False

        # Security lead CAN approve high risk decisions
        result2 = oversight.simulate_escalation(
            decision_class="high_risk",
            current_role=OversightRole.SECURITY_LEAD,
        )
        assert result2["can_approve"] is True


class TestEscalationPath:
    """Tests for EscalationPath dataclass."""

    def test_create_escalation_path(self):
        """Test creating escalation path."""
        path = EscalationPath(
            decision_class="test_class",
            roles=[OversightRole.COMPLIANCE_OFFICER, OversightRole.LEGAL_COUNSEL],
            max_response_time_minutes=30,
            requires_approval_from=OversightRole.LEGAL_COUNSEL,
        )

        assert path.decision_class == "test_class"
        assert len(path.roles) == 2
        assert path.max_response_time_minutes == 30

    def test_escalation_path_ordered_roles(self):
        """Test that escalation path maintains role order."""
        roles = [
            OversightRole.SOC_ANALYST,
            OversightRole.SECURITY_LEAD,
            OversightRole.EXECUTIVE,
        ]

        path = EscalationPath(
            decision_class="ordered",
            roles=roles,
            max_response_time_minutes=15,
            requires_approval_from=OversightRole.EXECUTIVE,
        )

        assert path.roles == roles
        assert path.roles[0] == OversightRole.SOC_ANALYST
        assert path.roles[-1] == OversightRole.EXECUTIVE


class TestHumanIntervention:
    """Tests for HumanIntervention dataclass."""

    def test_create_intervention(self):
        """Test creating human intervention record."""
        intervention = HumanIntervention(
            intervention_id="test_123",
            timestamp="2025-01-01T00:00:00Z",
            intervention_type=InterventionType.APPROVAL,
            ai_recommendation={"action": "allow"},
            ai_confidence=0.95,
            human_decision={"action": "allow"},
            human_role=OversightRole.COMPLIANCE_OFFICER,
            request_context={"user": "test"},
            reason="Test approval",
        )

        assert intervention.intervention_id == "test_123"
        assert intervention.intervention_type == InterventionType.APPROVAL
        assert intervention.ai_confidence == 0.95

    def test_intervention_optional_fields(self):
        """Test intervention with optional fields."""
        intervention = HumanIntervention(
            intervention_id="test",
            timestamp="2025-01-01T00:00:00Z",
            intervention_type=InterventionType.OVERRIDE,
            ai_recommendation={},
            ai_confidence=0.8,
            human_decision={},
            human_role=OversightRole.SECURITY_LEAD,
            request_context={},
            reason="Test",
            signature="test_signature",
            response_time_ms=1500,
            escalated_from="person_a",
            escalated_to="person_b",
        )

        assert intervention.signature == "test_signature"
        assert intervention.response_time_ms == 1500
        assert intervention.escalated_from == "person_a"
        assert intervention.escalated_to == "person_b"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_ai_recommendation(self):
        """Test handling empty AI recommendation."""
        oversight = HumanOversightEvidence()

        intervention = oversight.log_intervention(
            InterventionType.MANUAL_REVIEW,
            ai_recommendation={},
            human_decision={"action": "allow"},
            human_role=OversightRole.COMPLIANCE_OFFICER,
            reason="Manual review",
        )

        assert intervention.ai_confidence == 0.0  # Default when no confidence

    def test_very_long_reason(self):
        """Test intervention with very long reason."""
        oversight = HumanOversightEvidence()

        long_reason = "A" * 10000

        intervention = oversight.log_intervention(
            InterventionType.OVERRIDE,
            {"action": "deny"},
            {"action": "allow"},
            OversightRole.SECURITY_LEAD,
            long_reason,
        )

        assert intervention.reason == long_reason

    def test_effectiveness_report_no_interventions(self):
        """Test effectiveness report with no interventions."""
        oversight = HumanOversightEvidence()

        report = oversight.generate_oversight_effectiveness_report()

        assert report["total_interventions"] == 0
        # When no interventions, report structure may be minimal
        assert "intervention_breakdown" in report or "total_interventions" in report

    def test_effectiveness_report_no_response_times(self):
        """Test effectiveness report when no response times recorded."""
        oversight = HumanOversightEvidence()

        oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved",
            response_time_ms=None,
        )

        report = oversight.generate_oversight_effectiveness_report()

        # Should handle missing response times gracefully
        assert "response_time_metrics" in report

    def test_unicode_in_reason(self):
        """Test intervention with unicode characters."""
        oversight = HumanOversightEvidence()

        intervention = oversight.log_intervention(
            InterventionType.APPROVAL,
            {"action": "allow"},
            {"action": "allow"},
            OversightRole.COMPLIANCE_OFFICER,
            "Approved 审批 ✓",
        )

        assert "审批" in intervention.reason

    def test_concurrent_interventions(self):
        """Test logging multiple interventions rapidly."""
        oversight = HumanOversightEvidence()

        interventions = []
        for i in range(100):
            intervention = oversight.log_intervention(
                InterventionType.APPROVAL,
                {"action": "allow", "index": i},
                {"action": "allow"},
                OversightRole.COMPLIANCE_OFFICER,
                f"Approved {i}",
            )
            interventions.append(intervention)

        # All should have unique IDs
        ids = [i.intervention_id for i in interventions]
        assert len(ids) == len(set(ids))

    def test_export_with_no_data(self):
        """Test exporting evidence package with no interventions."""
        oversight = HumanOversightEvidence()

        package = oversight.export_evidence_package()

        assert package["summary"]["total_interventions"] == 0
        assert len(package["interventions"]) == 0
