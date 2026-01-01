"""Tests for policy engine."""

from lexecon.policy.engine import PolicyEngine, PolicyMode
from lexecon.policy.relations import PolicyRelation, RelationType
from lexecon.policy.terms import PolicyTerm, TermType


class TestPolicyTerm:
    """Tests for PolicyTerm."""

    def test_create_action(self):
        """Test creating an action term."""
        term = PolicyTerm.create_action("read", "Read Data")
        assert term.term_id == "action:read"
        assert term.term_type == TermType.ACTION
        assert term.label == "Read Data"

    def test_create_actor(self):
        """Test creating an actor term."""
        term = PolicyTerm.create_actor("user", "User")
        assert term.term_id == "actor:user"
        assert term.term_type == TermType.ACTOR

    def test_to_dict(self):
        """Test serialization."""
        term = PolicyTerm.create_action("write", "Write Data")
        data = term.to_dict()
        assert data["term_id"] == "action:write"
        assert data["term_type"] == "action"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "term_id": "action:delete",
            "term_type": "action",
            "label": "Delete",
            "description": "Delete data",
            "metadata": {},
        }
        term = PolicyTerm.from_dict(data)
        assert term.term_id == "action:delete"
        assert term.term_type == TermType.ACTION


class TestPolicyRelation:
    """Tests for PolicyRelation."""

    def test_permits(self):
        """Test creating a permit relation."""
        relation = PolicyRelation.permits("actor:user", "action:read")
        assert relation.relation_type == RelationType.PERMITS
        assert relation.source == "actor:user"
        assert relation.target == "action:read"

    def test_forbids(self):
        """Test creating a forbid relation."""
        relation = PolicyRelation.forbids("actor:model", "action:delete")
        assert relation.relation_type == RelationType.FORBIDS

    def test_to_dict(self):
        """Test serialization."""
        relation = PolicyRelation.permits("actor:admin", "action:write")
        data = relation.to_dict()
        assert data["relation_type"] == "permits"
        assert data["source"] == "actor:admin"


class TestPolicyEngine:
    """Tests for PolicyEngine."""

    def test_init(self):
        """Test initialization."""
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        assert engine.mode == PolicyMode.STRICT
        assert len(engine.terms) == 0
        assert len(engine.relations) == 0

    def test_add_term(self):
        """Test adding a term."""
        engine = PolicyEngine()
        term = PolicyTerm.create_action("read", "Read")
        engine.add_term(term)
        assert len(engine.terms) == 1
        assert "action:read" in engine.terms

    def test_add_relation(self):
        """Test adding a relation."""
        engine = PolicyEngine()
        relation = PolicyRelation.permits("actor:user", "action:read")
        engine.add_relation(relation)
        assert len(engine.relations) == 1

    def test_policy_hash(self):
        """Test policy hash generation."""
        engine = PolicyEngine()
        hash1 = engine.get_policy_hash()
        assert len(hash1) == 64  # SHA256 hex

        # Adding a term should change hash
        term = PolicyTerm.create_action("read", "Read")
        engine.add_term(term)
        hash2 = engine.get_policy_hash()
        assert hash1 != hash2

    def test_evaluate_strict_mode(self):
        """Test evaluation in strict mode."""
        engine = PolicyEngine(mode=PolicyMode.STRICT)

        # No permissions - should deny
        result = engine.evaluate("actor:user", "action:read")
        assert result["permitted"] is False

        # Add permission
        relation = PolicyRelation.permits("actor:user", "action:read")
        engine.add_relation(relation)

        result = engine.evaluate("actor:user", "action:read")
        assert result["permitted"] is True

    def test_evaluate_with_forbid(self):
        """Test evaluation with forbid rule."""
        engine = PolicyEngine(mode=PolicyMode.STRICT)

        # Add permission
        engine.add_relation(PolicyRelation.permits("actor:user", "action:write"))

        # Add forbid - should override
        engine.add_relation(PolicyRelation.forbids("actor:user", "action:write"))

        result = engine.evaluate("actor:user", "action:write")
        assert result["permitted"] is False
