"""Integration tests for Lexecon API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_health_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "node_id" in data

    def test_status_endpoint_returns_metrics(self, client: TestClient) -> None:
        """Test that status endpoint returns system metrics."""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "node_id" in data
        assert "policies_loaded" in data
        assert "ledger_entries" in data
        assert "uptime_seconds" in data


class TestPolicyEndpoints:
    """Test policy management endpoints."""

    def test_list_policies_returns_array(self, client: TestClient) -> None:
        """Test that list policies endpoint returns array."""
        response = client.get("/policies")
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert isinstance(data["policies"], list)

    def test_load_policy_validates_schema(self, client: TestClient) -> None:
        """Test that invalid policy is rejected."""
        invalid_policy = {"name": "Test"}
        response = client.post("/policies/load", json=invalid_policy)
        assert response.status_code in [400, 422]  # Validation error

    def test_load_valid_policy_succeeds(self, client: TestClient) -> None:
        """Test loading a valid policy."""
        valid_policy = {
            "name": "Test Policy",
            "version": "1.0",
            "mode": "strict",
            "terms": [],
            "relations": [],
            "constraints": [],
        }
        response = client.post("/policies/load", json=valid_policy)
        assert response.status_code == 200


class TestDecisionEndpoints:
    """Test decision-making endpoints."""

    def test_decide_requires_valid_request(self, client: TestClient) -> None:
        """Test that decision endpoint validates request."""
        invalid_request = {"actor": "model"}
        response = client.post("/decide", json=invalid_request)
        assert response.status_code in [400, 422]

    def test_decide_returns_decision_response(self, client: TestClient) -> None:
        """Test that valid decision request returns proper response."""
        valid_request = {
            "request_id": "test_001",
            "actor": "model",
            "proposed_action": "Execute web_search",
            "tool": "web_search",
            "user_intent": "Research AI governance",
            "risk_level": 1,
            "policy_mode": "strict",
        }
        response = client.post("/decide", json=valid_request)
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "allowed" in data
        assert "reason" in data
        assert "policy_version_hash" in data
        assert "timestamp" in data
        assert "signature" in data

    def test_decide_with_high_risk_level(self, client: TestClient) -> None:
        """Test decision with high risk level."""
        high_risk_request = {
            "request_id": "test_002",
            "actor": "model",
            "proposed_action": "Delete production database",
            "tool": "database_admin",
            "user_intent": "Clean up data",
            "risk_level": 5,
            "policy_mode": "paranoid",
        }
        response = client.post("/decide", json=high_risk_request)
        assert response.status_code == 200
        data = response.json()
        # High risk actions should typically be denied or require confirmation
        assert "allowed" in data

    def test_decide_creates_ledger_entry(self, client: TestClient) -> None:
        """Test that decision creates ledger entry."""
        request = {
            "request_id": "test_003",
            "actor": "model",
            "proposed_action": "Read public data",
            "tool": "read",
            "user_intent": "Get information",
            "risk_level": 1,
            "policy_mode": "strict",
        }
        response = client.post("/decide", json=request)
        assert response.status_code == 200
        data = response.json()
        assert "ledger_entry_hash" in data
        assert data["ledger_entry_hash"] is not None

    def test_decide_verify_endpoint(self, client: TestClient) -> None:
        """Test decision verification endpoint."""
        # First make a decision
        request = {
            "request_id": "test_004",
            "actor": "model",
            "proposed_action": "Test action",
            "tool": "test_tool",
            "user_intent": "Testing",
            "risk_level": 1,
            "policy_mode": "strict",
        }
        decision_response = client.post("/decide", json=request)
        assert decision_response.status_code == 200
        decision_data = decision_response.json()

        # Then verify it
        verify_request = {
            "decision_response": decision_data,
            "original_request": request,
        }
        verify_response = client.post("/decide/verify", json=verify_request)
        assert verify_response.status_code == 200


class TestLedgerEndpoints:
    """Test ledger operations endpoints."""

    def test_ledger_verify_checks_integrity(self, client: TestClient) -> None:
        """Test that ledger verify endpoint checks integrity."""
        response = client.get("/ledger/verify")
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "entries_checked" in data
        assert "chain_intact" in data

    def test_ledger_report_generates_audit_report(self, client: TestClient) -> None:
        """Test ledger report generation."""
        response = client.get("/ledger/report?format=json")
        assert response.status_code == 200
        # Report should contain audit information


class TestErrorHandling:
    """Test API error handling."""

    def test_invalid_endpoint_returns_404(self, client: TestClient) -> None:
        """Test that invalid endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_malformed_json_returns_400(self, client: TestClient) -> None:
        """Test that malformed JSON returns 400."""
        response = client.post(
            "/decide",
            data="{invalid json}",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]

    def test_missing_required_fields_returns_422(self, client: TestClient) -> None:
        """Test that missing required fields returns validation error."""
        incomplete_request = {"actor": "model"}
        response = client.post("/decide", json=incomplete_request)
        assert response.status_code == 422


class TestCapabilityTokens:
    """Test capability token functionality."""

    def test_allowed_decision_includes_token(self, client: TestClient) -> None:
        """Test that allowed decisions include capability token."""
        request = {
            "request_id": "test_005",
            "actor": "model",
            "proposed_action": "Safe action",
            "tool": "safe_tool",
            "user_intent": "Safe operation",
            "risk_level": 1,
            "policy_mode": "permissive",
        }
        response = client.post("/decide", json=request)
        assert response.status_code == 200
        data = response.json()
        if data["allowed"]:
            assert "capability_token" in data
            token = data["capability_token"]
            assert "token_id" in token
            assert "scope" in token
            assert "expiry" in token
            assert "signature" in token


@pytest.fixture
def client() -> TestClient:
    """Create test client for API."""
    from lexecon.api.server import app

    return TestClient(app)
