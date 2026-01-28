"""Isolated coverage tests that don't trigger cryptography imports."""
import sys
from pathlib import Path
from unittest.mock import Mock

# Mock cryptography before any imports
sys.modules['cryptography'] = Mock()
sys.modules['cryptography.hazmat'] = Mock()
sys.modules['cryptography.hazmat.primitives'] = Mock()
sys.modules['cryptography.hazmat.primitives.serialization'] = Mock()
sys.modules['cryptography.hazmat.primitives.asymmetric'] = Mock()
sys.modules['cryptography.hazmat.primitives.asymmetric.ed25519'] = Mock()
sys.modules['cryptography.hazmat.primitives.hashes'] = Mock()

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lexecon.policy.engine import PolicyEngine, PolicyMode, PolicyDecision
from lexecon.policy.terms import PolicyTerm
from lexecon.policy.relations import PolicyRelation


class TestPolicyEngineCoverage:
    def test_policy_modes_all(self):
        for mode in [PolicyMode.STRICT, PolicyMode.PERMISSIVE, PolicyMode.PARANOID]:
            engine = PolicyEngine(mode=mode)
            assert engine.mode == mode

    def test_policy_mode_from_string(self):
        engine = PolicyEngine(mode="strict")
        assert engine.mode == PolicyMode.STRICT

    def test_strict_mode_denies_unknown(self):
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        result = engine.evaluate(actor="unknown_user", action="unknown_action")
        assert result.allowed is False

    def test_permissive_mode_allows_by_default(self):
        engine = PolicyEngine(mode=PolicyMode.PERMISSIVE)
        result = engine.evaluate(actor="unknown_user", action="unknown_action")
        assert result.allowed is True

    def test_policy_hash_changes_on_modification(self):
        engine = PolicyEngine()
        hash1 = engine.get_policy_hash()
        term = PolicyTerm.create_actor("user", "User")
        engine.add_term(term)
        hash2 = engine.get_policy_hash()
        assert hash2 is not None

    def test_forbid_relation_overrides_permit(self):
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        actor = PolicyTerm.create_actor("user", "User")
        action = PolicyTerm.create_action("sensitive_op", "Sensitive")
        engine.add_term(actor)
        engine.add_term(action)
        engine.add_relation(PolicyRelation.permits(actor.term_id, action.term_id))
        engine.add_relation(PolicyRelation.forbids(actor.term_id, action.term_id))
        result = engine.evaluate(actor="user", action="sensitive_op")
        assert result.allowed is False


class TestPolicyTermsCoverage:
    def test_create_all_term_types(self):
        actor = PolicyTerm.create_actor("user", "User")
        assert actor.term_type == "actor"
        action = PolicyTerm.create_action("read", "Read")
        assert action.term_type == "action"
        resource = PolicyTerm.create_resource("database", "Database")
        assert resource.term_type == "resource"
        data_class = PolicyTerm.create_data_class("pii", "PII")
        assert data_class.term_type == "data_class"

    def test_term_with_constraints(self):
        term = PolicyTerm(
            term_id="constrained_action",
            term_type="action",
            name="Constrained Action",
            constraints={"max_records": 100}
        )
        assert term.constraints["max_records"] == 100


class TestPolicyDecisionCoverage:
    def test_decision_creation(self):
        decision = PolicyDecision(allowed=True, reason="Test reason")
        assert decision.allowed is True
        assert decision.reason == "Test reason"
        assert decision.permitted is True

    def test_decision_dict_access(self):
        decision = PolicyDecision(allowed=False, reason="Denied", extra_field="extra")
        assert decision["allowed"] is False
        assert decision["reason"] == "Denied"
        assert decision["extra_field"] == "extra"

    def test_decision_get_method(self):
        decision = PolicyDecision(allowed=True, reason="OK")
        assert decision.get("allowed") is True
        assert decision.get("nonexistent") is None
        assert decision.get("nonexistent", "default") == "default"
