"""Integration tests for policy evaluation."""

import pytest
from lexecon import PolicyEngine, DecisionService


class TestPolicyEvaluation:
    """Test policy evaluation integration."""

    def test_strict_mode_denies_unknown_actions(self) -> None:
        """Test that strict mode denies actions not explicitly permitted."""
        engine = PolicyEngine(mode="strict")
        decision = engine.evaluate(
            actor="model", action="unknown_action", data_classes=[], risk_level=1
        )
        assert decision.allowed is False
        assert "not explicitly permitted" in decision.reason.lower()

    def test_permissive_mode_allows_unknown_actions(self) -> None:
        """Test that permissive mode allows actions not explicitly forbidden."""
        engine = PolicyEngine(mode="permissive")
        decision = engine.evaluate(
            actor="model", action="unknown_action", data_classes=[], risk_level=1
        )
        assert decision.allowed is True

    def test_paranoid_mode_requires_confirmation_for_high_risk(self) -> None:
        """Test that paranoid mode requires confirmation for high-risk actions."""
        engine = PolicyEngine(mode="paranoid")
        decision = engine.evaluate(
            actor="model", action="high_risk_action", data_classes=[], risk_level=4
        )
        assert "confirmation" in decision.reason.lower() or decision.allowed is False

    def test_explicit_permit_allows_action(self) -> None:
        """Test that explicit permit allows action in strict mode."""
        policy = {
            "name": "Test",
            "mode": "strict",
            "terms": [
                {"id": "actor:model", "type": "actor", "name": "model"},
                {"id": "action:read", "type": "action", "name": "read"},
            ],
            "relations": [
                {
                    "type": "permits",
                    "subject": "actor:model",
                    "action": "action:read",
                }
            ],
        }
        engine = PolicyEngine(policy)
        decision = engine.evaluate(
            actor="model", action="read", data_classes=[], risk_level=1
        )
        assert decision.allowed is True

    def test_explicit_forbid_denies_action(self) -> None:
        """Test that explicit forbid denies action even in permissive mode."""
        policy = {
            "name": "Test",
            "mode": "permissive",
            "terms": [
                {"id": "actor:model", "type": "actor", "name": "model"},
                {"id": "action:delete", "type": "action", "name": "delete"},
            ],
            "relations": [
                {
                    "type": "forbids",
                    "subject": "actor:model",
                    "action": "action:delete",
                }
            ],
        }
        engine = PolicyEngine(policy)
        decision = engine.evaluate(
            actor="model", action="delete", data_classes=[], risk_level=1
        )
        assert decision.allowed is False


class TestGDPRPolicyIntegration:
    """Test GDPR policy template integration."""

    @pytest.fixture
    def gdpr_policy(self) -> dict:
        """Load GDPR policy template."""
        import json
        from pathlib import Path

        policy_path = (
            Path(__file__).parent.parent.parent
            / "examples"
            / "policies"
            / "gdpr_compliance_policy.json"
        )
        with open(policy_path) as f:
            return json.load(f)

    def test_gdpr_forbids_special_category_processing(
        self, gdpr_policy: dict
    ) -> None:
        """Test that GDPR policy forbids AI processing of special category data."""
        engine = PolicyEngine(gdpr_policy)
        decision = engine.evaluate(
            actor="ai_model",
            action="process",
            data_classes=["special_category_data"],
            risk_level=3,
        )
        assert decision.allowed is False
        assert "Article 9" in decision.reason or "special category" in decision.reason.lower()

    def test_gdpr_allows_anonymous_data_processing(
        self, gdpr_policy: dict
    ) -> None:
        """Test that GDPR policy allows processing of anonymous data."""
        engine = PolicyEngine(gdpr_policy)
        decision = engine.evaluate(
            actor="ai_model",
            action="process",
            data_classes=["anonymous_data"],
            risk_level=1,
        )
        assert decision.allowed is True


class TestDecisionServiceIntegration:
    """Test decision service with ledger integration."""

    def test_decision_creates_ledger_entry(self) -> None:
        """Test that decision service creates ledger entry."""
        from lexecon.ledger import Ledger
        from lexecon.identity import NodeIdentity

        ledger = Ledger()
        identity = NodeIdentity("test-node")
        service = DecisionService(PolicyEngine(), ledger, identity)

        decision = service.evaluate(
            actor="model",
            proposed_action="Test action",
            tool="test_tool",
            user_intent="Testing",
            risk_level=1,
        )

        assert decision.ledger_entry_hash is not None
        entry = ledger.get_entry(decision.ledger_entry_hash)
        assert entry is not None

    def test_decision_signature_verification(self) -> None:
        """Test that decision signatures can be verified."""
        from lexecon.ledger import Ledger
        from lexecon.identity import NodeIdentity

        ledger = Ledger()
        identity = NodeIdentity("test-node")
        service = DecisionService(PolicyEngine(), ledger, identity)

        decision = service.evaluate(
            actor="model",
            proposed_action="Test action",
            tool="test_tool",
            user_intent="Testing",
            risk_level=1,
        )

        assert decision.signature is not None
        # Verify signature
        is_valid = identity.verify_signature(
            data=decision.decision_hash, signature=decision.signature
        )
        assert is_valid is True
