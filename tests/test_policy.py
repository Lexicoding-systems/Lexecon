"""Tests for policy engine."""

import pytest

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

    def test_create_data_class(self):
        """Test creating a data class term."""
        term = PolicyTerm.create_data_class("pii", "Personal Information")
        assert term.term_id == "data:pii"
        assert term.term_type == TermType.DATA_CLASS
        assert term.label == "Personal Information"

    def test_create_resource(self):
        """Test creating a resource term."""
        term = PolicyTerm.create_resource("database", "Database Resource")
        assert term.term_id == "resource:database"
        assert term.term_type == TermType.RESOURCE
        assert term.label == "Database Resource"

    def test_from_dict_missing_term_id(self):
        """Test from_dict raises ValueError when term_id is missing."""
        data = {
            "term_type": "action",
            "label": "Test",
        }
        with pytest.raises(ValueError, match="Missing term_id or id field"):
            PolicyTerm.from_dict(data)

    def test_from_dict_missing_term_type(self):
        """Test from_dict raises ValueError when term_type is missing."""
        data = {
            "term_id": "action:test",
            "label": "Test",
        }
        with pytest.raises(ValueError, match="Missing term_type or type field"):
            PolicyTerm.from_dict(data)


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

    def test_requires(self):
        """Test creating a requires relation."""
        relation = PolicyRelation.requires("action:delete", "condition:approval")
        assert relation.relation_type == RelationType.REQUIRES
        assert relation.source == "action:delete"
        assert relation.target == "condition:approval"
        assert relation.conditions == []

    def test_post_init_with_none_conditions(self):
        """Test __post_init__ initializes empty conditions list."""
        relation = PolicyRelation(
            relation_id="test:rel",
            relation_type=RelationType.PERMITS,
            source="actor:user",
            target="action:read",
            conditions=None,  # Explicitly None
        )
        assert relation.conditions == []
        assert relation.metadata == {}

    def test_from_dict_missing_relation_type(self):
        """Test from_dict raises ValueError when relation_type is missing."""
        data = {
            "source": "actor:user",
            "target": "action:read",
        }
        with pytest.raises(ValueError, match="Missing relation_type or type field"):
            PolicyRelation.from_dict(data)

    def test_from_dict_missing_source_and_target(self):
        """Test from_dict raises ValueError when both source and target are missing."""
        data = {
            "relation_type": "permits",
        }
        with pytest.raises(ValueError, match="Missing source/target"):
            PolicyRelation.from_dict(data)

    def test_from_dict_only_source(self):
        """Test from_dict uses source for target when target is missing."""
        data = {
            "relation_type": "permits",
            "source": "actor:user",
        }
        relation = PolicyRelation.from_dict(data)
        assert relation.source == "actor:user"
        assert relation.target == "actor:user"  # Should copy source to target

    def test_from_dict_only_target(self):
        """Test from_dict uses target for source when source is missing."""
        data = {
            "relation_type": "permits",
            "action": "action:read",  # Using 'action' as alias for 'target'
        }
        relation = PolicyRelation.from_dict(data)
        assert relation.source == "action:read"  # Should copy target to source
        assert relation.target == "action:read"

    def test_from_dict_with_object_and_justification(self):
        """Test from_dict stores object and justification in metadata."""
        data = {
            "relation_type": "permits",
            "source": "actor:user",
            "target": "action:read",
            "object": "data:pii",
            "justification": "User has clearance",
            "condition": "during_business_hours",
        }
        relation = PolicyRelation.from_dict(data)
        assert relation.metadata["object"] == "data:pii"
        assert relation.metadata["justification"] == "User has clearance"
        assert relation.metadata["condition"] == "during_business_hours"


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
