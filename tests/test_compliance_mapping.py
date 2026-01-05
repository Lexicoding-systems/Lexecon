"""
Tests for Compliance Mapping Service (Phase 7).

Tests regulatory alignment and control mapping functionality.
"""

import pytest
from lexecon.compliance_mapping.service import (
    ComplianceMappingService,
    RegulatoryFramework,
    GovernancePrimitive,
    ControlStatus,
)


@pytest.fixture
def compliance_service():
    """Create a compliance mapping service instance."""
    return ComplianceMappingService()


class TestComplianceMappingService:
    """Tests for ComplianceMappingService."""

    def test_service_initialization(self, compliance_service):
        """Test service initializes with framework registries."""
        assert compliance_service is not None

        # Should have controls registered for each framework
        stats = compliance_service.get_statistics()
        assert stats["frameworks_tracked"] == 3
        assert stats["total_controls"] > 0

    def test_map_risk_assessment_to_soc2(self, compliance_service):
        """Test mapping risk assessment to SOC 2 controls."""
        mapping = compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.RISK_ASSESSMENT,
            primitive_id="rsk_dec_test_001",
            framework=RegulatoryFramework.SOC2
        )

        assert mapping is not None
        assert mapping.primitive_type == GovernancePrimitive.RISK_ASSESSMENT
        assert mapping.framework == RegulatoryFramework.SOC2
        assert len(mapping.control_ids) > 0
        # Should map to CC7.2 and CC9.1 (risk-related controls)
        assert "CC7.2" in mapping.control_ids or "CC9.1" in mapping.control_ids

    def test_map_escalation_to_iso27001(self, compliance_service):
        """Test mapping escalation to ISO 27001 controls."""
        mapping = compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.ESCALATION,
            primitive_id="esc_test_001",
            framework=RegulatoryFramework.ISO27001
        )

        assert mapping is not None
        assert mapping.primitive_type == GovernancePrimitive.ESCALATION
        assert mapping.framework == RegulatoryFramework.ISO27001
        assert len(mapping.control_ids) > 0
        # Should map to A.16.1.4 (incident management)
        assert "A.16.1.4" in mapping.control_ids

    def test_map_override_to_gdpr(self, compliance_service):
        """Test mapping override to GDPR articles."""
        mapping = compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.OVERRIDE,
            primitive_id="ovr_test_001",
            framework=RegulatoryFramework.GDPR
        )

        assert mapping is not None
        assert mapping.primitive_type == GovernancePrimitive.OVERRIDE
        assert mapping.framework == RegulatoryFramework.GDPR

    def test_link_evidence_to_control(self, compliance_service):
        """Test linking evidence artifact to a control."""
        # Link evidence to SOC 2 control CC6.1
        result = compliance_service.link_evidence_to_control(
            control_id="CC6.1",
            framework=RegulatoryFramework.SOC2,
            evidence_artifact_id="evd_decisionlog_abc123"
        )

        assert result is True

        # Verify evidence was linked
        control = compliance_service.get_control_status("CC6.1", RegulatoryFramework.SOC2)
        assert control is not None
        assert "evd_decisionlog_abc123" in control.evidence_artifact_ids

    def test_link_evidence_to_invalid_control(self, compliance_service):
        """Test linking evidence to non-existent control."""
        result = compliance_service.link_evidence_to_control(
            control_id="INVALID",
            framework=RegulatoryFramework.SOC2,
            evidence_artifact_id="evd_test_123"
        )

        assert result is False

    def test_verify_control(self, compliance_service):
        """Test marking a control as verified."""
        result = compliance_service.verify_control(
            control_id="CC7.2",
            framework=RegulatoryFramework.SOC2,
            notes="Verified through risk assessment process"
        )

        assert result is True

        # Check control status was updated
        control = compliance_service.get_control_status("CC7.2", RegulatoryFramework.SOC2)
        assert control is not None
        assert control.status == ControlStatus.VERIFIED
        assert control.last_verified is not None
        assert control.verification_notes == "Verified through risk assessment process"

    def test_verify_invalid_control(self, compliance_service):
        """Test verifying non-existent control."""
        result = compliance_service.verify_control(
            control_id="INVALID",
            framework=RegulatoryFramework.SOC2
        )

        assert result is False

    def test_get_control_status(self, compliance_service):
        """Test retrieving control status."""
        control = compliance_service.get_control_status("CC6.1", RegulatoryFramework.SOC2)

        assert control is not None
        assert control.control_id == "CC6.1"
        assert control.framework == RegulatoryFramework.SOC2
        assert control.title == "Logical and Physical Access Controls"
        assert len(control.mapped_primitives) > 0

    def test_list_controls_all(self, compliance_service):
        """Test listing all controls for a framework."""
        controls = compliance_service.list_controls(RegulatoryFramework.SOC2)

        assert len(controls) == 3  # We defined 3 SOC 2 controls
        assert all(c.framework == RegulatoryFramework.SOC2 for c in controls)

    def test_list_controls_by_status(self, compliance_service):
        """Test filtering controls by status."""
        # Verify one control
        compliance_service.verify_control("CC6.1", RegulatoryFramework.SOC2)

        # List verified controls
        verified = compliance_service.list_controls(
            RegulatoryFramework.SOC2,
            status=ControlStatus.VERIFIED
        )

        assert len(verified) == 1
        assert verified[0].control_id == "CC6.1"

        # List not implemented controls
        not_implemented = compliance_service.list_controls(
            RegulatoryFramework.SOC2,
            status=ControlStatus.NOT_IMPLEMENTED
        )

        assert len(not_implemented) == 2  # Remaining controls

    def test_list_controls_by_category(self, compliance_service):
        """Test filtering controls by category."""
        # All SOC 2 controls we defined are in "Common Criteria" category
        controls = compliance_service.list_controls(
            RegulatoryFramework.SOC2,
            category="Common Criteria"
        )

        assert len(controls) == 3
        assert all(c.category == "Common Criteria" for c in controls)

    def test_analyze_gaps(self, compliance_service):
        """Test gap analysis for a framework."""
        # Initially, all controls should be gaps (not implemented)
        gaps = compliance_service.analyze_gaps(RegulatoryFramework.SOC2)

        assert len(gaps) == 3  # All 3 controls are gaps initially
        assert all(gap["status"] == "not_implemented" for gap in gaps)
        assert all("control_id" in gap for gap in gaps)
        assert all("severity" in gap for gap in gaps)

        # Verify one control
        compliance_service.verify_control("CC6.1", RegulatoryFramework.SOC2)

        # Gaps should decrease
        gaps_after = compliance_service.analyze_gaps(RegulatoryFramework.SOC2)
        assert len(gaps_after) == 2  # One less gap

    def test_generate_compliance_report(self, compliance_service):
        """Test generating compliance report."""
        # Verify some controls to get interesting data
        compliance_service.verify_control("CC6.1", RegulatoryFramework.SOC2)
        compliance_service.verify_control("CC7.2", RegulatoryFramework.SOC2)

        report = compliance_service.generate_compliance_report(RegulatoryFramework.SOC2)

        assert report is not None
        assert report.framework == RegulatoryFramework.SOC2
        assert report.total_controls == 3
        assert report.verified_controls == 2
        assert report.compliance_percentage > 0
        assert len(report.gaps) > 0
        assert len(report.recommendations) > 0
        assert report.generated_at is not None

    def test_get_framework_coverage(self, compliance_service):
        """Test getting framework coverage statistics."""
        coverage = compliance_service.get_framework_coverage(RegulatoryFramework.SOC2)

        assert coverage is not None
        assert coverage["framework"] == "soc2"
        assert coverage["total_controls"] == 3
        assert "status_breakdown" in coverage
        assert "categories" in coverage
        assert "overall_compliance" in coverage

    def test_get_framework_coverage_by_category(self, compliance_service):
        """Test framework coverage grouped by category."""
        # Verify some controls
        compliance_service.verify_control("CC6.1", RegulatoryFramework.SOC2)

        coverage = compliance_service.get_framework_coverage(RegulatoryFramework.SOC2)

        categories = coverage["categories"]
        assert "Common Criteria" in categories
        assert categories["Common Criteria"]["total"] == 3
        assert categories["Common Criteria"]["verified"] == 1

    def test_get_primitive_mappings(self, compliance_service):
        """Test getting all mappings for a primitive."""
        # Create some mappings
        compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.RISK_ASSESSMENT,
            primitive_id="rsk_test_123",
            framework=RegulatoryFramework.SOC2
        )

        compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.RISK_ASSESSMENT,
            primitive_id="rsk_test_123",
            framework=RegulatoryFramework.ISO27001
        )

        # Get mappings
        mappings = compliance_service.get_primitive_mappings("rsk_test_123")

        assert len(mappings) == 2
        assert all(m.primitive_id == "rsk_test_123" for m in mappings)
        assert {m.framework for m in mappings} == {
            RegulatoryFramework.SOC2,
            RegulatoryFramework.ISO27001
        }

    def test_get_statistics(self, compliance_service):
        """Test getting overall statistics."""
        # Create some mappings
        compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.RISK_ASSESSMENT,
            primitive_id="rsk_test_001",
            framework=RegulatoryFramework.SOC2
        )

        compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.ESCALATION,
            primitive_id="esc_test_001",
            framework=RegulatoryFramework.ISO27001
        )

        stats = compliance_service.get_statistics()

        assert stats["total_mappings"] == 2
        assert stats["frameworks_tracked"] == 3
        assert stats["total_controls"] == 9  # 3 per framework
        assert "overall_verification_rate" in stats
        assert "frameworks" in stats

    def test_all_frameworks_have_controls(self, compliance_service):
        """Test that all supported frameworks have controls defined."""
        for framework in [
            RegulatoryFramework.SOC2,
            RegulatoryFramework.ISO27001,
            RegulatoryFramework.GDPR
        ]:
            controls = compliance_service.list_controls(framework)
            assert len(controls) > 0, f"No controls defined for {framework.value}"

    def test_control_has_required_evidence_types(self, compliance_service):
        """Test that controls specify required evidence types."""
        control = compliance_service.get_control_status("CC7.2", RegulatoryFramework.SOC2)

        assert control is not None
        assert len(control.required_evidence_types) > 0
        # Risk control should require risk assessment evidence
        assert "risk_assessment" in control.required_evidence_types

    def test_control_has_mapped_primitives(self, compliance_service):
        """Test that controls are mapped to governance primitives."""
        control = compliance_service.get_control_status("A.16.1.4", RegulatoryFramework.ISO27001)

        assert control is not None
        assert len(control.mapped_primitives) > 0
        # Incident management should map to escalation
        assert GovernancePrimitive.ESCALATION in control.mapped_primitives

    def test_gdpr_article_mappings(self, compliance_service):
        """Test GDPR-specific article mappings."""
        # Art.32 - Security of Processing
        control = compliance_service.get_control_status("Art.32", RegulatoryFramework.GDPR)
        assert control is not None
        assert GovernancePrimitive.RISK_ASSESSMENT in control.mapped_primitives

        # Art.33 - Breach Notification
        control = compliance_service.get_control_status("Art.33", RegulatoryFramework.GDPR)
        assert control is not None
        assert GovernancePrimitive.ESCALATION in control.mapped_primitives

        # Art.35 - DPIA
        control = compliance_service.get_control_status("Art.35", RegulatoryFramework.GDPR)
        assert control is not None
        assert GovernancePrimitive.RISK_ASSESSMENT in control.mapped_primitives

    def test_multiple_frameworks_coverage(self, compliance_service):
        """Test that primitives can map to multiple frameworks."""
        # Risk assessment should map to controls in all frameworks
        soc2_mapping = compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.RISK_ASSESSMENT,
            primitive_id="rsk_multi_test",
            framework=RegulatoryFramework.SOC2
        )

        iso_mapping = compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.RISK_ASSESSMENT,
            primitive_id="rsk_multi_test",
            framework=RegulatoryFramework.ISO27001
        )

        gdpr_mapping = compliance_service.map_primitive_to_controls(
            primitive_type=GovernancePrimitive.RISK_ASSESSMENT,
            primitive_id="rsk_multi_test",
            framework=RegulatoryFramework.GDPR
        )

        assert len(soc2_mapping.control_ids) > 0
        assert len(iso_mapping.control_ids) > 0
        assert len(gdpr_mapping.control_ids) > 0

        # All should reference the same primitive
        mappings = compliance_service.get_primitive_mappings("rsk_multi_test")
        assert len(mappings) == 3
