"""Tests for decision service."""

import uuid
from datetime import datetime

import pytest

from lexecon.decision.service import DecisionRequest, DecisionResponse, DecisionService
from lexecon.identity.signing import NodeIdentity
from lexecon.ledger.chain import LedgerChain
from lexecon.policy.engine import PolicyEngine, PolicyMode
from lexecon.policy.relations import PolicyRelation
from lexecon.policy.terms import PolicyTerm


class TestDecisionRequest:
    """Tests for DecisionRequest class."""

    def test_create_decision_request(self):
        """Test creating a decision request."""
        request = DecisionRequest(
            actor="model",
            proposed_action="search",
            tool="web_search",
            user_intent="Research AI governance",
        )

        assert request.actor == "model"
        assert request.proposed_action == "search"
        assert request.tool == "web_search"
        assert request.user_intent == "Research AI governance"
        assert request.risk_level == 1  # Default
        assert request.policy_mode == "strict"  # Default
        assert isinstance(request.request_id, str)
        assert len(request.request_id) > 0

    def test_request_with_custom_id(self):
        """Test creating request with custom ID."""
        custom_id = "req_123456"
        request = DecisionRequest(
            request_id=custom_id,
            actor="user",
            proposed_action="read",
            tool="file_system",
            user_intent="Read file",
        )

        assert request.request_id == custom_id

    def test_request_generates_uuid_if_no_id(self):
        """Test that request generates UUID if no ID provided."""
        request1 = DecisionRequest(
            actor="model", proposed_action="action1", tool="tool1", user_intent="intent1"
        )
        request2 = DecisionRequest(
            actor="model", proposed_action="action2", tool="tool2", user_intent="intent2"
        )

        # Should be different UUIDs
        assert request1.request_id != request2.request_id

        # Should be valid UUIDs
        uuid.UUID(request1.request_id)
        uuid.UUID(request2.request_id)

    def test_request_with_data_classes(self):
        """Test request with data classes."""
        request = DecisionRequest(
            actor="model",
            proposed_action="process",
            tool="analytics",
            user_intent="Analyze data",
            data_classes=["pii", "financial"],
        )

        assert request.data_classes == ["pii", "financial"]

    def test_request_with_high_risk_level(self):
        """Test request with high risk level."""
        request = DecisionRequest(
            actor="model",
            proposed_action="delete",
            tool="database",
            user_intent="Clean up",
            risk_level=5,
        )

        assert request.risk_level == 5

    def test_request_with_context(self):
        """Test request with additional context."""
        context = {"session_id": "abc123", "ip": "192.168.1.1"}
        request = DecisionRequest(
            actor="user",
            proposed_action="login",
            tool="auth",
            user_intent="Login",
            context=context,
        )

        assert request.context == context

    def test_request_serialization(self):
        """Test request serialization to dict."""
        request = DecisionRequest(
            actor="model",
            proposed_action="search",
            tool="web",
            user_intent="Search",
            data_classes=["public"],
            risk_level=2,
            context={"query": "test"},
        )

        data = request.to_dict()

        assert data["actor"] == "model"
        assert data["proposed_action"] == "search"
        assert data["tool"] == "web"
        assert data["user_intent"] == "Search"
        assert data["data_classes"] == ["public"]
        assert data["risk_level"] == 2
        assert data["context"]["query"] == "test"
        assert "timestamp" in data
        assert "request_id" in data

    def test_request_has_timestamp(self):
        """Test that request includes timestamp."""
        request = DecisionRequest(
            actor="model", proposed_action="action", tool="tool", user_intent="intent"
        )

        assert hasattr(request, "timestamp")
        # Should be ISO format
        datetime.fromisoformat(request.timestamp)


class TestDecisionResponse:
    """Tests for DecisionResponse class."""

    def test_create_decision_response(self):
        """Test creating a decision response."""
        response = DecisionResponse(
            request_id="req_123",
            decision="permit",
            reasoning="Action is allowed by policy",
            policy_version_hash="abc123",
        )

        assert response.request_id == "req_123"
        assert response.decision == "permit"
        assert response.reasoning == "Action is allowed by policy"
        assert response.policy_version_hash == "abc123"

    def test_response_with_capability_token(self):
        """Test response including capability token."""
        token = {
            "token_id": "tok_abc123",
            "scope": {"action": "read", "tool": "api"},
            "expiry": "2025-01-02T12:00:00",
        }

        response = DecisionResponse(
            request_id="req_456",
            decision="permit",
            reasoning="Permitted",
            policy_version_hash="hash1",
            capability_token=token,
        )

        assert response.capability_token == token

    def test_response_with_ledger_entry(self):
        """Test response including ledger entry hash."""
        response = DecisionResponse(
            request_id="req_789",
            decision="deny",
            reasoning="Forbidden by policy",
            policy_version_hash="hash2",
            ledger_entry_hash="ledger_hash_abc",
        )

        assert response.ledger_entry_hash == "ledger_hash_abc"

    def test_response_with_signature(self):
        """Test response including signature."""
        response = DecisionResponse(
            request_id="req_sig",
            decision="permit",
            reasoning="OK",
            policy_version_hash="hash3",
            signature="sig_base64_encoded",
        )

        assert response.signature == "sig_base64_encoded"

    def test_decision_hash_generation(self):
        """Test decision hash generation."""
        response = DecisionResponse(
            request_id="req_hash",
            decision="permit",
            reasoning="Test",
            policy_version_hash="hash4",
        )

        decision_hash = response.decision_hash

        assert isinstance(decision_hash, str)
        assert len(decision_hash) == 64  # SHA256 hex

    def test_decision_hash_is_deterministic(self):
        """Test that decision hash is deterministic."""
        timestamp = "2025-01-01T00:00:00"
        response1 = DecisionResponse(
            request_id="req_det",
            decision="permit",
            reasoning="Test",
            policy_version_hash="hash5",
            timestamp=timestamp,
        )
        response2 = DecisionResponse(
            request_id="req_det",
            decision="permit",
            reasoning="Different reasoning",  # Hash doesn't include reasoning
            policy_version_hash="hash5",
            timestamp=timestamp,
        )

        # Same request_id, decision, policy hash, timestamp -> same hash
        assert response1.decision_hash == response2.decision_hash

    def test_response_serialization(self):
        """Test response serialization to dict."""
        response = DecisionResponse(
            request_id="req_ser",
            decision="deny",
            reasoning="Not authorized",
            policy_version_hash="hash6",
            ledger_entry_hash="ledger123",
            signature="sig123",
        )

        data = response.to_dict()

        assert data["request_id"] == "req_ser"
        assert data["decision"] == "deny"
        assert data["reasoning"] == "Not authorized"
        assert data["reason"] == "Not authorized"  # Backwards compatibility
        assert data["allowed"] is False  # deny -> allowed=False
        assert data["policy_version_hash"] == "hash6"
        assert data["ledger_entry_hash"] == "ledger123"
        assert data["signature"] == "sig123"
        assert "timestamp" in data

    def test_response_allowed_field_for_permit(self):
        """Test that 'allowed' field is True for permit."""
        response = DecisionResponse(
            request_id="req_permit",
            decision="permit",
            reasoning="OK",
            policy_version_hash="hash",
        )

        data = response.to_dict()
        assert data["allowed"] is True

    def test_response_allowed_field_for_deny(self):
        """Test that 'allowed' field is False for deny."""
        response = DecisionResponse(
            request_id="req_deny", decision="deny", reasoning="No", policy_version_hash="hash"
        )

        data = response.to_dict()
        assert data["allowed"] is False

    def test_response_signature_defaults_to_empty(self):
        """Test that signature defaults to empty string in serialization."""
        response = DecisionResponse(
            request_id="req_nosig", decision="permit", reasoning="OK", policy_version_hash="hash"
        )

        data = response.to_dict()
        assert data["signature"] == ""


class TestDecisionService:
    """Tests for DecisionService class."""

    @pytest.fixture
    def policy_engine(self):
        """Create a policy engine with basic rules."""
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        engine.add_term(PolicyTerm.create_actor("model", "AI Model"))
        engine.add_term(PolicyTerm.create_action("search", "Search"))
        engine.add_relation(PolicyRelation.permits("actor:model", "action:search"))
        return engine

    @pytest.fixture
    def service(self, policy_engine):
        """Create basic decision service."""
        return DecisionService(policy_engine)

    @pytest.fixture
    def full_service(self, policy_engine):
        """Create decision service with ledger and identity."""
        ledger = LedgerChain()
        identity = NodeIdentity("test-node")
        return DecisionService(policy_engine, ledger, identity)

    def test_service_initialization(self, policy_engine):
        """Test creating decision service."""
        service = DecisionService(policy_engine)

        assert service.policy_engine is not None
        assert service.ledger is None
        assert service.identity is None

    def test_service_with_ledger_and_identity(self, full_service):
        """Test service with all components."""
        assert full_service.policy_engine is not None
        assert full_service.ledger is not None
        assert full_service.identity is not None

    def test_evaluate_request_permit(self, service):
        """Test evaluating a request that should be permitted."""
        request = DecisionRequest(
            actor="model",
            proposed_action="search",
            tool="web_search",
            user_intent="Search for information",
        )

        response = service.evaluate_request(request)

        assert response.decision == "permit"
        assert response.request_id == request.request_id
        assert response.capability_token is not None
        assert "token_id" in response.capability_token

    def test_evaluate_request_deny(self, service):
        """Test evaluating a request that should be denied."""
        request = DecisionRequest(
            actor="model",
            proposed_action="delete",  # Not permitted
            tool="database",
            user_intent="Delete records",
        )

        response = service.evaluate_request(request)

        assert response.decision == "deny"
        assert response.capability_token is None

    def test_capability_token_generation(self, service):
        """Test that capability token is generated for permitted actions."""
        request = DecisionRequest(
            actor="model", proposed_action="search", tool="web_search", user_intent="Search"
        )

        response = service.evaluate_request(request)

        token = response.capability_token
        assert token is not None
        assert token["scope"]["action"] == "search"
        assert token["scope"]["tool"] == "web_search"
        assert "expiry" in token
        assert "granted_at" in token

    def test_ledger_entry_creation(self, full_service):
        """Test that ledger entry is created."""
        request = DecisionRequest(
            actor="model", proposed_action="search", tool="web", user_intent="Test"
        )

        response = full_service.evaluate_request(request)

        assert response.ledger_entry_hash is not None
        assert len(response.ledger_entry_hash) == 64  # SHA256 hex

        # Verify entry exists in ledger by hash
        entry = full_service.ledger.get_entry(response.ledger_entry_hash)
        assert entry is not None
        assert entry.event_type == "decision"

    def test_signature_generation(self, full_service):
        """Test that decision is signed."""
        request = DecisionRequest(
            actor="model", proposed_action="search", tool="web", user_intent="Test"
        )

        response = full_service.evaluate_request(request)

        assert response.signature is not None
        assert len(response.signature) > 0

        # Verify it's valid base64
        import base64

        decoded = base64.b64decode(response.signature)
        assert len(decoded) > 0

    def test_evaluate_convenience_method_simple(self, policy_engine):
        """Test simple evaluate method."""
        service = DecisionService(policy_engine)

        # Simple policy evaluation
        result = service.evaluate(actor="model", action="search")

        # Should return PolicyDecision object
        assert hasattr(result, "allowed")
        assert hasattr(result, "reason")

    def test_evaluate_convenience_method_full(self, full_service):
        """Test evaluate method with full parameters."""
        # Full decision request
        result = full_service.evaluate(
            actor="model",
            proposed_action="search",
            tool="web_search",
            user_intent="Testing",
            risk_level=1,
        )

        # Should return DecisionResponse
        assert hasattr(result, "decision")
        assert hasattr(result, "capability_token")
        assert hasattr(result, "ledger_entry_hash")

    def test_multiple_decisions_logged(self, full_service):
        """Test that multiple decisions are logged to ledger."""
        initial_count = len(full_service.ledger.entries)

        for i in range(5):
            request = DecisionRequest(
                actor="model",
                proposed_action="search",
                tool="web",
                user_intent=f"Search {i}",
            )
            full_service.evaluate_request(request)

        final_count = len(full_service.ledger.entries)
        assert final_count == initial_count + 5

    def test_decision_with_data_classes(self, policy_engine):
        """Test decision evaluation with data classes."""
        service = DecisionService(policy_engine)
        request = DecisionRequest(
            actor="model",
            proposed_action="search",
            tool="web",
            user_intent="Search",
            data_classes=["public"],
        )

        response = service.evaluate_request(request)

        # Should still work
        assert response.decision in ["permit", "deny"]

    def test_decision_with_high_risk_level(self, service):
        """Test decision with high risk level."""
        request = DecisionRequest(
            actor="model",
            proposed_action="search",
            tool="web",
            user_intent="Search",
            risk_level=5,
        )

        response = service.evaluate_request(request)

        # Should still evaluate
        assert response.decision in ["permit", "deny"]

    def test_policy_version_hash_in_response(self, service):
        """Test that response includes policy version hash."""
        request = DecisionRequest(
            actor="model", proposed_action="search", tool="web", user_intent="Test"
        )

        response = service.evaluate_request(request)

        assert response.policy_version_hash is not None
        assert len(response.policy_version_hash) == 64  # SHA256 hex

    def test_reasoning_in_response(self, service):
        """Test that response includes reasoning."""
        request = DecisionRequest(
            actor="model", proposed_action="search", tool="web", user_intent="Test"
        )

        response = service.evaluate_request(request)

        assert response.reasoning is not None
        assert len(response.reasoning) > 0


class TestDecisionWorkflow:
    """Integration tests for complete decision workflow."""

    def test_complete_workflow(self):
        """Test complete decision workflow from request to signed response."""
        # Setup
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        engine.add_term(PolicyTerm.create_actor("user", "User"))
        engine.add_term(PolicyTerm.create_action("read", "Read"))
        engine.add_relation(PolicyRelation.permits("actor:user", "action:read"))

        ledger = LedgerChain()
        identity = NodeIdentity("governance-node")
        service = DecisionService(engine, ledger, identity)

        # Make decision
        request = DecisionRequest(
            actor="user", proposed_action="read", tool="file_system", user_intent="Read file"
        )

        response = service.evaluate_request(request)

        # Verify all components
        assert response.decision == "permit"
        assert response.capability_token is not None
        assert response.ledger_entry_hash is not None
        assert response.signature is not None

        # Verify ledger integrity
        assert ledger.verify_integrity()["valid"] is True

        # Verify signature
        is_valid = identity.verify_signature(response.decision_hash, response.signature)
        assert is_valid is True

    def test_deny_workflow(self):
        """Test workflow for denied decision."""
        # Strict mode - deny by default
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        ledger = LedgerChain()
        identity = NodeIdentity("test-node")
        service = DecisionService(engine, ledger, identity)

        request = DecisionRequest(
            actor="unknown", proposed_action="forbidden", tool="admin", user_intent="Test"
        )

        response = service.evaluate_request(request)

        # Should be denied
        assert response.decision == "deny"
        assert response.capability_token is None  # No token for deny
        assert response.ledger_entry_hash is not None  # Still logged
        assert response.signature is not None  # Still signed

    def test_decision_audit_trail(self):
        """Test that decisions create proper audit trail."""
        engine = PolicyEngine(mode=PolicyMode.STRICT)
        engine.add_term(PolicyTerm.create_actor("bot", "Bot"))
        engine.add_term(PolicyTerm.create_action("execute", "Execute"))
        engine.add_relation(PolicyRelation.permits("actor:bot", "action:execute"))

        ledger = LedgerChain()
        identity = NodeIdentity("audit-node")
        service = DecisionService(engine, ledger, identity)

        # Make multiple decisions
        requests = [
            DecisionRequest(
                actor="bot", proposed_action="execute", tool=f"tool{i}", user_intent=f"Task {i}"
            )
            for i in range(3)
        ]

        responses = [service.evaluate_request(req) for req in requests]

        # Check audit report
        report = ledger.generate_audit_report()

        assert report["total_entries"] >= 4  # Genesis + 3 decisions
        assert "decision" in report["event_type_counts"]
        assert report["event_type_counts"]["decision"] == 3

        # Verify all entries
        decision_entries = ledger.get_entries_by_type("decision")
        assert len(decision_entries) == 3

    def test_concurrent_decisions(self):
        """Test handling multiple concurrent decisions."""
        engine = PolicyEngine(mode=PolicyMode.PERMISSIVE)
        ledger = LedgerChain()
        identity = NodeIdentity("concurrent-node")
        service = DecisionService(engine, ledger, identity)

        # Simulate concurrent requests
        requests = [
            DecisionRequest(
                actor=f"actor{i}", proposed_action="action", tool="tool", user_intent="Intent"
            )
            for i in range(10)
        ]

        responses = [service.evaluate_request(req) for req in requests]

        # All should succeed
        assert len(responses) == 10
        assert all(r.ledger_entry_hash is not None for r in responses)

        # All hashes should be unique
        hashes = [r.ledger_entry_hash for r in responses]
        assert len(hashes) == len(set(hashes))

        # Ledger should still be valid
        assert ledger.verify_integrity()["valid"] is True


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_user_intent(self):
        """Test request with empty user intent."""
        engine = PolicyEngine()
        service = DecisionService(engine)

        request = DecisionRequest(
            actor="model", proposed_action="action", tool="tool", user_intent=""
        )

        response = service.evaluate_request(request)
        assert response is not None

    def test_very_long_user_intent(self):
        """Test request with very long user intent."""
        engine = PolicyEngine()
        service = DecisionService(engine)

        long_intent = "A" * 10000
        request = DecisionRequest(
            actor="model", proposed_action="action", tool="tool", user_intent=long_intent
        )

        response = service.evaluate_request(request)
        assert response is not None

    def test_special_characters_in_fields(self):
        """Test request with special characters."""
        engine = PolicyEngine()
        service = DecisionService(engine)

        request = DecisionRequest(
            actor="model-v2.0",
            proposed_action="read/write",
            tool="tool_@#$",
            user_intent="Test with 特殊文字 and émojis 🔒",
        )

        response = service.evaluate_request(request)
        assert response is not None

    def test_decision_without_ledger(self):
        """Test that service works without ledger."""
        engine = PolicyEngine()
        service = DecisionService(engine)  # No ledger

        request = DecisionRequest(
            actor="model", proposed_action="action", tool="tool", user_intent="Test"
        )

        response = service.evaluate_request(request)

        assert response.ledger_entry_hash is None
        assert response.decision in ["permit", "deny"]

    def test_decision_without_identity(self):
        """Test that service works without identity."""
        engine = PolicyEngine()
        ledger = LedgerChain()
        service = DecisionService(engine, ledger)  # No identity

        request = DecisionRequest(
            actor="model", proposed_action="action", tool="tool", user_intent="Test"
        )

        response = service.evaluate_request(request)

        assert response.signature is None
        assert response.ledger_entry_hash is not None  # Ledger still works
