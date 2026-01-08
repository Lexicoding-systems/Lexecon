"""
Tests for Lexecon Governance Pydantic Models.

These tests verify that the Pydantic models correctly enforce
the constraints defined in the canonical JSON schemas.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from model_governance_pack.models import (  # Action; Actor; Compliance Control; Context; Decision; Escalation; Evidence Artifact; Override; Policy; Resource; Risk
    Action,
    ActionCategory,
    Actor,
    ActorType,
    ArtifactType,
    Behavioral,
    ComplianceControl,
    ComplianceFramework,
    Constraint,
    Context,
    Decision,
    DecisionOutcome,
    DeploymentEnvironment,
    DigitalSignature,
    Environment,
    Escalation,
    EscalationPriority,
    EscalationStatus,
    EscalationTrigger,
    EvidenceArtifact,
    NewOutcome,
    OriginalOutcome,
    Override,
    OverrideScope,
    OverrideType,
    Policy,
    PolicyMode,
    Relation,
    RelationType,
    Resolution,
    ResolutionOutcome,
    Resource,
    ResourceClassification,
    ResourceType,
    Risk,
    RiskDimensions,
    RiskFactor,
    RiskLevel,
    Temporal,
    Term,
    TermType,
)

# =============================================================================
# Decision Model Tests
# =============================================================================


class TestDecision:
    """Tests for Decision model."""

    def test_valid_decision_required_fields_only(self):
        """Test Decision with only required fields."""
        decision = Decision(
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            request_id="req-123",
            actor_id="act_ai_agent:claude",
            action_id="axn_read:file_contents",
            outcome=DecisionOutcome.APPROVED,
            timestamp=datetime.now(timezone.utc),
            policy_ids=["pol_default_v1"],
        )
        assert decision.outcome == DecisionOutcome.APPROVED
        assert decision.reasoning is None
        assert decision.metadata is None

    def test_valid_decision_all_fields(self):
        """Test Decision with all fields populated."""
        decision = Decision(
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            request_id="req-123",
            actor_id="act_ai_agent:claude",
            action_id="axn_read:file_contents",
            resource_id="res_pii:customer/profiles",
            outcome=DecisionOutcome.CONDITIONAL,
            timestamp=datetime.now(timezone.utc),
            policy_ids=["pol_default_v1", "pol_security_v2"],
            reasoning="Approved with conditions due to PII access",
            risk_assessment="rsk_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            conditions=["log_access", "notify_dpo"],
            evidence_ids=["evd_log_a1b2c3d4"],
            context_snapshot={"session": "abc123"},
            metadata={"reviewer": "system"},
        )
        assert decision.outcome == DecisionOutcome.CONDITIONAL
        assert len(decision.conditions) == 2

    def test_invalid_decision_id_pattern(self):
        """Test that invalid decision_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Decision(
                decision_id="invalid-id",  # Should match ^dec_[A-Z0-9]{26}$
                request_id="req-123",
                actor_id="act_ai_agent:claude",
                action_id="axn_read:file_contents",
                outcome=DecisionOutcome.APPROVED,
                timestamp=datetime.now(timezone.utc),
                policy_ids=["pol_default_v1"],
            )
        assert "decision_id" in str(exc_info.value)

    def test_invalid_actor_id_pattern(self):
        """Test that invalid actor_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Decision(
                decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                request_id="req-123",
                actor_id="invalid_actor",  # Should match ^act_[a-z_]+:.+$
                action_id="axn_read:file_contents",
                outcome=DecisionOutcome.APPROVED,
                timestamp=datetime.now(timezone.utc),
                policy_ids=["pol_default_v1"],
            )
        assert "actor_id" in str(exc_info.value)

    def test_invalid_action_id_pattern(self):
        """Test that invalid action_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Decision(
                decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                request_id="req-123",
                actor_id="act_ai_agent:claude",
                action_id="bad_action",  # Should match ^axn_[a-z_]+:.+$
                outcome=DecisionOutcome.APPROVED,
                timestamp=datetime.now(timezone.utc),
                policy_ids=["pol_default_v1"],
            )
        assert "action_id" in str(exc_info.value)

    def test_missing_required_field(self):
        """Test that missing required field raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Decision(
                decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                request_id="req-123",
                actor_id="act_ai_agent:claude",
                # action_id missing
                outcome=DecisionOutcome.APPROVED,
                timestamp=datetime.now(timezone.utc),
                policy_ids=["pol_default_v1"],
            )
        assert "action_id" in str(exc_info.value)

    def test_empty_policy_ids_fails(self):
        """Test that empty policy_ids array fails min_length validation."""
        with pytest.raises(ValidationError) as exc_info:
            Decision(
                decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                request_id="req-123",
                actor_id="act_ai_agent:claude",
                action_id="axn_read:file_contents",
                outcome=DecisionOutcome.APPROVED,
                timestamp=datetime.now(timezone.utc),
                policy_ids=[],  # minItems: 1
            )
        assert "policy_ids" in str(exc_info.value)

    def test_invalid_outcome_enum(self):
        """Test that invalid outcome enum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Decision(
                decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                request_id="req-123",
                actor_id="act_ai_agent:claude",
                action_id="axn_read:file_contents",
                outcome="invalid_outcome",
                timestamp=datetime.now(timezone.utc),
                policy_ids=["pol_default_v1"],
            )
        assert "outcome" in str(exc_info.value)

    def test_invalid_resource_id_pattern(self):
        """Test that invalid resource_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Decision(
                decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                request_id="req-123",
                actor_id="act_ai_agent:claude",
                action_id="axn_read:file_contents",
                resource_id="bad_resource",  # Should match ^res_[a-z_]+:.+$
                outcome=DecisionOutcome.APPROVED,
                timestamp=datetime.now(timezone.utc),
                policy_ids=["pol_default_v1"],
            )
        assert "resource_id" in str(exc_info.value)

    def test_invalid_risk_assessment_pattern(self):
        """Test that invalid risk_assessment pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Decision(
                decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                request_id="req-123",
                actor_id="act_ai_agent:claude",
                action_id="axn_read:file_contents",
                outcome=DecisionOutcome.APPROVED,
                timestamp=datetime.now(timezone.utc),
                policy_ids=["pol_default_v1"],
                risk_assessment="bad_risk",  # Should match ^rsk_dec_.+$
            )
        assert "risk_assessment" in str(exc_info.value)


# =============================================================================
# Policy Model Tests
# =============================================================================


class TestPolicy:
    """Tests for Policy model."""

    def test_valid_policy_required_fields_only(self):
        """Test Policy with only required fields."""
        policy = Policy(
            policy_id="pol_acme_security_v1",
            name="Security Policy",
            version="1.0.0",
            mode=PolicyMode.STRICT,
            terms=[
                Term(id="actor:user", type=TermType.ACTOR, name="User"),
            ],
            relations=[
                Relation(
                    type=RelationType.PERMITS,
                    subject="actor:user",
                    action="action:read",
                ),
            ],
        )
        assert policy.mode == PolicyMode.STRICT
        assert policy.description is None

    def test_valid_policy_all_fields(self):
        """Test Policy with all fields populated."""
        policy = Policy(
            policy_id="pol_acme_security_v1",
            name="Security Policy",
            version="1.0.0",
            mode=PolicyMode.PARANOID,
            terms=[
                Term(
                    id="actor:user",
                    type=TermType.ACTOR,
                    name="User",
                    description="Human user",
                    attributes={"trust_level": 50},
                ),
            ],
            relations=[
                Relation(
                    type=RelationType.FORBIDS,
                    subject="actor:model",
                    action="action:write",
                    object="data:pii",
                    conditions=["unless_authorized"],
                    justification="Protect PII from AI writes",
                ),
            ],
            description="Enterprise security policy",
            compliance_frameworks=["SOC 2", "GDPR"],
            constraints=[
                Constraint(
                    name="high_risk_block",
                    condition="risk_level >= 4",
                    action="deny",
                    justification="Block high-risk actions",
                ),
            ],
            effective_from=datetime.now(timezone.utc),
            effective_until=datetime(2027, 1, 1, tzinfo=timezone.utc),
            metadata={"author": "security_team"},
        )
        assert policy.mode == PolicyMode.PARANOID
        assert len(policy.compliance_frameworks) == 2

    def test_invalid_policy_id_pattern(self):
        """Test that invalid policy_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Policy(
                policy_id="invalid-policy-id",  # Should match ^pol_[a-z0-9_]+_v[0-9]+$
                name="Test Policy",
                version="1.0.0",
                mode=PolicyMode.STRICT,
                terms=[Term(id="actor:user", type=TermType.ACTOR, name="User")],
                relations=[
                    Relation(
                        type=RelationType.PERMITS,
                        subject="actor:user",
                        action="action:read",
                    )
                ],
            )
        assert "policy_id" in str(exc_info.value)

    def test_invalid_version_pattern(self):
        """Test that invalid version pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Policy(
                policy_id="pol_test_v1",
                name="Test Policy",
                version="v1.0",  # Should match ^[0-9]+\.[0-9]+\.[0-9]+$
                mode=PolicyMode.STRICT,
                terms=[Term(id="actor:user", type=TermType.ACTOR, name="User")],
                relations=[
                    Relation(
                        type=RelationType.PERMITS,
                        subject="actor:user",
                        action="action:read",
                    )
                ],
            )
        assert "version" in str(exc_info.value)

    def test_name_too_short(self):
        """Test that name shorter than minLength raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Policy(
                policy_id="pol_test_v1",
                name="AB",  # minLength: 3
                version="1.0.0",
                mode=PolicyMode.STRICT,
                terms=[Term(id="actor:user", type=TermType.ACTOR, name="User")],
                relations=[
                    Relation(
                        type=RelationType.PERMITS,
                        subject="actor:user",
                        action="action:read",
                    )
                ],
            )
        assert "name" in str(exc_info.value)

    def test_name_too_long(self):
        """Test that name longer than maxLength raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Policy(
                policy_id="pol_test_v1",
                name="A" * 129,  # maxLength: 128
                version="1.0.0",
                mode=PolicyMode.STRICT,
                terms=[Term(id="actor:user", type=TermType.ACTOR, name="User")],
                relations=[
                    Relation(
                        type=RelationType.PERMITS,
                        subject="actor:user",
                        action="action:read",
                    )
                ],
            )
        assert "name" in str(exc_info.value)


# =============================================================================
# Actor Model Tests
# =============================================================================


class TestActor:
    """Tests for Actor model."""

    def test_valid_actor_required_fields_only(self):
        """Test Actor with only required fields."""
        actor = Actor(
            actor_id="act_ai_agent:claude_v3",
            actor_type=ActorType.AI_AGENT,
            name="Claude Assistant",
        )
        assert actor.actor_type == ActorType.AI_AGENT
        assert actor.is_active is True  # default value

    def test_valid_actor_all_fields(self):
        """Test Actor with all fields populated."""
        actor = Actor(
            actor_id="act_human_user:john_doe",
            actor_type=ActorType.HUMAN_USER,
            name="John Doe",
            description="Senior Engineer",
            parent_actor_id="act_organizational_role:engineering",
            roles=["developer", "reviewer"],
            trust_level=75,
            is_active=True,
            attributes={"department": "engineering", "clearance": "secret"},
            metadata={"hire_date": "2023-01-15"},
        )
        assert actor.trust_level == 75
        assert len(actor.roles) == 2

    def test_invalid_actor_id_pattern(self):
        """Test that invalid actor_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Actor(
                actor_id="bad_actor_id",  # Should match ^act_[a-z_]+:.+$
                actor_type=ActorType.HUMAN_USER,
                name="Test User",
            )
        assert "actor_id" in str(exc_info.value)

    def test_trust_level_below_minimum(self):
        """Test that trust_level below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Actor(
                actor_id="act_human_user:test",
                actor_type=ActorType.HUMAN_USER,
                name="Test User",
                trust_level=-1,  # minimum: 0
            )
        assert "trust_level" in str(exc_info.value)

    def test_trust_level_above_maximum(self):
        """Test that trust_level above 100 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Actor(
                actor_id="act_human_user:test",
                actor_type=ActorType.HUMAN_USER,
                name="Test User",
                trust_level=101,  # maximum: 100
            )
        assert "trust_level" in str(exc_info.value)

    def test_default_is_active(self):
        """Test that is_active defaults to True."""
        actor = Actor(
            actor_id="act_system_service:scheduler",
            actor_type=ActorType.SYSTEM_SERVICE,
            name="Scheduler Service",
        )
        assert actor.is_active is True


# =============================================================================
# Action Model Tests
# =============================================================================


class TestAction:
    """Tests for Action model."""

    def test_valid_action_required_fields_only(self):
        """Test Action with only required fields."""
        action = Action(
            action_id="axn_read:file_contents",
            category=ActionCategory.READ,
            operation="file_contents",
        )
        assert action.category == ActionCategory.READ
        assert action.requires_confirmation is False  # default value

    def test_valid_action_all_fields(self):
        """Test Action with all fields populated."""
        action = Action(
            action_id="axn_execute:shell_command",
            category=ActionCategory.EXECUTE,
            operation="shell_command",
            description="Execute a shell command",
            risk_weight=8,
            is_reversible=False,
            requires_confirmation=True,
            parameters_schema={"type": "object", "properties": {"command": {"type": "string"}}},
            metadata={"added_by": "security_team"},
        )
        assert action.risk_weight == 8
        assert action.requires_confirmation is True

    def test_invalid_action_id_pattern(self):
        """Test that invalid action_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Action(
                action_id="bad_action_id",  # Should match ^axn_[a-z_]+:.+$
                category=ActionCategory.READ,
                operation="test",
            )
        assert "action_id" in str(exc_info.value)

    def test_risk_weight_below_minimum(self):
        """Test that risk_weight below 1 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Action(
                action_id="axn_read:test",
                category=ActionCategory.READ,
                operation="test",
                risk_weight=0,  # minimum: 1
            )
        assert "risk_weight" in str(exc_info.value)

    def test_risk_weight_above_maximum(self):
        """Test that risk_weight above 10 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Action(
                action_id="axn_read:test",
                category=ActionCategory.READ,
                operation="test",
                risk_weight=11,  # maximum: 10
            )
        assert "risk_weight" in str(exc_info.value)


# =============================================================================
# Resource Model Tests
# =============================================================================


class TestResource:
    """Tests for Resource model."""

    def test_valid_resource_required_fields_only(self):
        """Test Resource with only required fields."""
        resource = Resource(
            resource_id="res_pii:customer_data",
            classification=ResourceClassification.CONFIDENTIAL,
            name="Customer Data",
        )
        assert resource.classification == ResourceClassification.CONFIDENTIAL

    def test_valid_resource_all_fields(self):
        """Test Resource with all fields populated."""
        resource = Resource(
            resource_id="res_critical:encryption_keys",
            classification=ResourceClassification.CRITICAL,
            name="Encryption Keys",
            resource_type=ResourceType.DATA,
            description="Master encryption keys for data at rest",
            owner_actor_id="act_organizational_role:security",
            compliance_tags=["pci_dss", "sox"],
            retention_days=2555,
            is_encrypted=True,
            metadata={"rotation_policy": "90_days"},
        )
        assert resource.classification == ResourceClassification.CRITICAL
        assert resource.is_encrypted is True

    def test_invalid_resource_id_pattern(self):
        """Test that invalid resource_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Resource(
                resource_id="bad_resource_id",  # Should match ^res_[a-z_]+:.+$
                classification=ResourceClassification.PUBLIC,
                name="Test Resource",
            )
        assert "resource_id" in str(exc_info.value)


# =============================================================================
# Context Model Tests
# =============================================================================


class TestContext:
    """Tests for Context model."""

    def test_valid_context_required_fields_only(self):
        """Test Context with only required fields."""
        context = Context(
            context_id="ctx_session_abc123",
            session_id="session_abc123",
            timestamp=datetime.now(timezone.utc),
        )
        assert context.user_intent is None

    def test_valid_context_all_fields(self):
        """Test Context with all fields populated."""
        context = Context(
            context_id="ctx_session_abc123",
            session_id="session_abc123",
            timestamp=datetime.now(timezone.utc),
            user_intent="Review quarterly report",
            environment=Environment(
                deployment=DeploymentEnvironment.PRODUCTION,
                region="us-east-1",
                network_zone="internal",
            ),
            temporal=Temporal(
                is_business_hours=True,
                day_of_week="Monday",
                timezone="America/New_York",
            ),
            behavioral=Behavioral(
                request_rate=5.2,
                anomaly_score=0.15,
                session_action_count=42,
            ),
            prior_decisions=["dec_01HQXK5M8N2P3R4S5T6V7W8X9Y"],
            custom={"client_version": "2.1.0"},
        )
        assert context.environment.deployment == DeploymentEnvironment.PRODUCTION
        assert context.behavioral.anomaly_score == 0.15

    def test_invalid_context_id_pattern(self):
        """Test that invalid context_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Context(
                context_id="bad_context_id",  # Should match ^ctx_.+$
                session_id="session_123",
                timestamp=datetime.now(timezone.utc),
            )
        assert "context_id" in str(exc_info.value)


# =============================================================================
# Risk Model Tests
# =============================================================================


class TestRisk:
    """Tests for Risk model."""

    def test_valid_risk_required_fields_only(self):
        """Test Risk with only required fields."""
        risk = Risk(
            risk_id="rsk_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            overall_score=45,
            timestamp=datetime.now(timezone.utc),
        )
        assert risk.overall_score == 45
        assert risk.risk_level is None

    def test_valid_risk_all_fields(self):
        """Test Risk with all fields populated."""
        risk = Risk(
            risk_id="rsk_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            overall_score=72,
            timestamp=datetime.now(timezone.utc),
            risk_level=RiskLevel.HIGH,
            dimensions=RiskDimensions(
                security=80,
                privacy=65,
                compliance=70,
                operational=50,
                reputational=75,
                financial=60,
            ),
            likelihood=0.65,
            impact=4,
            factors=[
                RiskFactor(name="pii_access", weight=0.4, value=0.8),
                RiskFactor(name="external_network", weight=0.3, value=0.5),
            ],
            mitigations_applied=["encryption", "audit_logging"],
            metadata={"model_version": "risk_v2"},
        )
        assert risk.risk_level == RiskLevel.HIGH
        assert risk.dimensions.security == 80

    def test_invalid_risk_id_pattern(self):
        """Test that invalid risk_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Risk(
                risk_id="bad_risk_id",  # Should match ^rsk_dec_.+$
                decision_id="dec_123",
                overall_score=50,
                timestamp=datetime.now(timezone.utc),
            )
        assert "risk_id" in str(exc_info.value)

    def test_overall_score_below_minimum(self):
        """Test that overall_score below 1 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Risk(
                risk_id="rsk_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                decision_id="dec_123",
                overall_score=0,  # minimum: 1
                timestamp=datetime.now(timezone.utc),
            )
        assert "overall_score" in str(exc_info.value)

    def test_overall_score_above_maximum(self):
        """Test that overall_score above 100 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Risk(
                risk_id="rsk_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                decision_id="dec_123",
                overall_score=101,  # maximum: 100
                timestamp=datetime.now(timezone.utc),
            )
        assert "overall_score" in str(exc_info.value)

    def test_likelihood_bounds(self):
        """Test that likelihood outside 0-1 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Risk(
                risk_id="rsk_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                decision_id="dec_123",
                overall_score=50,
                timestamp=datetime.now(timezone.utc),
                likelihood=1.5,  # maximum: 1
            )
        assert "likelihood" in str(exc_info.value)

    def test_impact_bounds(self):
        """Test that impact outside 1-5 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Risk(
                risk_id="rsk_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                decision_id="dec_123",
                overall_score=50,
                timestamp=datetime.now(timezone.utc),
                impact=6,  # maximum: 5
            )
        assert "impact" in str(exc_info.value)


# =============================================================================
# ComplianceControl Model Tests
# =============================================================================


class TestComplianceControl:
    """Tests for ComplianceControl model."""

    def test_valid_compliance_control_required_fields_only(self):
        """Test ComplianceControl with only required fields."""
        control = ComplianceControl(
            control_id="ctl_soc2:CC6.1",
            framework=ComplianceFramework.SOC2,
            control_ref="CC6.1",
            name="Logical Access Controls",
        )
        assert control.framework == ComplianceFramework.SOC2
        assert control.is_active is True  # default value

    def test_valid_compliance_control_all_fields(self):
        """Test ComplianceControl with all fields populated."""
        control = ComplianceControl(
            control_id="ctl_hipaa:164.312a",
            framework=ComplianceFramework.HIPAA,
            control_ref="164.312(a)",
            name="Access Control",
            description="Implement technical policies for access to ePHI",
            category="Technical Safeguards",
            policy_mappings=["pol_healthcare_v1", "pol_access_control_v2"],
            evidence_requirements=["access_logs", "audit_reports"],
            test_procedure="Review access logs quarterly",
            is_active=True,
            metadata={"last_audit": "2025-12-01"},
        )
        assert control.framework == ComplianceFramework.HIPAA
        assert len(control.policy_mappings) == 2

    def test_invalid_control_id_pattern(self):
        """Test that invalid control_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ComplianceControl(
                control_id="bad_control_id",  # Should match ^ctl_[a-z0-9_]+:.+$
                framework=ComplianceFramework.SOC2,
                control_ref="CC6.1",
                name="Test Control",
            )
        assert "control_id" in str(exc_info.value)


# =============================================================================
# Override Model Tests
# =============================================================================


class TestOverride:
    """Tests for Override model."""

    def test_valid_override_required_fields_only(self):
        """Test Override with only required fields."""
        override = Override(
            override_id="ovr_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y_001",
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            override_type=OverrideType.EMERGENCY_BYPASS,
            authorized_by="act_human_user:ciso",
            justification="Emergency access required for incident response - ticket INC-12345",
            timestamp=datetime.now(timezone.utc),
        )
        assert override.override_type == OverrideType.EMERGENCY_BYPASS

    def test_valid_override_all_fields(self):
        """Test Override with all fields populated."""
        override = Override(
            override_id="ovr_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y_001",
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            override_type=OverrideType.TIME_LIMITED_EXCEPTION,
            authorized_by="act_human_user:cto",
            justification="Temporary exception for critical deployment - approved by security",
            timestamp=datetime.now(timezone.utc),
            original_outcome=OriginalOutcome.DENIED,
            new_outcome=NewOutcome.CONDITIONAL,
            expires_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            scope=OverrideScope(
                is_one_time=False,
                applies_to_policy="pol_deployment_v1",
                applies_to_actor="act_system_service:deployer",
            ),
            review_required_by=datetime(2026, 1, 10, tzinfo=timezone.utc),
            evidence_ids=["evd_attestation_abc123"],
            metadata={"ticket": "CHG-98765"},
        )
        assert override.original_outcome == OriginalOutcome.DENIED
        assert override.new_outcome == NewOutcome.CONDITIONAL

    def test_invalid_override_id_pattern(self):
        """Test that invalid override_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Override(
                override_id="bad_override_id",  # Should match ^ovr_dec_.+$
                decision_id="dec_123",
                override_type=OverrideType.EMERGENCY_BYPASS,
                authorized_by="act_human_user:admin",
                justification="This is a valid justification with enough characters",
                timestamp=datetime.now(timezone.utc),
            )
        assert "override_id" in str(exc_info.value)

    def test_justification_too_short(self):
        """Test that justification shorter than 20 chars raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Override(
                override_id="ovr_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y_001",
                decision_id="dec_123",
                override_type=OverrideType.EMERGENCY_BYPASS,
                authorized_by="act_human_user:admin",
                justification="Too short",  # minLength: 20
                timestamp=datetime.now(timezone.utc),
            )
        assert "justification" in str(exc_info.value)


# =============================================================================
# Escalation Model Tests
# =============================================================================


class TestEscalation:
    """Tests for Escalation model."""

    def test_valid_escalation_required_fields_only(self):
        """Test Escalation with only required fields."""
        escalation = Escalation(
            escalation_id="esc_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            trigger=EscalationTrigger.RISK_THRESHOLD,
            escalated_to=["act_human_user:security_reviewer"],
            status=EscalationStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        assert escalation.status == EscalationStatus.PENDING

    def test_valid_escalation_all_fields(self):
        """Test Escalation with all fields populated."""
        escalation = Escalation(
            escalation_id="esc_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            trigger=EscalationTrigger.POLICY_CONFLICT,
            escalated_to=["act_human_user:reviewer1", "act_human_user:reviewer2"],
            status=EscalationStatus.RESOLVED,
            created_at=datetime.now(timezone.utc),
            priority=EscalationPriority.HIGH,
            sla_deadline=datetime(2026, 1, 5, tzinfo=timezone.utc),
            acknowledged_at=datetime.now(timezone.utc),
            acknowledged_by="act_human_user:reviewer1",
            resolved_at=datetime.now(timezone.utc),
            resolution=Resolution(
                outcome=ResolutionOutcome.APPROVED,
                resolved_by="act_human_user:reviewer1",
                notes="Reviewed and approved after verifying business justification",
            ),
            context_summary="Request to access production database for debugging",
            metadata={"escalation_count": 1},
        )
        assert escalation.resolution.outcome == ResolutionOutcome.APPROVED

    def test_invalid_escalation_id_pattern(self):
        """Test that invalid escalation_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Escalation(
                escalation_id="bad_escalation_id",  # Should match ^esc_dec_.+$
                decision_id="dec_123",
                trigger=EscalationTrigger.RISK_THRESHOLD,
                escalated_to=["act_human_user:reviewer"],
                status=EscalationStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
        assert "escalation_id" in str(exc_info.value)

    def test_empty_escalated_to_fails(self):
        """Test that empty escalated_to array fails min_length validation."""
        with pytest.raises(ValidationError) as exc_info:
            Escalation(
                escalation_id="esc_dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
                decision_id="dec_123",
                trigger=EscalationTrigger.RISK_THRESHOLD,
                escalated_to=[],  # minItems: 1
                status=EscalationStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
        assert "escalated_to" in str(exc_info.value)


# =============================================================================
# EvidenceArtifact Model Tests
# =============================================================================


class TestEvidenceArtifact:
    """Tests for EvidenceArtifact model."""

    def test_valid_evidence_artifact_required_fields_only(self):
        """Test EvidenceArtifact with only required fields."""
        artifact = EvidenceArtifact(
            artifact_id="evd_log_a1b2c3d4",
            artifact_type=ArtifactType.DECISION_LOG,
            sha256_hash="a" * 64,
            created_at=datetime.now(timezone.utc),
            source="lexecon_decision_service",
        )
        assert artifact.artifact_type == ArtifactType.DECISION_LOG
        assert artifact.is_immutable is True  # default value

    def test_valid_evidence_artifact_all_fields(self):
        """Test EvidenceArtifact with all fields populated."""
        artifact = EvidenceArtifact(
            artifact_id="evd_attestation_b2c3d4e5",
            artifact_type=ArtifactType.ATTESTATION,
            sha256_hash="b" * 64,
            created_at=datetime.now(timezone.utc),
            source="compliance_service",
            content_type="application/json",
            size_bytes=4096,
            storage_uri="https://storage.example.com/artifacts/b2c3d4e5",
            related_decision_ids=["dec_01HQXK5M8N2P3R4S5T6V7W8X9Y"],
            related_control_ids=["ctl_soc2:CC6.1"],
            digital_signature=DigitalSignature(
                algorithm="RS256",
                signature="base64_encoded_signature",
                signer_id="act_system_service:signer",
                signed_at=datetime.now(timezone.utc),
            ),
            retention_until=datetime(2030, 1, 1, tzinfo=timezone.utc),
            is_immutable=True,
            metadata={"version": "1.0"},
        )
        assert artifact.size_bytes == 4096
        assert artifact.digital_signature.algorithm == "RS256"

    def test_invalid_artifact_id_pattern(self):
        """Test that invalid artifact_id pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EvidenceArtifact(
                artifact_id="bad_artifact_id",  # Should match ^evd_[a-z]+_[a-f0-9]{8}$
                artifact_type=ArtifactType.DECISION_LOG,
                sha256_hash="a" * 64,
                created_at=datetime.now(timezone.utc),
                source="test",
            )
        assert "artifact_id" in str(exc_info.value)

    def test_invalid_sha256_hash_pattern(self):
        """Test that invalid sha256_hash pattern raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EvidenceArtifact(
                artifact_id="evd_log_a1b2c3d4",
                artifact_type=ArtifactType.DECISION_LOG,
                sha256_hash="invalid_hash",  # Should match ^[a-f0-9]{64}$
                created_at=datetime.now(timezone.utc),
                source="test",
            )
        assert "sha256_hash" in str(exc_info.value)

    def test_invalid_storage_uri_format(self):
        """Test that invalid storage_uri format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EvidenceArtifact(
                artifact_id="evd_log_a1b2c3d4",
                artifact_type=ArtifactType.DECISION_LOG,
                sha256_hash="a" * 64,
                created_at=datetime.now(timezone.utc),
                source="test",
                storage_uri="not_a_valid_uri",  # Should be valid URI
            )
        assert "storage_uri" in str(exc_info.value)

    def test_valid_storage_uri_formats(self):
        """Test that valid URI formats are accepted."""
        valid_uris = [
            "https://storage.example.com/artifacts/123",
            "s3://bucket-name/path/to/artifact",
            "file:///var/log/artifacts/test.json",
        ]
        for uri in valid_uris:
            artifact = EvidenceArtifact(
                artifact_id="evd_log_a1b2c3d4",
                artifact_type=ArtifactType.DECISION_LOG,
                sha256_hash="a" * 64,
                created_at=datetime.now(timezone.utc),
                source="test",
                storage_uri=uri,
            )
            assert str(artifact.storage_uri) == uri


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Tests for all enum types."""

    def test_decision_outcome_values(self):
        """Test DecisionOutcome enum values."""
        assert DecisionOutcome.APPROVED.value == "approved"
        assert DecisionOutcome.DENIED.value == "denied"
        assert DecisionOutcome.ESCALATED.value == "escalated"
        assert DecisionOutcome.CONDITIONAL.value == "conditional"

    def test_policy_mode_values(self):
        """Test PolicyMode enum values."""
        assert PolicyMode.PERMISSIVE.value == "permissive"
        assert PolicyMode.STRICT.value == "strict"
        assert PolicyMode.PARANOID.value == "paranoid"

    def test_actor_type_values(self):
        """Test ActorType enum values."""
        assert ActorType.AI_AGENT.value == "ai_agent"
        assert ActorType.HUMAN_USER.value == "human_user"
        assert ActorType.SYSTEM_SERVICE.value == "system_service"
        assert ActorType.ORGANIZATIONAL_ROLE.value == "organizational_role"
        assert ActorType.EXTERNAL_PARTY.value == "external_party"

    def test_action_category_values(self):
        """Test ActionCategory enum values."""
        assert ActionCategory.READ.value == "read"
        assert ActionCategory.WRITE.value == "write"
        assert ActionCategory.EXECUTE.value == "execute"
        assert ActionCategory.TRANSMIT.value == "transmit"
        assert ActionCategory.DELETE.value == "delete"
        assert ActionCategory.APPROVE.value == "approve"
        assert ActionCategory.ESCALATE.value == "escalate"

    def test_resource_classification_values(self):
        """Test ResourceClassification enum values."""
        assert ResourceClassification.PUBLIC.value == "public"
        assert ResourceClassification.INTERNAL.value == "internal"
        assert ResourceClassification.CONFIDENTIAL.value == "confidential"
        assert ResourceClassification.RESTRICTED.value == "restricted"
        assert ResourceClassification.CRITICAL.value == "critical"

    def test_compliance_framework_values(self):
        """Test ComplianceFramework enum values."""
        assert ComplianceFramework.SOC2.value == "soc2"
        assert ComplianceFramework.HIPAA.value == "hipaa"
        assert ComplianceFramework.GDPR.value == "gdpr"
        assert ComplianceFramework.PCI_DSS.value == "pci_dss"
        assert ComplianceFramework.ISO27001.value == "iso27001"
        assert ComplianceFramework.NIST_CSF.value == "nist_csf"
        assert ComplianceFramework.FEDRAMP.value == "fedramp"
        assert ComplianceFramework.CCPA.value == "ccpa"

    def test_risk_level_values(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_escalation_trigger_values(self):
        """Test EscalationTrigger enum values."""
        assert EscalationTrigger.RISK_THRESHOLD.value == "risk_threshold"
        assert EscalationTrigger.POLICY_CONFLICT.value == "policy_conflict"
        assert EscalationTrigger.EXPLICIT_RULE.value == "explicit_rule"
        assert EscalationTrigger.ACTOR_REQUEST.value == "actor_request"
        assert EscalationTrigger.ANOMALY_DETECTED.value == "anomaly_detected"

    def test_artifact_type_values(self):
        """Test ArtifactType enum values."""
        assert ArtifactType.DECISION_LOG.value == "decision_log"
        assert ArtifactType.POLICY_SNAPSHOT.value == "policy_snapshot"
        assert ArtifactType.CONTEXT_CAPTURE.value == "context_capture"
        assert ArtifactType.SCREENSHOT.value == "screenshot"
        assert ArtifactType.ATTESTATION.value == "attestation"
        assert ArtifactType.SIGNATURE.value == "signature"
        assert ArtifactType.AUDIT_TRAIL.value == "audit_trail"
        assert ArtifactType.EXTERNAL_REPORT.value == "external_report"


# =============================================================================
# Serialization Tests
# =============================================================================


class TestSerialization:
    """Tests for model serialization."""

    def test_decision_to_dict(self):
        """Test Decision model serialization to dict."""
        decision = Decision(
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            request_id="req-123",
            actor_id="act_ai_agent:claude",
            action_id="axn_read:file_contents",
            outcome=DecisionOutcome.APPROVED,
            timestamp=datetime(2026, 1, 4, 12, 0, 0, tzinfo=timezone.utc),
            policy_ids=["pol_default_v1"],
        )
        data = decision.model_dump()
        assert data["decision_id"] == "dec_01HQXK5M8N2P3R4S5T6V7W8X9Y"
        assert data["outcome"] == "approved"

    def test_decision_to_json(self):
        """Test Decision model serialization to JSON."""
        decision = Decision(
            decision_id="dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            request_id="req-123",
            actor_id="act_ai_agent:claude",
            action_id="axn_read:file_contents",
            outcome=DecisionOutcome.APPROVED,
            timestamp=datetime(2026, 1, 4, 12, 0, 0, tzinfo=timezone.utc),
            policy_ids=["pol_default_v1"],
        )
        json_str = decision.model_dump_json()
        assert "dec_01HQXK5M8N2P3R4S5T6V7W8X9Y" in json_str
        assert '"outcome":"approved"' in json_str

    def test_decision_from_dict(self):
        """Test Decision model deserialization from dict."""
        data = {
            "decision_id": "dec_01HQXK5M8N2P3R4S5T6V7W8X9Y",
            "request_id": "req-123",
            "actor_id": "act_ai_agent:claude",
            "action_id": "axn_read:file_contents",
            "outcome": "approved",
            "timestamp": "2026-01-04T12:00:00Z",
            "policy_ids": ["pol_default_v1"],
        }
        decision = Decision.model_validate(data)
        assert decision.outcome == DecisionOutcome.APPROVED
        assert decision.decision_id == "dec_01HQXK5M8N2P3R4S5T6V7W8X9Y"

    def test_policy_roundtrip(self):
        """Test Policy model serialization roundtrip."""
        original = Policy(
            policy_id="pol_test_v1",
            name="Test Policy",
            version="1.0.0",
            mode=PolicyMode.STRICT,
            terms=[Term(id="actor:user", type=TermType.ACTOR, name="User")],
            relations=[
                Relation(
                    type=RelationType.PERMITS,
                    subject="actor:user",
                    action="action:read",
                )
            ],
        )
        data = original.model_dump()
        restored = Policy.model_validate(data)
        assert restored.policy_id == original.policy_id
        assert restored.mode == original.mode
        assert len(restored.terms) == len(original.terms)
