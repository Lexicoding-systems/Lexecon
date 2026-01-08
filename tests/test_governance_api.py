"""
Tests for Governance API endpoints (Phase 5).

Tests REST API endpoints for Risk, Escalation, Override, and Evidence services.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from lexecon.api.server import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestRiskAPI:
    """Tests for Risk Service API endpoints."""

    def test_assess_risk(self, client):
        """Test risk assessment endpoint."""
        response = client.post(
            "/api/governance/risk/assess",
            json={
                "decision_id": "dec_test_123",
                "dimensions": {
                    "security": 85,
                    "privacy": 70,
                    "compliance": 60,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "risk_id" in data
        assert data["decision_id"] == "dec_test_123"
        assert "overall_score" in data
        assert "risk_level" in data
        assert data["dimensions"]["security"] == 85
        assert data["dimensions"]["privacy"] == 70
        assert data["dimensions"]["compliance"] == 60

    def test_get_risk(self, client):
        """Test get risk by ID endpoint."""
        # First create a risk
        create_response = client.post(
            "/api/governance/risk/assess",
            json={
                "decision_id": "dec_test_456",
                "dimensions": {"security": 50},
            },
        )
        risk_id = create_response.json()["risk_id"]

        # Now get it
        response = client.get(f"/api/governance/risk/{risk_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["risk_id"] == risk_id
        assert data["decision_id"] == "dec_test_456"

    def test_get_risk_not_found(self, client):
        """Test get risk with non-existent ID."""
        response = client.get("/api/governance/risk/rsk_invalid_999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_risk_for_decision(self, client):
        """Test get risk for decision endpoint."""
        decision_id = "dec_test_789"

        # Create risk for decision
        client.post(
            "/api/governance/risk/assess",
            json={
                "decision_id": decision_id,
                "dimensions": {"security": 75},
            },
        )

        # Get risk for decision
        response = client.get(f"/api/governance/risk/decision/{decision_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["decision_id"] == decision_id
        assert "risk_id" in data

    def test_assess_risk_invalid_dimensions(self, client):
        """Test risk assessment with invalid dimensions."""
        response = client.post(
            "/api/governance/risk/assess",
            json={
                "decision_id": "dec_test_invalid",
                "dimensions": {
                    "security": 150,  # Invalid: exceeds 100
                },
            },
        )

        assert response.status_code == 422  # Validation error

    def test_assess_risk_duplicate_decision(self, client):
        """Test assessing risk for same decision twice (should fail)."""
        decision_id = "dec_test_duplicate"

        # First assessment
        response1 = client.post(
            "/api/governance/risk/assess",
            json={
                "decision_id": decision_id,
                "dimensions": {"security": 50},
            },
        )
        assert response1.status_code == 200

        # Second assessment for same decision (should fail)
        response2 = client.post(
            "/api/governance/risk/assess",
            json={
                "decision_id": decision_id,
                "dimensions": {"security": 60},
            },
        )
        assert response2.status_code == 400
        assert "already has risk" in response2.json()["detail"].lower()


class TestEscalationAPI:
    """Tests for Escalation Service API endpoints."""

    def test_create_escalation(self, client):
        """Test escalation creation endpoint."""
        response = client.post(
            "/api/governance/escalation",
            json={
                "decision_id": "dec_esc_001",
                "trigger": "risk_threshold",
                "escalated_to": ["act_human_user:manager"],
                "priority": "high",
                "context_summary": "Risk score exceeded threshold of 80",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "escalation_id" in data
        assert data["decision_id"] == "dec_esc_001"
        assert data["priority"] == "high"
        assert data["status"] == "pending"
        assert "sla_deadline" in data

    def test_resolve_escalation(self, client):
        """Test escalation resolution endpoint."""
        # Create escalation
        create_response = client.post(
            "/api/governance/escalation",
            json={
                "decision_id": "dec_esc_002",
                "trigger": "policy_conflict",
                "escalated_to": ["act_human_user:reviewer"],
                "priority": "medium",
                "context_summary": "Policy violation detected",
            },
        )
        escalation_id = create_response.json()["escalation_id"]

        # Resolve it
        response = client.post(
            f"/api/governance/escalation/{escalation_id}/resolve",
            json={
                "resolved_by": "act_human_user:reviewer",
                "outcome": "approved",
                "notes": "Approved after review with additional monitoring",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["escalation_id"] == escalation_id
        assert data["status"] == "resolved"
        assert data["outcome"] == "approved"
        assert "resolved_at" in data

    def test_get_escalation(self, client):
        """Test get escalation by ID endpoint."""
        # Create escalation
        create_response = client.post(
            "/api/governance/escalation",
            json={
                "decision_id": "dec_esc_003",
                "trigger": "risk_threshold",
                "escalated_to": ["act_human_user:admin"],
                "priority": "low",
                "context_summary": "Test escalation",
            },
        )
        escalation_id = create_response.json()["escalation_id"]

        # Get it
        response = client.get(f"/api/governance/escalation/{escalation_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["escalation_id"] == escalation_id
        assert "status" in data
        assert "priority" in data

    def test_get_escalations_for_decision(self, client):
        """Test get all escalations for a decision."""
        decision_id = "dec_esc_multiple"

        # Create multiple escalations
        for i in range(3):
            client.post(
                "/api/governance/escalation",
                json={
                    "decision_id": decision_id,
                    "trigger": "risk_threshold",
                    "escalated_to": ["act_human_user:admin"],
                    "priority": "low",
                    "context_summary": f"Context {i}",
                },
            )

        # Get all escalations
        response = client.get(f"/api/governance/escalation/decision/{decision_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["decision_id"] == decision_id
        assert data["count"] == 3
        assert len(data["escalations"]) == 3

    def test_get_sla_violations(self, client):
        """Test get SLA violations endpoint."""
        response = client.get("/api/governance/escalation/sla/violations")

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "violations" in data
        assert isinstance(data["violations"], list)

    def test_create_escalation_invalid_priority(self, client):
        """Test creating escalation with invalid priority."""
        response = client.post(
            "/api/governance/escalation",
            json={
                "decision_id": "dec_esc_invalid",
                "trigger": "risk_threshold",
                "escalated_to": ["act_human_user:admin"],
                "priority": "invalid_priority",
                "context_summary": "Test",
            },
        )

        assert response.status_code == 400  # Endpoint catches ValueError and returns 400


class TestOverrideAPI:
    """Tests for Override Service API endpoints."""

    def test_create_override(self, client):
        """Test override creation endpoint."""
        response = client.post(
            "/api/governance/override",
            json={
                "decision_id": "dec_ovr_001",
                "override_type": "executive_override",
                "authorized_by": "act_human_user:executive:ceo",
                "justification": "Emergency business requirement necessitates temporary policy exception for critical customer deployment.",
                "original_outcome": "denied",
                "new_outcome": "approved",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "override_id" in data
        assert data["decision_id"] == "dec_ovr_001"
        assert data["override_type"] == "executive_override"
        assert "timestamp" in data
        assert "evidence_ids" in data

    def test_get_override(self, client):
        """Test get override by ID endpoint."""
        # Create override
        create_response = client.post(
            "/api/governance/override",
            json={
                "decision_id": "dec_ovr_002",
                "override_type": "risk_accepted",
                "authorized_by": "act_human_user:governance_lead:john",
                "justification": "Manual review completed and decision approved after detailed analysis of risk factors.",
            },
        )
        override_id = create_response.json()["override_id"]

        # Get it
        response = client.get(f"/api/governance/override/{override_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["override_id"] == override_id
        assert "justification" in data

    def test_get_overrides_for_decision(self, client):
        """Test get all overrides for a decision."""
        decision_id = "dec_ovr_multi"

        # Create multiple overrides
        for i in range(2):
            client.post(
                "/api/governance/override",
                json={
                    "decision_id": decision_id,
                    "override_type": "time_limited_exception",
                    "authorized_by": "act_human_user:executive:ceo",
                    "justification": f"Override justification number {i} with sufficient detail for audit trail.",
                },
            )

        # Get all overrides
        response = client.get(f"/api/governance/override/decision/{decision_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["decision_id"] == decision_id
        assert data["count"] == 2

    def test_check_active_override(self, client):
        """Test check if decision has active override."""
        decision_id = "dec_ovr_active"

        # Create override
        client.post(
            "/api/governance/override",
            json={
                "decision_id": decision_id,
                "override_type": "emergency_bypass",
                "authorized_by": "act_human_user:executive:ceo",
                "justification": "Active override test with detailed business justification for policy exception.",
            },
        )

        # Check active override
        response = client.get(f"/api/governance/override/decision/{decision_id}/active")

        assert response.status_code == 200
        data = response.json()
        assert data["decision_id"] == decision_id
        assert data["is_overridden"] is True
        assert "override" in data

    def test_get_decision_with_override_status(self, client):
        """Test get decision enriched with override status."""
        decision_id = "dec_ovr_status"

        # Create override
        client.post(
            "/api/governance/override",
            json={
                "decision_id": decision_id,
                "override_type": "executive_override",
                "authorized_by": "act_human_user:executive:ceo",
                "justification": "Testing override status enrichment with proper justification length requirement.",
            },
        )

        # Get decision with override status
        response = client.get(f"/api/governance/override/decision/{decision_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert "override_status" in data
        assert data["override_status"]["is_overridden"] is True

    def test_create_override_short_justification(self, client):
        """Test creating override with too short justification."""
        response = client.post(
            "/api/governance/override",
            json={
                "decision_id": "dec_ovr_short",
                "override_type": "risk_accepted",
                "authorized_by": "act_human_user:executive:ceo",
                "justification": "Too short",  # Less than 20 chars
            },
        )

        assert response.status_code == 422  # Validation error

    def test_create_override_unauthorized(self, client):
        """Test creating override with unauthorized actor."""
        response = client.post(
            "/api/governance/override",
            json={
                "decision_id": "dec_ovr_unauth",
                "override_type": "executive_override",
                "authorized_by": "act_human_user:regular_user",  # Not authorized
                "justification": "This should fail due to insufficient authorization level for executive override.",
            },
        )

        assert response.status_code == 400
        assert "not authorized" in response.json()["detail"].lower()


class TestEvidenceAPI:
    """Tests for Evidence Service API endpoints."""

    def test_store_evidence_artifact(self, client):
        """Test storing evidence artifact."""
        response = client.post(
            "/api/governance/evidence",
            json={
                "artifact_type": "decision_log",
                "content": "Test decision log content",
                "source": "test_api",
                "related_decision_ids": ["dec_test_001"],
                "content_type": "text/plain",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "artifact_id" in data
        assert data["artifact_type"] == "decision_log"
        assert "sha256_hash" in data
        assert data["source"] == "test_api"
        assert data["is_immutable"] is True

    def test_get_evidence_artifact(self, client):
        """Test get evidence artifact by ID."""
        # Store artifact
        store_response = client.post(
            "/api/governance/evidence",
            json={
                "artifact_type": "attestation",
                "content": "Test attestation content",
                "source": "test_api",
            },
        )
        artifact_id = store_response.json()["artifact_id"]

        # Get it
        response = client.get(f"/api/governance/evidence/{artifact_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["artifact_id"] == artifact_id
        assert "sha256_hash" in data
        assert "created_at" in data

    def test_verify_evidence_artifact(self, client):
        """Test verifying artifact integrity."""
        content = "Original content for verification"

        # Store artifact
        store_response = client.post(
            "/api/governance/evidence",
            json={
                "artifact_type": "policy_snapshot",
                "content": content,
                "source": "test_api",
            },
        )
        artifact_id = store_response.json()["artifact_id"]

        # Verify with correct content
        response = client.post(
            f"/api/governance/evidence/{artifact_id}/verify",
            json={"content": content},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert "stored_hash" in data

    def test_verify_evidence_artifact_tampered(self, client):
        """Test verifying tampered artifact."""
        # Store artifact
        store_response = client.post(
            "/api/governance/evidence",
            json={
                "artifact_type": "audit_trail",
                "content": "Original audit trail",
                "source": "test_api",
            },
        )
        artifact_id = store_response.json()["artifact_id"]

        # Verify with different content
        response = client.post(
            f"/api/governance/evidence/{artifact_id}/verify",
            json={"content": "Tampered content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False

    def test_get_artifacts_for_decision(self, client):
        """Test get all artifacts for a decision."""
        decision_id = "dec_evd_001"

        # Store multiple artifacts
        for i in range(3):
            client.post(
                "/api/governance/evidence",
                json={
                    "artifact_type": "context_capture",
                    "content": f"Context {i}",
                    "source": "test_api",
                    "related_decision_ids": [decision_id],
                },
            )

        # Get artifacts
        response = client.get(f"/api/governance/evidence/decision/{decision_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["decision_id"] == decision_id
        assert data["count"] == 3
        assert len(data["artifacts"]) == 3

    def test_export_artifact_lineage(self, client):
        """Test exporting artifact lineage for a decision."""
        decision_id = "dec_evd_lineage"

        # Store artifacts
        for i in range(2):
            client.post(
                "/api/governance/evidence",
                json={
                    "artifact_type": "decision_log",
                    "content": f"Log entry {i}",
                    "source": "test_api",
                    "related_decision_ids": [decision_id],
                },
            )

        # Export lineage
        response = client.get(f"/api/governance/evidence/decision/{decision_id}/lineage")

        assert response.status_code == 200
        data = response.json()
        assert data["decision_id"] == decision_id
        assert data["artifact_count"] == 2
        assert "artifacts" in data
        assert "exported_at" in data

    def test_sign_evidence_artifact(self, client):
        """Test signing an artifact."""
        # Store artifact
        store_response = client.post(
            "/api/governance/evidence",
            json={
                "artifact_type": "signature",
                "content": "Document to be signed",
                "source": "test_api",
            },
        )
        artifact_id = store_response.json()["artifact_id"]

        # Sign it
        response = client.post(
            f"/api/governance/evidence/{artifact_id}/sign",
            json={
                "signer_id": "act_human_user:executive:alice",
                "signature": "base64_encoded_signature_data",
                "algorithm": "RSA-SHA256",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["artifact_id"] == artifact_id
        assert data["signed"] is True
        assert "signer_id" in data
        assert "signed_at" in data

    def test_get_evidence_statistics(self, client):
        """Test get evidence service statistics."""
        response = client.get("/api/governance/evidence/statistics")

        assert response.status_code == 200
        data = response.json()
        assert "total_artifacts" in data
        assert "total_size_bytes" in data
        assert "signed_artifacts" in data

    def test_store_evidence_invalid_type(self, client):
        """Test storing artifact with invalid type."""
        response = client.post(
            "/api/governance/evidence",
            json={
                "artifact_type": "invalid_type",
                "content": "Test content",
                "source": "test_api",
            },
        )

        assert response.status_code == 400


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns governance endpoints."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Lexecon Governance API"
        assert "endpoints" in data

        # Check governance endpoints are documented
        endpoints = data["endpoints"]
        assert "risk_assess" in endpoints
        assert "escalation_create" in endpoints
        assert "override_create" in endpoints
        assert "evidence_store" in endpoints
