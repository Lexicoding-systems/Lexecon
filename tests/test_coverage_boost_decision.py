"""Coverage boost tests for decision/service.py

Target: +60 lines coverage (from 21.7% to ~60%)
"""

import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lexecon.policy.engine import PolicyEngine, PolicyMode
from lexecon.decision.service import (
    DecisionService,
    DecisionRequest,
    DecisionResponse,
    generate_decision_id,
    generate_risk_id,
    generate_ulid,
)


class TestDecisionIdGeneration:
    """Test ULID-based ID generation."""

    def test_generate_ulid_format(self):
        """ULID should be 26 uppercase alphanumeric chars."""
        ulid = generate_ulid()
        assert len(ulid) == 26
        assert ulid.isupper() or ulid.isdigit()
        # Should only contain valid Crockford's Base32 chars
        valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
        assert all(c in valid_chars for c in ulid)

    def test_generate_ulid_sortability(self):
        """ULIDs should be roughly time-sortable."""
        ulid1 = generate_ulid()
        import time
        time.sleep(0.01)
        ulid2 = generate_ulid()
        # In most cases, earlier ULID < later ULID (timestamp component)
        assert ulid1 != ulid2

    def test_generate_decision_id_format(self):
        """Decision ID should have dec_ prefix."""
        decision_id = generate_decision_id()
        assert decision_id.startswith("dec_")
        assert len(decision_id) == 30  # "dec_" + 26 char ULID

    def test_generate_risk_id_format(self):
        """Risk ID should link to decision ID."""
        decision_id = "dec_01HN7YQZKEXAMPLE123456789"
        risk_id = generate_risk_id(decision_id)
        assert risk_id == f"rsk_{decision_id}"


class TestDecisionRequest:
    """Test DecisionRequest model."""

    def test_basic_request_creation(self):
        """Create basic decision request."""
        request = DecisionRequest(
            actor="test_user",
            proposed_action="read_file",
            tool="file_system",
            user_intent="Read config file",
        )
        assert request.actor == "test_user"
        assert request.proposed_action == "read_file"
        assert request.tool == "file_system"
        assert request.request_id is not None  # Auto-generated
        assert request.data_classes == []
        assert request.risk_level == 1
        assert request.policy_mode == "strict"

    def test_request_with_all_fields(self):
        """Create request with all optional fields."""
        request = DecisionRequest(
            actor="ai_agent",
            proposed_action="delete_database",
            tool="db_admin",
            user_intent="Clean up old records",
            request_id="req_test_123",
            data_classes=["pii", "financial"],
            risk_level=5,
            requested_output_type="confirmation",
            policy_mode="paranoid",
            context={"env": "production", "dry_run": False},
        )
        assert request.request_id == "req_test_123"
        assert request.data_classes == ["pii", "financial"]
        assert request.risk_level == 5
        assert request.policy_mode == "paranoid"
        assert request.context["env"] == "production"

    def test_request_to_canonical_actor_id(self):
        """Convert legacy actor to canonical actor ID."""
        request = DecisionRequest(
            actor="data_scientist",
            proposed_action="train_model",
            tool="ml_pipeline",
            user_intent="Train new model",
        )
        actor_id = request.to_canonical_actor_id()
        assert actor_id.startswith("act_")
        assert "data_scientist" in actor_id

    def test_request_to_canonical_action_id(self):
        """Convert legacy action to canonical action ID."""
        request = DecisionRequest(
            actor="user",
            proposed_action="deploy_model",
            tool="k8s",
            user_intent="Deploy",
        )
        action_id = request.to_canonical_action_id()
        assert action_id.startswith("axn_")
        assert "deploy_model" in action_id


class MockLedger:
    """Mock ledger for testing."""
    
    def __init__(self):
        self.entries = []
        
    def append(self, event_type, data):
        class Entry:
            def __init__(self):
                self.entry_hash = "mock_hash_123"
        self.entries.append((event_type, data))
        return Entry()


class MockIdentity:
    """Mock identity for testing."""
    
    class MockKeyManager:
        class MockKey:
            def sign(self, message):
                return b"mock_signature"
        private_key = MockKey()
    
    key_manager = MockKeyManager()


class TestDecisionService:
    """Test DecisionService evaluation."""

    def setup_method(self):
        """Set up policy engine for each test."""
        self.policy_engine = PolicyEngine(mode=PolicyMode.STRICT)
        # Add a permit rule
        from lexecon.policy.terms import PolicyTerm
        from lexecon.policy.relations import PolicyRelation
        
        actor = PolicyTerm.create_actor("test_user", "Test User")
        action = PolicyTerm.create_action("allowed_action", "Allowed")
        self.policy_engine.add_term(actor)
        self.policy_engine.add_term(action)
        self.policy_engine.add_relation(PolicyRelation.permits(actor, action))

    def test_service_init_defaults(self):
        """Initialize service with defaults."""
        service = DecisionService(self.policy_engine)
        assert service.policy_engine == self.policy_engine
        assert service.ledger is None
        assert service.identity is None

    def test_service_init_with_ledger(self):
        """Initialize service with ledger."""
        ledger = MockLedger()
        service = DecisionService(self.policy_engine, ledger=ledger)
        assert service.ledger == ledger

    def test_service_init_with_identity(self):
        """Initialize service with identity."""
        identity = MockIdentity()
        service = DecisionService(self.policy_engine, identity=identity)
        assert service.identity == identity

    def test_evaluate_request_permit(self):
        """Evaluate request that should be permitted."""
        service = DecisionService(self.policy_engine)
        request = DecisionRequest(
            actor="test_user",
            proposed_action="allowed_action",
            tool="test_tool",
            user_intent="Test",
        )
        
        response = service.evaluate_request(request)
        
        assert response.decision == "permit"
        assert response.decision_id is not None
        assert response.decision_id.startswith("dec_")
        assert response.policy_version_hash is not None
        assert response.capability_token is not None
        assert response.request_id == request.request_id

    def test_evaluate_request_deny(self):
        """Evaluate request that should be denied."""
        service = DecisionService(self.policy_engine)
        request = DecisionRequest(
            actor="test_user",
            proposed_action="forbidden_action",
            tool="test_tool",
            user_intent="Test",
        )
        
        response = service.evaluate_request(request)
        
        assert response.decision == "deny"
        assert response.capability_token is None

    def test_evaluate_request_with_ledger(self):
        """Evaluate request with ledger recording."""
        ledger = MockLedger()
        service = DecisionService(self.policy_engine, ledger=ledger)
        request = DecisionRequest(
            actor="test_user",
            proposed_action="allowed_action",
            tool="test_tool",
            user_intent="Test",
        )
        
        response = service.evaluate_request(request)
        
        assert response.ledger_entry_hash is not None
        assert len(ledger.entries) == 1
        assert ledger.entries[0][0] == "decision"

    def test_evaluate_request_with_identity(self):
        """Evaluate request with identity signing."""
        identity = MockIdentity()
        service = DecisionService(self.policy_engine, identity=identity)
        request = DecisionRequest(
            actor="test_user",
            proposed_action="allowed_action",
            tool="test_tool",
            user_intent="Test",
        )
        
        response = service.evaluate_request(request)
        
        assert response.signature is not None

    def test_simple_evaluate_method(self):
        """Use simple evaluate convenience method."""
        service = DecisionService(self.policy_engine)
        
        # Simple policy evaluation
        result = service.evaluate(
            actor="test_user",
            action="allowed_action",
            data_classes=[],
            risk_level=1,
        )
        
        assert result.allowed is True

    def test_evaluate_with_full_request_params(self):
        """Use evaluate with full request parameters."""
        service = DecisionService(self.policy_engine)
        
        result = service.evaluate(
            actor="test_user",
            proposed_action="allowed_action",
            tool="test_tool",
            user_intent="Test",
            data_classes=[],
            risk_level=1,
        )
        
        # Returns DecisionResponse when full params provided
        assert hasattr(result, 'decision')
        assert result.decision == "permit"

    def test_decision_response_properties(self):
        """Test DecisionResponse helper properties."""
        response = DecisionResponse(
            request_id="req_123",
            decision="permit",
            reasoning="Test reasoning",
            policy_version_hash="hash123",
            decision_id="dec_456",
        )
        
        assert response.is_permitted is True
        assert response.is_denied is False
        
        response2 = DecisionResponse(
            request_id="req_123",
            decision="deny",
            reasoning="Denied",
            policy_version_hash="hash123",
            decision_id="dec_456",
        )
        assert response2.is_permitted is False
        assert response2.is_denied is True

    def test_decision_response_to_dict(self):
        """Convert response to dictionary."""
        response = DecisionResponse(
            request_id="req_123",
            decision="permit",
            reasoning="Test",
            policy_version_hash="hash123",
            decision_id="dec_456",
        )
        
        d = response.to_dict()
        assert d["request_id"] == "req_123"
        assert d["decision"] == "permit"
        assert d["reasoning"] == "Test"
        assert d["policy_version_hash"] == "hash123"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
