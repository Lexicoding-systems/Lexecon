"""Comprehensive coverage tests for high-impact modules.
Target: +120 lines coverage toward 85% goal.
"""
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

# Mock cryptography
for mod_name in [
    'cryptography', 'cryptography.hazmat', 'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.serialization', 'cryptography.hazmat.primitives.asymmetric',
    'cryptography.hazmat.primitives.asymmetric.ed25519', 'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.backends', 'cryptography.exceptions'
]:
    sys.modules[mod_name] = Mock()

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lexecon.policy.engine import PolicyEngine, PolicyMode, PolicyDecision
from lexecon.policy.terms import PolicyTerm, TermType
from lexecon.policy.relations import PolicyRelation, RelationType
from lexecon.ledger.chain import LedgerEntry, LedgerChain
from lexecon.risk.service import RiskLevel, RiskScoringEngine


class TestPolicyEngineComprehensive:
    """Comprehensive policy engine tests (+25 coverage)."""
    
    def test_all_policy_modes(self):
        """Test all three policy modes work."""
        for mode in [PolicyMode.STRICT, PolicyMode.PERMISSIVE, PolicyMode.PARANOID]:
            engine = PolicyEngine(mode=mode)
            assert engine.mode == mode
    
    def test_mode_from_strings(self):
        """Test mode initialization from strings."""
        assert PolicyEngine(mode="strict").mode == PolicyMode.STRICT
        assert PolicyEngine(mode="permissive").mode == PolicyMode.PERMISSIVE
        assert PolicyEngine(mode="paranoid").mode == PolicyMode.PARANOID
    
    def test_strict_denies_unknown(self):
        """Strict mode denies unknown actions."""
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        result = engine.evaluate(actor="unknown", action="unknown")
        assert result.allowed is False
    
    def test_permissive_allows_unknown(self):
        """Permissive mode allows unknown actions."""
        engine = PolicyEngine(mode=PolicyMode.PERMISSIVE)
        result = engine.evaluate(actor="unknown", action="unknown")
        assert result.allowed is True
    
    def test_explicit_permit_works(self):
        """Explicit permit allows action."""
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        actor = PolicyTerm.create_actor("user", "User")
        action = PolicyTerm.create_action("read", "Read")
        engine.add_term(actor)
        engine.add_term(action)
        engine.add_relation(PolicyRelation.permits(actor.term_id, action.term_id))
        
        result = engine.evaluate(actor="user", action="read")
        assert result.allowed is True
    
    def test_explicit_forbid_blocks(self):
        """Explicit forbid blocks action."""
        engine = PolicyEngine(mode=PolicyMode.PERMISSIVE)
        actor = PolicyTerm.create_actor("user", "User")
        action = PolicyTerm.create_action("delete", "Delete")
        engine.add_term(actor)
        engine.add_term(action)
        engine.add_relation(PolicyRelation.forbids(actor.term_id, action.term_id))
        
        result = engine.evaluate(actor="user", action="delete")
        assert result.allowed is False
    
    def test_forbid_overrides_permit(self):
        """Forbid takes precedence over permit."""
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        actor = PolicyTerm.create_actor("user", "User")
        action = PolicyTerm.create_action("mixed", "Mixed")
        engine.add_term(actor)
        engine.add_term(action)
        engine.add_relation(PolicyRelation.permits(actor.term_id, action.term_id))
        engine.add_relation(PolicyRelation.forbids(actor.term_id, action.term_id))
        
        result = engine.evaluate(actor="user", action="mixed")
        assert result.allowed is False
    
    def test_policy_hash_changes(self):
        """Policy hash changes when modified."""
        engine = PolicyEngine()
        hash1 = engine.get_policy_hash()
        
        engine.add_term(PolicyTerm.create_actor("u", "User"))
        hash2 = engine.get_policy_hash()
        assert hash2 != hash1
        
        engine.add_relation(PolicyRelation.permits("act_u", "act_u"))
        hash3 = engine.get_policy_hash()
        assert hash3 != hash2


class TestLedgerChainComprehensive:
    """Comprehensive ledger chain tests (+30 coverage)."""
    
    def test_ledger_genesis_entry(self):
        """Ledger has genesis entry."""
        chain = LedgerChain()
        assert len(chain.entries) >= 1
        assert chain.entries[0].event_type == "genesis"
    
    def test_ledger_append_creates_entry(self):
        """Append creates new entry."""
        chain = LedgerChain()
        entry = chain.append("test", {"data": 1})
        assert entry.event_type == "test"
        assert entry.data["data"] == 1
    
    def test_ledger_hash_chain(self):
        """Entries form hash chain."""
        chain = LedgerChain()
        e1 = chain.append("e1", {})
        e2 = chain.append("e2", {})
        assert e2.previous_hash == e1.entry_hash
    
    def test_ledger_integrity_valid(self):
        """Integrity check passes for valid chain."""
        chain = LedgerChain()
        chain.append("e1", {"a": 1})
        chain.append("e2", {"b": 2})
        
        result = chain.verify_integrity()
        assert result["valid"] is True
        assert result["chain_intact"] is True
    
    def test_entry_hash_deterministic(self):
        """Entry hash is deterministic."""
        chain = LedgerChain()
        entry = chain.append("test", {"k": "v"})
        
        h1 = entry.calculate_hash()
        h2 = entry.calculate_hash()
        assert h1 == h2
    
    def test_entry_to_dict(self):
        """Entry serializes to dict."""
        chain = LedgerChain()
        entry = chain.append("test", {"k": "v"})
        
        d = entry.to_dict()
        assert d["event_type"] == "test"
        assert d["data"]["k"] == "v"
        assert "entry_hash" in d


class TestRiskServiceComprehensive:
    """Risk service tests (+20 coverage)."""
    
    def test_risk_levels(self):
        """Test all risk level determinations."""
        engine = RiskScoringEngine()
        
        assert engine.determine_risk_level(10) == RiskLevel.LOW
        assert engine.determine_risk_level(30) == RiskLevel.MEDIUM
        assert engine.determine_risk_level(60) == RiskLevel.HIGH
        assert engine.determine_risk_level(85) == RiskLevel.CRITICAL
    
    def test_risk_level_boundaries(self):
        """Test boundary conditions."""
        engine = RiskScoringEngine()
        
        # At boundaries
        assert engine.determine_risk_level(0) == RiskLevel.LOW
        assert engine.determine_risk_level(25) == RiskLevel.LOW
        assert engine.determine_risk_level(50) == RiskLevel.MEDIUM
        assert engine.determine_risk_level(75) == RiskLevel.HIGH
        assert engine.determine_risk_level(100) == RiskLevel.CRITICAL


class TestPolicyDecisionComprehensive:
    """Policy decision tests (+15 coverage)."""
    
    def test_decision_attributes(self):
        """Decision has correct attributes."""
        d = PolicyDecision(allowed=True, reason="OK")
        assert d.allowed is True
        assert d.permitted is True  # backwards compat
        assert d.reason == "OK"
        assert d.reasoning == "OK"  # backwards compat
    
    def test_decision_dict_access(self):
        """Decision supports dict access."""
        d = PolicyDecision(allowed=False, reason="Denied", extra="val")
        assert d["allowed"] is False
        assert d["reason"] == "Denied"
        assert d["extra"] == "val"
    
    def test_decision_get(self):
        """Decision supports get method."""
        d = PolicyDecision(allowed=True, reason="OK")
        assert d.get("allowed") is True
        assert d.get("missing") is None
        assert d.get("missing", "default") == "default"


class TestPolicyTermsComprehensive:
    """Policy terms tests (+15 coverage)."""
    
    def test_all_term_types(self):
        """Create all term types."""
        assert PolicyTerm.create_actor("u", "U").term_type == TermType.ACTOR
        assert PolicyTerm.create_action("a", "A").term_type == TermType.ACTION
        assert PolicyTerm.create_resource("r", "R").term_type == TermType.RESOURCE
        assert PolicyTerm.create_data_class("d", "D").term_type == TermType.DATA_CLASS
    
    def test_term_metadata(self):
        """Term with metadata."""
        t = PolicyTerm(
            term_id="t", term_type=TermType.ACTION, label="T",
            description="Desc", metadata={"k": "v"}
        )
        assert t.metadata["k"] == "v"
    
    def test_term_to_dict(self):
        """Term serialization."""
        t = PolicyTerm.create_actor("user", "User")
        d = t.to_dict()
        assert "term_id" in d
        assert "term_type" in d
        assert "label" in d


class TestPolicyRelationsComprehensive:
    """Policy relations tests (+15 coverage)."""
    
    def test_all_relation_types(self):
        """Create all relation types."""
        p = PolicyRelation.permits("a", "b")
        assert p.relation_type == RelationType.PERMITS
        
        f = PolicyRelation.forbids("a", "b")
        assert f.relation_type == RelationType.FORBIDS
        
        r = PolicyRelation.requires("a", "b")
        assert r.relation_type == RelationType.REQUIRES
    
    def test_relation_attributes(self):
        """Relation has correct attributes."""
        r = PolicyRelation.permits("actor_a", "action_b", conditions=["c1"])
        assert r.source == "actor_a"
        assert r.target == "action_b"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
