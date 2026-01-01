"""Tests for model governance adapters."""

import os
import sys

import pytest

# Add model_governance_pack to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../model_governance_pack/adapters"))

from base import GovernanceAdapter, GovernanceError  # noqa: E402
from verification import GovernanceVerifier  # noqa: E402


class MockGovernanceAdapter(GovernanceAdapter):
    """Mock adapter for testing."""

    def intercept_tool_call(self, tool_name: str, tool_args: dict, **kwargs):
        decision = self.request_decision(
            tool_name=tool_name, tool_args=tool_args, user_intent=kwargs.get("user_intent", "")
        )
        return decision

    def wrap_response(self, decision: dict, result=None):
        return {"decision": decision, "result": result}


class TestGovernanceAdapter:
    """Tests for base GovernanceAdapter."""

    def test_init(self):
        """Test adapter initialization."""
        adapter = MockGovernanceAdapter(governance_url="http://localhost:8000", actor="model")
        assert adapter.governance_url == "http://localhost:8000"
        assert adapter.actor == "model"
        assert len(adapter.capability_tokens) == 0

    def test_check_health(self):
        """Test health check."""
        adapter = MockGovernanceAdapter()
        # Will fail if server not running, which is expected
        # In actual tests with running server, this would pass
        result = adapter.check_health()
        assert isinstance(result, bool)

    def test_is_permitted(self):
        """Test permission checking."""
        adapter = MockGovernanceAdapter()

        # Test permit
        assert adapter.is_permitted({"decision": "permit"}) is True

        # Test deny
        assert adapter.is_permitted({"decision": "deny"}) is False

        # Test error
        assert adapter.is_permitted({"decision": "permit", "error": True}) is False

    def test_verify_token(self):
        """Test capability token verification."""
        from datetime import datetime, timedelta

        adapter = MockGovernanceAdapter()

        # Create a valid token
        future_time = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        token = {
            "token_id": "tok_test123",
            "scope": {"action": "search", "tool": "web_search"},
            "expiry": future_time,
            "policy_version_hash": "test_hash",
        }

        # Store token
        adapter.capability_tokens["tok_test123"] = token

        # Verify valid token
        assert adapter.verify_token("tok_test123", "search", "web_search") is True

        # Verify wrong action
        assert adapter.verify_token("tok_test123", "write", "web_search") is False

        # Verify wrong tool
        assert adapter.verify_token("tok_test123", "search", "file_system") is False

        # Verify non-existent token
        assert adapter.verify_token("tok_nonexistent", "search", "web_search") is False

    def test_expired_token(self):
        """Test expired token handling."""
        from datetime import datetime, timedelta

        adapter = MockGovernanceAdapter()

        # Create an expired token
        past_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        token = {
            "token_id": "tok_expired",
            "scope": {"action": "search", "tool": "web_search"},
            "expiry": past_time,
            "policy_version_hash": "test_hash",
        }

        adapter.capability_tokens["tok_expired"] = token

        # Should return False and remove token
        assert adapter.verify_token("tok_expired", "search", "web_search") is False
        assert "tok_expired" not in adapter.capability_tokens


class TestGovernanceVerifier:
    """Tests for GovernanceVerifier."""

    def test_init(self):
        """Test verifier initialization."""
        verifier = GovernanceVerifier("http://localhost:8000")
        assert verifier.governance_url == "http://localhost:8000"

    def test_verify_capability_token_valid(self):
        """Test token verification with valid token."""
        from datetime import datetime, timedelta

        verifier = GovernanceVerifier()

        future_time = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        token = {
            "token_id": "tok_test123",
            "scope": {"action": "search", "tool": "web_search"},
            "expiry": future_time,
            "policy_version_hash": "test_hash",
        }

        result = verifier.verify_capability_token(token)
        assert result["valid"] is True
        assert result["token_id"] == "tok_test123"
        assert result["time_remaining"] > 0

    def test_verify_capability_token_expired(self):
        """Test token verification with expired token."""
        from datetime import datetime, timedelta

        verifier = GovernanceVerifier()

        past_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        token = {
            "token_id": "tok_expired",
            "scope": {"action": "search", "tool": "web_search"},
            "expiry": past_time,
            "policy_version_hash": "test_hash",
        }

        result = verifier.verify_capability_token(token)
        assert result["valid"] is False
        assert "expired" in result["error"].lower()

    def test_verify_capability_token_missing_fields(self):
        """Test token verification with missing fields."""
        verifier = GovernanceVerifier()

        incomplete_token = {
            "token_id": "tok_incomplete",
            "scope": {"action": "search"},
            # Missing expiry and policy_version_hash
        }

        result = verifier.verify_capability_token(incomplete_token)
        assert result["valid"] is False
        assert "missing" in result["error"].lower()

    def test_verify_capability_token_incomplete_scope(self):
        """Test token verification with incomplete scope."""
        from datetime import datetime, timedelta

        verifier = GovernanceVerifier()

        future_time = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        token = {
            "token_id": "tok_incomplete_scope",
            "scope": {"action": "search"},  # Missing tool
            "expiry": future_time,
            "policy_version_hash": "test_hash",
        }

        result = verifier.verify_capability_token(token)
        assert result["valid"] is False
        assert "scope" in result["error"].lower()


class TestGovernanceError:
    """Tests for GovernanceError exception."""

    def test_governance_error(self):
        """Test GovernanceError creation."""
        decision = {"decision": "deny", "reasoning": "Action not permitted"}

        error = GovernanceError(decision)
        assert error.decision == decision
        assert error.reasoning == "Action not permitted"
        assert str(error) == "Action not permitted"

    def test_governance_error_default_reasoning(self):
        """Test GovernanceError with missing reasoning."""
        decision = {"decision": "deny"}

        error = GovernanceError(decision)
        assert "denied" in error.reasoning.lower()


@pytest.mark.integration
class TestAdapterIntegration:
    """Integration tests requiring running governance server."""

    def test_request_decision_with_server(self):
        """Test decision request against live server."""
        adapter = MockGovernanceAdapter()

        if not adapter.check_health():
            pytest.skip("Governance server not running")

        # This would test actual decision request
        # Requires governance server to be running
        pass

    def test_verify_ledger_with_server(self):
        """Test ledger verification against live server."""
        # Would test actual ledger verification
        # Requires governance server to be running
        pass
