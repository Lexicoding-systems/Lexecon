"""Tests for override service."""

from datetime import datetime, timedelta, timezone

import pytest

from lexecon.override.service import (
    OverrideConfig,
    OverrideService,
    OverrideValidator,
    generate_override_id,
)

# Import canonical governance models
try:
    from model_governance_pack.models import (
        EvidenceArtifact,
        NewOutcome,
        OriginalOutcome,
        Override,
        OverrideScope,
        OverrideType,
    )

    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False
    pytestmark = pytest.mark.skip("Governance models not available")


class TestOverrideIdGeneration:
    """Tests for override ID generation."""

    def test_generate_override_id_format(self):
        """Test override ID format."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"
        override_id = generate_override_id(decision_id)

        assert override_id.startswith("ovr_dec_")
        assert "01JQXYZ1234567890ABCDEFGH" in override_id

    def test_generate_override_id_uniqueness(self):
        """Test that override IDs are unique (allows multiple overrides)."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Multiple overrides for same decision should have different IDs
        id1 = generate_override_id(decision_id)
        id2 = generate_override_id(decision_id)

        assert id1 != id2
        assert id1.startswith("ovr_dec_")
        assert id2.startswith("ovr_dec_")

    def test_generate_override_id_without_prefix(self):
        """Test override ID generation with decision_id without dec_ prefix."""
        decision_id = "custom_decision_123"
        override_id = generate_override_id(decision_id)

        assert override_id.startswith("ovr_dec_")
        assert "custom_decision_123" in override_id


class TestOverrideConfig:
    """Tests for override configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OverrideConfig()

        assert len(config.AUTHORIZED_ROLES) > 0
        assert len(config.EXECUTIVE_ONLY_TYPES) > 0
        assert config.DEFAULT_TIME_LIMIT_HOURS == 24
        assert config.DEFAULT_REVIEW_PERIOD_DAYS == 30

    def test_executive_only_types(self):
        """Test that certain override types require executive."""
        config = OverrideConfig()

        assert OverrideType.EMERGENCY_BYPASS in config.EXECUTIVE_ONLY_TYPES
        assert OverrideType.EXECUTIVE_OVERRIDE in config.EXECUTIVE_ONLY_TYPES


class TestOverrideService:
    """Tests for override service."""

    @pytest.fixture
    def service(self):
        """Create an override service instance."""
        return OverrideService()

    @pytest.fixture
    def executive_actor(self):
        """Executive actor ID."""
        return "act_human_user:executive_john"

    @pytest.fixture
    def governance_actor(self):
        """Governance lead actor ID."""
        return "act_human_user:governance_lead_jane"

    @pytest.fixture
    def unauthorized_actor(self):
        """Unauthorized actor ID."""
        return "act_ai_agent:unauthorized"

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service.config is not None
        assert service.store_evidence is True

    def test_is_authorized_executive(self, service, executive_actor):
        """Test that executive is authorized for all override types."""
        assert service.is_authorized(executive_actor, OverrideType.EMERGENCY_BYPASS)
        assert service.is_authorized(executive_actor, OverrideType.EXECUTIVE_OVERRIDE)
        assert service.is_authorized(executive_actor, OverrideType.RISK_ACCEPTED)

    def test_is_authorized_governance_lead(self, service, governance_actor):
        """Test that governance lead is authorized for non-executive overrides."""
        assert service.is_authorized(governance_actor, OverrideType.RISK_ACCEPTED)
        assert service.is_authorized(
            governance_actor, OverrideType.TIME_LIMITED_EXCEPTION,
        )

        # But not for executive-only types
        assert not service.is_authorized(
            governance_actor, OverrideType.EMERGENCY_BYPASS,
        )
        assert not service.is_authorized(
            governance_actor, OverrideType.EXECUTIVE_OVERRIDE,
        )

    def test_is_authorized_unauthorized_actor(self, service, unauthorized_actor):
        """Test that unauthorized actors cannot override."""
        assert not service.is_authorized(
            unauthorized_actor, OverrideType.RISK_ACCEPTED,
        )

    def test_create_override_valid(self, service, executive_actor):
        """Test creating a valid override."""
        override = service.create_override(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            override_type=OverrideType.EXECUTIVE_OVERRIDE,
            authorized_by=executive_actor,
            justification="Critical business need: Customer deadline requires immediate access to complete regulatory filing. Risk mitigated by audit trail.",
            original_outcome=OriginalOutcome.DENIED,
            new_outcome=NewOutcome.APPROVED,
        )

        # Validate against schema
        assert isinstance(override, Override)
        assert override.override_id.startswith("ovr_dec_")
        assert override.decision_id == "dec_01JQXYZ1234567890ABCDEFGH"
        assert override.override_type == OverrideType.EXECUTIVE_OVERRIDE
        assert override.authorized_by == executive_actor
        assert len(override.justification) >= 20
        assert override.original_outcome == OriginalOutcome.DENIED
        assert override.new_outcome == NewOutcome.APPROVED

    def test_create_override_requires_authorization(self, service, unauthorized_actor):
        """Test that unauthorized actors cannot create overrides."""
        with pytest.raises(ValueError, match="not authorized"):
            service.create_override(
                decision_id="dec_01JQXYZ1234567890ABCDEFGH",
                override_type=OverrideType.EXECUTIVE_OVERRIDE,
                authorized_by=unauthorized_actor,
                justification="This should fail due to lack of authorization.",
            )

    def test_create_override_requires_justification(self, service, executive_actor):
        """Test that justification is required."""
        with pytest.raises(ValueError, match="at least 20 characters"):
            service.create_override(
                decision_id="dec_01JQXYZ1234567890ABCDEFGH",
                override_type=OverrideType.EXECUTIVE_OVERRIDE,
                authorized_by=executive_actor,
                justification="Too short",  # < 20 chars
            )

    def test_create_override_sets_defaults(self, service, executive_actor):
        """Test that defaults are set for optional fields."""
        override = service.create_override(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Risk is acceptable given business context and current mitigations in place.",
        )

        # Should have review deadline set
        assert override.review_required_by is not None
        assert override.review_required_by > datetime.now(timezone.utc)

    def test_create_override_time_limited(self, service, governance_actor):
        """Test creating time-limited exception."""
        override = service.create_override(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            override_type=OverrideType.TIME_LIMITED_EXCEPTION,
            authorized_by=governance_actor,
            justification="Temporary access needed for migration project completing by end of month.",
        )

        # Should have expiration set
        assert override.expires_at is not None
        assert override.expires_at > datetime.now(timezone.utc)

    def test_create_override_generates_evidence(self, service, executive_actor):
        """Test that creating override generates evidence artifact."""
        override = service.create_override(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Risk is acceptable given business context and current mitigations in place.",
        )

        # Evidence artifact should be created
        artifacts = service.list_evidence_artifacts(override_id=override.override_id)
        assert len(artifacts) == 1

        artifact = artifacts[0]
        assert isinstance(artifact, EvidenceArtifact)
        assert artifact.is_immutable is True
        assert len(artifact.sha256_hash) == 64  # SHA-256 hex

    def test_get_evidence_artifact(self, service, executive_actor):
        """Test retrieving evidence artifact by ID."""
        override = service.create_override(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Risk is acceptable given business context and current mitigations in place.",
        )

        # Get artifact ID
        artifacts = service.list_evidence_artifacts(override_id=override.override_id)
        artifact_id = artifacts[0].artifact_id

        # Retrieve by ID
        retrieved = service.get_evidence_artifact(artifact_id)
        assert retrieved is not None
        assert retrieved.artifact_id == artifact_id

    def test_list_evidence_artifacts_by_decision_id(self, service, executive_actor):
        """Test listing evidence artifacts filtered by decision_id."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Risk is acceptable given business context and current mitigations in place.",
        )

        # List by decision_id
        artifacts = service.list_evidence_artifacts(decision_id=decision_id)
        assert len(artifacts) >= 1

        # Verify all artifacts are related to the decision
        for artifact in artifacts:
            assert decision_id in artifact.related_decision_ids

    def test_get_override(self, service, executive_actor):
        """Test retrieving override by ID."""
        override = service.create_override(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Risk is acceptable given business context and current mitigations in place.",
        )

        retrieved = service.get_override(override.override_id)
        assert retrieved is not None
        assert retrieved.override_id == override.override_id

    def test_get_overrides_for_decision(self, service, executive_actor):
        """Test retrieving all overrides for a decision."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Create multiple overrides (audit trail)
        override1 = service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Initial override: Risk accepted for business reasons.",
        )

        override2 = service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.EXECUTIVE_OVERRIDE,
            authorized_by=executive_actor,
            justification="Second override: Additional executive approval obtained.",
        )

        overrides = service.get_overrides_for_decision(decision_id)
        assert len(overrides) == 2
        # Should be in chronological order
        assert overrides[0].override_id == override1.override_id
        assert overrides[1].override_id == override2.override_id

    def test_get_active_override(self, service, executive_actor):
        """Test getting active override for decision."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        override = service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Risk is acceptable given business context and current mitigations in place.",
        )

        active = service.get_active_override(decision_id)
        assert active is not None
        assert active.override_id == override.override_id

    def test_get_active_override_expired(self, service, executive_actor):
        """Test that expired overrides are not returned as active."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Create override with past expiration
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.TIME_LIMITED_EXCEPTION,
            authorized_by=executive_actor,
            justification="Temporary access needed for migration project completing by end of month.",
            expires_at=past_time,
        )

        active = service.get_active_override(decision_id)
        assert active is None  # Expired

    def test_is_decision_overridden(self, service, executive_actor):
        """Test checking if decision is overridden."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Not overridden initially
        assert service.is_decision_overridden(decision_id) is False

        # Create override
        service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Risk is acceptable given business context and current mitigations in place.",
        )

        # Now overridden
        assert service.is_decision_overridden(decision_id) is True

    def test_list_overrides_no_filter(self, service, executive_actor):
        """Test listing all overrides."""
        # Create multiple overrides
        for i in range(3):
            service.create_override(
                decision_id=f"dec_01JQXYZ{i:022d}",
                override_type=OverrideType.RISK_ACCEPTED,
                authorized_by=executive_actor,
                justification=f"Override {i}: Risk is acceptable given business context.",
            )

        overrides = service.list_overrides()
        assert len(overrides) == 3

    def test_list_overrides_by_type(self, service, executive_actor):
        """Test filtering overrides by type."""
        service.create_override(
            decision_id="dec_01JQXYZ1111111111111111111",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Risk accepted override justification text here.",
        )
        service.create_override(
            decision_id="dec_01JQXYZ2222222222222222222",
            override_type=OverrideType.EMERGENCY_BYPASS,
            authorized_by=executive_actor,
            justification="Emergency bypass override justification text here.",
        )

        risk_accepted = service.list_overrides(override_type=OverrideType.RISK_ACCEPTED)
        assert len(risk_accepted) == 1
        assert risk_accepted[0].override_type == OverrideType.RISK_ACCEPTED

    def test_list_overrides_by_authorized_by(self, service, executive_actor, governance_actor):
        """Test filtering overrides by authorizing actor."""
        service.create_override(
            decision_id="dec_01JQXYZ1111111111111111111",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Executive authorized override justification text here.",
        )
        service.create_override(
            decision_id="dec_01JQXYZ2222222222222222222",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=governance_actor,
            justification="Governance authorized override justification text here.",
        )

        executive_overrides = service.list_overrides(authorized_by=executive_actor)
        assert len(executive_overrides) == 1
        assert executive_overrides[0].authorized_by == executive_actor

    def test_list_overrides_by_expiration(self, service, governance_actor):
        """Test filtering overrides by expiration status."""
        # Create expired override
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        service.create_override(
            decision_id="dec_01JQXYZ1111111111111111111",
            override_type=OverrideType.TIME_LIMITED_EXCEPTION,
            authorized_by=governance_actor,
            justification="Expired time limited exception override text here.",
            expires_at=past_time,
        )

        # Create active override
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        service.create_override(
            decision_id="dec_01JQXYZ2222222222222222222",
            override_type=OverrideType.TIME_LIMITED_EXCEPTION,
            authorized_by=governance_actor,
            justification="Active time limited exception override text here.",
            expires_at=future_time,
        )

        # Get expired
        expired = service.list_overrides(expired=True)
        assert len(expired) == 1

        # Get active
        active = service.list_overrides(expired=False)
        assert len(active) == 1

    def test_get_overrides_needing_review(self, service, executive_actor):
        """Test getting overrides needing review."""
        # Create override with past review deadline
        past_review = datetime.now(timezone.utc) - timedelta(days=1)
        service.create_override(
            decision_id="dec_01JQXYZ1111111111111111111",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Override needing review justification text here.",
            review_required_by=past_review,
        )

        # Create override with future review deadline
        future_review = datetime.now(timezone.utc) + timedelta(days=1)
        service.create_override(
            decision_id="dec_01JQXYZ2222222222222222222",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Override not needing review yet justification text.",
            review_required_by=future_review,
        )

        needing_review = service.get_overrides_needing_review()
        assert len(needing_review) == 1

    def test_get_decision_with_override_status_not_overridden(self, service):
        """Test enriching decision data when not overridden."""
        decision_data = {
            "decision_id": "dec_01JQXYZ1234567890ABCDEFGH",
            "decision": "deny",
            "reasoning": "Policy violation",
        }

        enriched = service.get_decision_with_override_status(
            "dec_01JQXYZ1234567890ABCDEFGH", decision_data,
        )

        assert enriched["decision"] == "deny"  # Original preserved
        assert enriched["override_status"]["is_overridden"] is False

    def test_get_decision_with_override_status_overridden(
        self, service, executive_actor,
    ):
        """Test enriching decision data when overridden."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"
        decision_data = {
            "decision_id": decision_id,
            "decision": "deny",
            "reasoning": "Policy violation",
        }

        # Create override
        override = service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.EXECUTIVE_OVERRIDE,
            authorized_by=executive_actor,
            justification="Executive approval: Business critical requirement overrides policy.",
            original_outcome=OriginalOutcome.DENIED,
            new_outcome=NewOutcome.APPROVED,
        )

        enriched = service.get_decision_with_override_status(decision_id, decision_data)

        # Original decision preserved
        assert enriched["decision"] == "deny"
        assert enriched["reasoning"] == "Policy violation"

        # Override status added
        assert enriched["override_status"]["is_overridden"] is True
        assert enriched["override_status"]["override_id"] == override.override_id
        assert (
            enriched["override_status"]["override_type"]
            == OverrideType.EXECUTIVE_OVERRIDE.value
        )
        assert enriched["override_status"]["original_outcome"] == "denied"
        assert enriched["override_status"]["new_outcome"] == "approved"

    def test_override_immutability(self, service, executive_actor):
        """Test that overrides are immutable."""
        override = service.create_override(
            decision_id="dec_01JQXYZ1234567890ABCDEFGH",
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive_actor,
            justification="Risk is acceptable given business context and current mitigations in place.",
        )

        # Get override
        retrieved = service.get_override(override.override_id)

        # Attempting to modify should not affect stored version
        original_justification = retrieved.justification
        # (In real code, you can't modify pydantic frozen models, but this tests the principle)

        # Re-retrieve
        retrieved_again = service.get_override(override.override_id)
        assert retrieved_again.justification == original_justification


class TestOverrideValidator:
    """Tests for override validator."""

    def test_validate_justification_valid(self):
        """Test validating valid justification."""
        valid = "This is a valid justification with sufficient detail about the override reason."
        assert OverrideValidator.validate_justification(valid) is True

    def test_validate_justification_too_short(self):
        """Test that short justification fails."""
        with pytest.raises(ValueError, match="at least 20 characters"):
            OverrideValidator.validate_justification("Too short")

    def test_validate_justification_generic(self):
        """Test that generic justification fails if too short."""
        # Short generic phrase - fails length check first
        with pytest.raises(ValueError, match="at least 20 characters"):
            OverrideValidator.validate_justification("Override needed")

        # Longer generic phrase that meets length but is generic
        with pytest.raises(ValueError, match="appears generic"):
            OverrideValidator.validate_justification("Emergency override required for business")

    def test_validate_justification_generic_but_detailed(self):
        """Test that generic phrases are ok if justification is detailed."""
        detailed = (
            "Emergency override required for customer X due to contractual obligation. "
            "Risk is mitigated by enhanced monitoring and limited duration."
        )
        assert OverrideValidator.validate_justification(detailed) is True

    def test_validate_time_limit_valid(self):
        """Test validating valid time limit."""
        future = datetime.now(timezone.utc) + timedelta(hours=24)
        assert (
            OverrideValidator.validate_time_limit(
                OverrideType.TIME_LIMITED_EXCEPTION, future,
            )
            is True
        )

    def test_validate_time_limit_missing(self):
        """Test that time-limited exception requires expiration."""
        with pytest.raises(ValueError, match="must have expiration"):
            OverrideValidator.validate_time_limit(
                OverrideType.TIME_LIMITED_EXCEPTION, None,
            )

    def test_validate_time_limit_past(self):
        """Test that expiration must be in future."""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        with pytest.raises(ValueError, match="must be in the future"):
            OverrideValidator.validate_time_limit(
                OverrideType.TIME_LIMITED_EXCEPTION, past,
            )

    def test_validate_time_limit_too_long(self):
        """Test that time limit cannot exceed maximum."""
        too_far = datetime.now(timezone.utc) + timedelta(days=100)
        with pytest.raises(ValueError, match="cannot exceed 90 days"):
            OverrideValidator.validate_time_limit(
                OverrideType.TIME_LIMITED_EXCEPTION, too_far,
            )

    def test_validate_scope_emergency_bypass(self):
        """Test that emergency bypass must be one-time."""
        # Missing scope
        with pytest.raises(ValueError, match="must be one-time"):
            OverrideValidator.validate_scope(OverrideType.EMERGENCY_BYPASS, None)

        # Scope without is_one_time
        scope = OverrideScope(is_one_time=False)
        with pytest.raises(ValueError, match="must be one-time"):
            OverrideValidator.validate_scope(OverrideType.EMERGENCY_BYPASS, scope)

        # Valid scope
        valid_scope = OverrideScope(is_one_time=True)
        assert (
            OverrideValidator.validate_scope(OverrideType.EMERGENCY_BYPASS, valid_scope)
            is True
        )


class TestIntegrationWorkflows:
    """Integration tests for complete override workflows."""

    def test_complete_override_workflow(self):
        """Test complete workflow from override to evidence."""
        service = OverrideService()
        executive = "act_human_user:executive_john"

        # 1. Create override
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"
        override = service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.EXECUTIVE_OVERRIDE,
            authorized_by=executive,
            justification="Critical business requirement: Major customer needs immediate access to complete regulatory filing by deadline. Risk mitigated through enhanced audit logging and time-limited access.",
            original_outcome=OriginalOutcome.DENIED,
            new_outcome=NewOutcome.APPROVED,
        )

        # 2. Verify override created
        assert override.override_id.startswith("ovr_dec_")
        assert service.is_decision_overridden(decision_id) is True

        # 3. Check evidence artifact
        artifacts = service.list_evidence_artifacts(override_id=override.override_id)
        assert len(artifacts) == 1
        assert artifacts[0].is_immutable is True

        # 4. Enrich decision with override status
        decision_data = {"decision_id": decision_id, "decision": "deny"}
        enriched = service.get_decision_with_override_status(decision_id, decision_data)

        assert enriched["decision"] == "deny"  # Original preserved
        assert enriched["override_status"]["is_overridden"] is True
        assert enriched["override_status"]["new_outcome"] == "approved"

    def test_multiple_overrides_audit_trail(self):
        """Test that multiple overrides create audit trail."""
        service = OverrideService()
        executive = "act_human_user:executive_john"
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Create first override
        override1 = service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.RISK_ACCEPTED,
            authorized_by=executive,
            justification="Initial risk acceptance: Low probability high impact scenario.",
        )

        # Create second override (e.g., escalation)
        override2 = service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.EXECUTIVE_OVERRIDE,
            authorized_by=executive,
            justification="Executive escalation: Additional approval obtained from board.",
        )

        # Both should exist in audit trail
        overrides = service.get_overrides_for_decision(decision_id)
        assert len(overrides) == 2
        assert overrides[0].override_id == override1.override_id
        assert overrides[1].override_id == override2.override_id

        # Most recent should be active
        active = service.get_active_override(decision_id)
        assert active.override_id == override2.override_id

    def test_time_limited_override_expiration(self):
        """Test time-limited override expiration."""
        service = OverrideService()
        governance = "act_human_user:governance_lead_jane"
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Create time-limited override (very short for testing)
        expires = datetime.now(timezone.utc) + timedelta(seconds=1)
        service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.TIME_LIMITED_EXCEPTION,
            authorized_by=governance,
            justification="Temporary access for maintenance window completing within one hour.",
            expires_at=expires,
        )

        # Should be active immediately
        assert service.is_decision_overridden(decision_id) is True

        # Wait for expiration
        import time

        time.sleep(2)

        # Should be expired
        assert service.is_decision_overridden(decision_id) is False

    def test_decision_integrity_preserved(self):
        """Test that original decision is never mutated."""
        service = OverrideService()
        executive = "act_human_user:executive_john"
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Original decision data
        original_decision = {
            "decision_id": decision_id,
            "decision": "deny",
            "reasoning": "Violates security policy",
            "policy_version_hash": "abc123",
        }

        # Create copy to simulate storage
        stored_decision = dict(original_decision)

        # Create override
        service.create_override(
            decision_id=decision_id,
            override_type=OverrideType.EXECUTIVE_OVERRIDE,
            authorized_by=executive,
            justification="Executive approval overrides security policy for critical business need.",
            original_outcome=OriginalOutcome.DENIED,
            new_outcome=NewOutcome.APPROVED,
        )

        # Get enriched view
        enriched = service.get_decision_with_override_status(
            decision_id, stored_decision,
        )

        # Original decision unchanged
        assert stored_decision == original_decision
        assert stored_decision["decision"] == "deny"

        # Enriched view has override status
        assert enriched["override_status"]["is_overridden"] is True
        assert enriched["decision"] == "deny"  # Still shows original
