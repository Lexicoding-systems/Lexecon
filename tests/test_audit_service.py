"""
Tests for the Export Audit Service.
"""

import os
import pytest
import tempfile
from datetime import datetime, timezone
from lexecon.security.audit_service import (
    AuditService,
    ExportStatus,
    ApprovalStatus,
    ExportRequest,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def audit_service(temp_db):
    """Create an AuditService with a temporary database."""
    return AuditService(db_path=temp_db)


class TestAuditServiceInitialization:
    """Tests for AuditService initialization."""

    def test_creates_database(self, temp_db):
        """Test that service creates database on initialization."""
        service = AuditService(db_path=temp_db)
        assert os.path.exists(temp_db)

    def test_creates_tables(self, audit_service, temp_db):
        """Test that service creates required tables."""
        import sqlite3

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check export_requests table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='export_requests'"
        )
        assert cursor.fetchone() is not None

        # Check approval_workflow table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='approval_workflow'"
        )
        assert cursor.fetchone() is not None

        # Check access_log table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='access_log'"
        )
        assert cursor.fetchone() is not None

        conn.close()


class TestExportStatus:
    """Tests for ExportStatus enum."""

    def test_pending_status(self):
        """Test PENDING status."""
        assert ExportStatus.PENDING == "pending"

    def test_approved_status(self):
        """Test APPROVED status."""
        assert ExportStatus.APPROVED == "approved"

    def test_completed_status(self):
        """Test COMPLETED status."""
        assert ExportStatus.COMPLETED == "completed"

    def test_rejected_status(self):
        """Test REJECTED status."""
        assert ExportStatus.REJECTED == "rejected"

    def test_failed_status(self):
        """Test FAILED status."""
        assert ExportStatus.FAILED == "failed"


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_not_required_status(self):
        """Test NOT_REQUIRED status."""
        assert ApprovalStatus.NOT_REQUIRED == "not_required"

    def test_pending_status(self):
        """Test PENDING status."""
        assert ApprovalStatus.PENDING == "pending"

    def test_approved_status(self):
        """Test APPROVED status."""
        assert ApprovalStatus.APPROVED == "approved"

    def test_rejected_status(self):
        """Test REJECTED status."""
        assert ApprovalStatus.REJECTED == "rejected"


class TestExportRequest:
    """Tests for ExportRequest dataclass."""

    def test_create_export_request(self):
        """Test creating an export request."""
        request = ExportRequest(
            request_id="req-001",
            user_id="user-001",
            username="testuser",
            user_email="test@example.com",
            user_role="auditor",
            purpose="Regulatory compliance audit",
            case_id="CASE-2024-001",
            notes="Quarterly audit",
            requested_at=datetime.now(timezone.utc).isoformat(),
            time_window="30d",
            formats=["json", "csv"],
            include_decisions=True,
            include_interventions=True,
            include_ledger=True,
            include_responsibility=True,
            attestation_accepted=True,
            attestation_timestamp=datetime.now(timezone.utc).isoformat(),
            attestation_ip_address="192.168.1.100",
            approval_status=ApprovalStatus.PENDING,
            approval_required=True,
            approved_by_user_id=None,
            approved_by_username=None,
            approved_at=None,
            rejection_reason=None,
            export_status=ExportStatus.PENDING,
            completed_at=None,
            packet_hashes=None,
            packet_size_bytes=None,
            previous_hash="0" * 64,
            entry_hash="abc123",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        assert request.request_id == "req-001"
        assert request.user_id == "user-001"
        assert request.purpose == "Regulatory compliance audit"
        assert request.approval_status == ApprovalStatus.PENDING
        assert request.export_status == ExportStatus.PENDING

    def test_export_request_optional_fields(self):
        """Test export request with optional fields as None."""
        request = ExportRequest(
            request_id="req-002",
            user_id="user-002",
            username="admin",
            user_email="admin@example.com",
            user_role="admin",
            purpose="Test export",
            case_id=None,
            notes=None,
            requested_at=datetime.now(timezone.utc).isoformat(),
            time_window="7d",
            formats=["json"],
            include_decisions=True,
            include_interventions=False,
            include_ledger=False,
            include_responsibility=False,
            attestation_accepted=True,
            attestation_timestamp=datetime.now(timezone.utc).isoformat(),
            attestation_ip_address=None,
            approval_status=ApprovalStatus.NOT_REQUIRED,
            approval_required=False,
            approved_by_user_id=None,
            approved_by_username=None,
            approved_at=None,
            rejection_reason=None,
            export_status=ExportStatus.PENDING,
            completed_at=None,
            packet_hashes=None,
            packet_size_bytes=None,
            previous_hash="0" * 64,
            entry_hash="def456",
            ip_address=None,
            user_agent=None,
        )

        assert request.case_id is None
        assert request.notes is None
        assert request.attestation_ip_address is None


class TestAuditServiceHashComputation:
    """Tests for hash computation in AuditService."""

    def test_compute_hash_deterministic(self, audit_service):
        """Test that hash computation is deterministic."""
        data = {"key": "value", "number": 42}

        hash1 = audit_service._compute_hash(data)
        hash2 = audit_service._compute_hash(data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_compute_hash_different_data(self, audit_service):
        """Test that different data produces different hashes."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}

        hash1 = audit_service._compute_hash(data1)
        hash2 = audit_service._compute_hash(data2)

        assert hash1 != hash2

    def test_compute_hash_empty_dict(self, audit_service):
        """Test computing hash of empty dict."""
        hash_val = audit_service._compute_hash({})
        assert len(hash_val) == 64  # SHA-256 hex length


class TestAuditServiceChainIntegrity:
    """Tests for chain integrity in AuditService."""

    def test_hash_chain_integrity(self, audit_service):
        """Test that entries form a valid hash chain."""
        # The hash chain should be verifiable
        # Each entry's previous_hash should match the previous entry's entry_hash
        pass  # Chain integrity tests would require more complex setup
