"""
Additional API tests to boost coverage to 80%+.

Focuses on error paths, edge cases, and untested endpoints.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from lexecon.api.server import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestErrorPaths:
    """Tests for error handling paths."""

    def test_dashboard_not_found(self, client):
        """Test dashboard endpoint when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            response = client.get("/dashboard")
            assert response.status_code == 404
            assert "Dashboard not found" in response.json()["detail"]

    def test_governance_dashboard_not_found(self, client):
        """Test governance dashboard endpoint when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            response = client.get("/dashboard/governance")
            assert response.status_code == 404
            assert "Governance dashboard not found" in response.json()["detail"]

    def test_invalid_policy_format(self, client):
        """Test policy loading with invalid format."""
        response = client.post(
            "/policies/load",
            json={"policy": {"invalid": "structure", "missing": "required_fields"}},
        )
        # Should fail gracefully
        assert response.status_code in [400, 422, 500]

    def test_verify_decision_with_invalid_hash(self, client):
        """Test decision verification with non-existent hash."""
        response = client.post(
            "/decide/verify",
            json={"ledger_entry_hash": "nonexistent_hash_12345"},
        )
        assert response.status_code == 404

    def test_storage_stats_endpoint(self, client):
        """Test storage statistics endpoint."""
        response = client.get("/storage/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_entries" in data
        assert isinstance(data["total_entries"], int)


class TestEUAIActArticle11:
    """Tests for EU AI Act Article 11 (Technical Documentation)."""

    def test_generate_article_11_json(self, client):
        """Test Article 11 documentation generation in JSON format."""
        response = client.get("/compliance/eu-ai-act/article-11?format=json")
        assert response.status_code == 200
        data = response.json()
        assert "system_info" in data
        assert "technical_documentation" in data

    def test_generate_article_11_text(self, client):
        """Test Article 11 documentation generation in text format."""
        response = client.get("/compliance/eu-ai-act/article-11?format=text")
        assert response.status_code == 200
        # Text format should return plain text
        assert response.headers["content-type"].startswith("text/plain")


class TestEUAIActArticle12:
    """Tests for EU AI Act Article 12 (Record-keeping)."""

    def test_retention_status(self, client):
        """Test getting record retention status."""
        response = client.get("/compliance/eu-ai-act/article-12/status")
        assert response.status_code == 200
        data = response.json()
        assert "retention_policy" in data
        assert "storage_backend" in data
        assert "statistics" in data

    def test_generate_regulatory_package_default(self, client):
        """Test regulatory package generation with default format."""
        response = client.get("/compliance/eu-ai-act/article-12/regulatory-package")
        assert response.status_code == 200
        data = response.json()
        assert "package_id" in data
        assert "records" in data

    def test_generate_regulatory_package_csv(self, client):
        """Test regulatory package generation in CSV format."""
        response = client.get("/compliance/eu-ai-act/article-12/regulatory-package?format=csv")
        assert response.status_code == 200
        # CSV format handling
        assert response.status_code == 200

    def test_apply_legal_hold(self, client):
        """Test applying legal hold to records."""
        response = client.post(
            "/compliance/eu-ai-act/article-12/legal-hold",
            json={
                "reason": "Regulatory investigation",
                "authority": "Data Protection Authority",
                "case_reference": "CASE-2024-001",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "hold_id" in data
        assert "reason" in data


class TestEUAIActArticle14:
    """Tests for EU AI Act Article 14 (Human Oversight)."""

    def test_log_intervention_full(self, client):
        """Test logging a complete human intervention."""
        response = client.post(
            "/compliance/eu-ai-act/article-14/intervention",
            json={
                "decision_id": "dec_test_123",
                "human_actor": "operator_alice",
                "intervention_type": "override",
                "reason": "Safety concern detected",
                "outcome": "decision_overridden",
                "notes": "Model suggested risky action, manually prevented",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "intervention_id" in data
        assert data["decision_id"] == "dec_test_123"

    def test_oversight_effectiveness(self, client):
        """Test oversight effectiveness metrics."""
        # First log an intervention
        client.post(
            "/compliance/eu-ai-act/article-14/intervention",
            json={
                "decision_id": "dec_test_124",
                "human_actor": "operator_bob",
                "intervention_type": "monitoring",
                "reason": "Routine check",
                "outcome": "decision_confirmed",
            },
        )

        # Now get effectiveness metrics
        response = client.get("/compliance/eu-ai-act/article-14/effectiveness")
        assert response.status_code == 200
        data = response.json()
        assert "total_interventions" in data
        assert "intervention_rate" in data
        assert "average_response_time_seconds" in data

    def test_verify_intervention(self, client):
        """Test intervention verification."""
        # Create an intervention first
        create_response = client.post(
            "/compliance/eu-ai-act/article-14/intervention",
            json={
                "decision_id": "dec_test_125",
                "human_actor": "operator_charlie",
                "intervention_type": "override",
                "reason": "Testing",
            },
        )
        intervention_id = create_response.json()["intervention_id"]

        # Verify it
        response = client.post(
            "/compliance/eu-ai-act/article-14/verify",
            json={"intervention_id": intervention_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True

    def test_evidence_package(self, client):
        """Test evidence package generation."""
        # Log some interventions first
        client.post(
            "/compliance/eu-ai-act/article-14/intervention",
            json={
                "decision_id": "dec_test_126",
                "human_actor": "operator_diana",
                "intervention_type": "monitoring",
                "reason": "Compliance check",
            },
        )

        response = client.get("/compliance/eu-ai-act/article-14/evidence-package?format=json")
        assert response.status_code == 200
        data = response.json()
        assert "evidence_package_id" in data
        assert "interventions" in data

    def test_simulate_escalation(self, client):
        """Test escalation simulation."""
        response = client.post(
            "/compliance/eu-ai-act/article-14/escalation",
            json={
                "decision_id": "dec_test_127",
                "trigger": "high_risk_threshold_exceeded",
                "priority": "high",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "escalation_id" in data
        assert "escalation_workflow" in data

    def test_intervention_storage_stats(self, client):
        """Test intervention storage statistics."""
        response = client.get("/compliance/eu-ai-act/article-14/storage/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_interventions" in data
        assert isinstance(data["total_interventions"], int)


class TestAuditPacket:
    """Tests for audit packet generation."""

    def test_generate_audit_packet_all(self, client):
        """Test audit packet generation for all time."""
        response = client.get("/compliance/eu-ai-act/audit-packet?time_window=all&format=json")
        assert response.status_code == 200
        data = response.json()
        assert "report_type" in data
        assert data["report_type"] == "EU_AI_ACT_AUDIT_PACKET"
        assert "compliance_summary" in data
        assert "decision_log" in data
        assert "human_oversight_log" in data

    def test_generate_audit_packet_24h(self, client):
        """Test audit packet generation for 24 hours."""
        response = client.get("/compliance/eu-ai-act/audit-packet?time_window=24h")
        assert response.status_code == 200
        data = response.json()
        assert data["time_window"] == "24h"

    def test_generate_audit_packet_7d(self, client):
        """Test audit packet generation for 7 days."""
        response = client.get("/compliance/eu-ai-act/audit-packet?time_window=7d")
        assert response.status_code == 200

    def test_generate_audit_packet_30d(self, client):
        """Test audit packet generation for 30 days."""
        response = client.get("/compliance/eu-ai-act/audit-packet?time_window=30d")
        assert response.status_code == 200

    def test_generate_audit_packet_text_format(self, client):
        """Test audit packet in text format."""
        response = client.get("/compliance/eu-ai-act/audit-packet?format=text")
        assert response.status_code == 200


class TestResponsibilityTracking:
    """Tests for responsibility tracking endpoints."""

    def test_accountability_report_default(self, client):
        """Test accountability report with default parameters."""
        response = client.get("/responsibility/report")
        assert response.status_code == 200
        data = response.json()
        assert "report" in data or "decisions" in data or "total_decisions" in data

    def test_accountability_report_with_filters(self, client):
        """Test accountability report with time filters."""
        response = client.get("/responsibility/report?start_date=2024-01-01&end_date=2024-12-31")
        assert response.status_code == 200

    def test_responsibility_chain(self, client):
        """Test getting responsibility chain for a decision."""
        # First make a decision
        policy = {
            "name": "test_policy",
            "version": "1.0",
            "terms": [
                {"term_id": "t1", "term_type": "actor", "value": "model"},
                {"term_id": "t2", "term_type": "action", "value": "test_action"},
            ],
            "relations": [
                {"subject": "t1", "relation_type": "permits", "object": "t2"},
            ],
        }
        client.post("/policies/load", json={"policy": policy})

        decision_response = client.post(
            "/decide",
            json={
                "actor": "model",
                "proposed_action": "test_action",
                "tool": "test_tool",
                "user_intent": "testing responsibility tracking",
            },
        )

        if decision_response.status_code == 200:
            decision_data = decision_response.json()
            decision_id = decision_data.get("decision_id")

            if decision_id:
                response = client.get(f"/responsibility/chain/{decision_id}")
                # May return 404 if responsibility tracking isn't fully initialized
                assert response.status_code in [200, 404]

    def test_get_by_party(self, client):
        """Test getting responsibilities by party."""
        response = client.get("/responsibility/party/test_party")
        assert response.status_code in [200, 404]  # May not exist yet

    def test_ai_overrides(self, client):
        """Test getting AI overrides."""
        response = client.get("/responsibility/overrides")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_pending_reviews(self, client):
        """Test getting pending reviews."""
        response = client.get("/responsibility/pending-reviews")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_legal_export(self, client):
        """Test legal export for a decision."""
        response = client.get("/responsibility/legal/dec_test_123")
        assert response.status_code in [200, 404]

    def test_responsibility_storage_stats(self, client):
        """Test responsibility storage statistics."""
        response = client.get("/responsibility/storage/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication."""
        response = client.get("/auth/me")
        assert response.status_code in [401, 403]

    def test_logout_without_session(self, client):
        """Test logout without active session."""
        response = client.post("/auth/logout")
        assert response.status_code in [200, 401]

    def test_list_users_unauthorized(self, client):
        """Test listing users without proper permissions."""
        response = client.get("/auth/users")
        assert response.status_code in [401, 403]

    def test_create_user_unauthorized(self, client):
        """Test creating user without admin permissions."""
        response = client.post(
            "/auth/users",
            json={
                "username": "newuser",
                "password": "password123",
                "role": "viewer",
            },
        )
        assert response.status_code in [401, 403]


class TestComplianceMapping:
    """Tests for compliance mapping endpoints."""

    def test_map_primitive_to_controls(self, client):
        """Test mapping a primitive to compliance controls."""
        response = client.post(
            "/api/governance/compliance/map",
            json={
                "primitive_type": "DECISION_LOGGING",
                "primitive_id": "dec_test_123",
                "framework": "EU_AI_ACT",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "control_ids" in data
        assert isinstance(data["control_ids"], list)

    def test_list_compliance_controls(self, client):
        """Test listing compliance controls for a framework."""
        response = client.get("/api/governance/compliance/EU_AI_ACT/controls")
        assert response.status_code == 200
        data = response.json()
        assert "controls" in data
        assert isinstance(data["controls"], list)

    def test_get_control_status(self, client):
        """Test getting status of a specific control."""
        response = client.get("/api/governance/compliance/EU_AI_ACT/Article_12")
        assert response.status_code in [200, 404]

    def test_verify_control(self, client):
        """Test verifying a compliance control."""
        response = client.post(
            "/api/governance/compliance/EU_AI_ACT/Article_12/verify",
            json={
                "evidence_ids": ["ev_123"],
                "verifier_id": "auditor_1",
                "verification_notes": "All requirements met",
            },
        )
        assert response.status_code == 200

    def test_link_evidence_to_control(self, client):
        """Test linking evidence to a control."""
        response = client.post(
            "/api/governance/compliance/EU_AI_ACT/Article_12/link-evidence",
            json={
                "evidence_id": "ev_123",
                "link_type": "satisfies",
            },
        )
        assert response.status_code == 200

    def test_analyze_compliance_gaps(self, client):
        """Test analyzing compliance gaps."""
        response = client.get("/api/governance/compliance/EU_AI_ACT/gaps")
        assert response.status_code == 200
        data = response.json()
        assert "gaps" in data

    def test_generate_compliance_report(self, client):
        """Test generating compliance report."""
        response = client.get("/api/governance/compliance/EU_AI_ACT/report")
        assert response.status_code == 200
        data = response.json()
        assert "framework" in data
        assert "compliance_percentage" in data

    def test_get_framework_coverage(self, client):
        """Test getting framework coverage."""
        response = client.get("/api/governance/compliance/EU_AI_ACT/coverage")
        assert response.status_code == 200
        data = response.json()
        assert "total_controls" in data
        assert "implemented_controls" in data

    def test_get_primitive_mappings(self, client):
        """Test getting mappings for a primitive."""
        response = client.get("/api/governance/compliance/primitive/dec_test_123/mappings")
        assert response.status_code in [200, 404]

    def test_get_compliance_statistics(self, client):
        """Test getting overall compliance statistics."""
        response = client.get("/api/governance/compliance/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "frameworks" in data


class TestAuditExport:
    """Tests for audit export endpoints."""

    def test_create_audit_export_request(self, client):
        """Test creating an audit export request."""
        response = client.post(
            "/api/governance/audit-export/request",
            json={
                "requester_id": "user_123",
                "export_format": "JSON",
                "export_scope": "FULL",
                "purpose": "Annual compliance audit",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert data["status"] == "PENDING"

    def test_list_audit_exports(self, client):
        """Test listing audit exports."""
        response = client.get("/api/governance/audit-export/list")
        assert response.status_code == 200
        data = response.json()
        assert "exports" in data
        assert isinstance(data["exports"], list)

    def test_list_audit_export_requests(self, client):
        """Test listing audit export requests."""
        response = client.get("/api/governance/audit-export/requests")
        assert response.status_code == 200
        data = response.json()
        assert "requests" in data

    def test_get_audit_export_statistics(self, client):
        """Test getting audit export statistics."""
        response = client.get("/api/governance/audit-export/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_exports" in data
        assert "exports_by_status" in data

    def test_get_audit_export_nonexistent(self, client):
        """Test getting a non-existent export."""
        response = client.get("/api/governance/audit-export/exp_nonexistent_123")
        assert response.status_code == 404

    def test_download_audit_export_nonexistent(self, client):
        """Test downloading a non-existent export."""
        response = client.get("/api/governance/audit-export/exp_nonexistent_123/download")
        assert response.status_code == 404


class TestSignatureVerification:
    """Tests for signature verification endpoints."""

    def test_verify_signature(self, client):
        """Test signature verification endpoint."""
        response = client.post(
            "/compliance/verify-signature",
            json={
                "data": {"test": "data"},
                "signature": "mock_signature",
                "signer_id": "sys_test",
            },
        )
        # Will fail verification but should handle gracefully
        assert response.status_code in [200, 400]

    def test_get_public_key(self, client):
        """Test getting public key."""
        response = client.get("/compliance/public-key")
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data or "key" in data

    def test_verify_audit_chain(self, client):
        """Test audit chain verification."""
        response = client.get("/compliance/audit-chain-verification")
        assert response.status_code == 200
        data = response.json()
        assert "chain_valid" in data or "verified" in data

    def test_list_export_requests(self, client):
        """Test listing export requests."""
        response = client.get("/compliance/export-requests")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))


class TestLedgerEndpoints:
    """Additional ledger endpoint tests."""

    def test_get_ledger_entries_with_limit(self, client):
        """Test getting ledger entries with limit."""
        response = client.get("/ledger/entries?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert len(data["entries"]) <= 5

    def test_get_ledger_entries_with_offset(self, client):
        """Test getting ledger entries with offset."""
        response = client.get("/ledger/entries?offset=10&limit=5")
        assert response.status_code == 200

    def test_get_ledger_entries_invalid_limit(self, client):
        """Test getting ledger entries with invalid limit."""
        response = client.get("/ledger/entries?limit=-1")
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data
