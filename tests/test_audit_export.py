"""
Tests for Audit Export Service (Phase 8).

Tests comprehensive governance data export functionality.
"""

import pytest
from datetime import datetime, timezone, timedelta
from lexecon.audit_export.service import (
    AuditExportService,
    ExportFormat,
    ExportScope,
    ExportStatus,
)


@pytest.fixture
def export_service():
    """Create an audit export service instance."""
    return AuditExportService()


@pytest.fixture
def mock_risk_service():
    """Create a mock risk service with test data."""
    from lexecon.risk.service import RiskService, RiskDimensions

    service = RiskService()

    # Add test risks
    service.assess_risk(
        decision_id="dec_001",
        dimensions=RiskDimensions(security=80, privacy=60, compliance=40)
    )
    service.assess_risk(
        decision_id="dec_002",
        dimensions=RiskDimensions(security=30, privacy=20, compliance=10)
    )

    return service


@pytest.fixture
def mock_escalation_service():
    """Create a mock escalation service with test data."""
    from lexecon.escalation.service import EscalationService
    from model_governance_pack.models import EscalationTrigger, EscalationPriority

    service = EscalationService()

    # Add test escalations
    service.create_escalation(
        decision_id="dec_001",
        trigger=EscalationTrigger.RISK_THRESHOLD,
        escalated_to=["manager@example.com"],
        priority=EscalationPriority.HIGH
    )

    return service


@pytest.fixture
def mock_override_service():
    """Create a mock override service with test data."""
    from lexecon.override.service import OverrideService
    from model_governance_pack.models import Override, OverrideType
    from datetime import datetime, timezone
    import uuid

    service = OverrideService()

    # Manually add test override to service storage
    test_override = Override(
        override_id=f"ovr_dec_{uuid.uuid4().hex[:12]}",
        decision_id="dec_001",
        override_type=OverrideType.EMERGENCY_BYPASS,
        authorized_by="admin@example.com",
        justification="Emergency override due to critical business need",
        timestamp=datetime.now(timezone.utc),
        evidence_ids=[]
    )

    # Add to service's internal storage
    service._overrides[test_override.override_id] = test_override
    service._decision_overrides["dec_001"] = [test_override]

    return service


@pytest.fixture
def mock_evidence_service():
    """Create a mock evidence service with test data."""
    from lexecon.evidence.service import EvidenceService
    from model_governance_pack.models import ArtifactType

    service = EvidenceService()

    # Add test artifacts
    service.store_artifact(
        artifact_type=ArtifactType.DECISION_LOG,
        content="Test decision log content",
        source="test_system",
        related_decision_ids=["dec_001"]
    )

    return service


@pytest.fixture
def mock_compliance_service():
    """Create a mock compliance service."""
    from lexecon.compliance_mapping.service import ComplianceMappingService

    return ComplianceMappingService()


@pytest.fixture
def mock_ledger():
    """Create a mock ledger with test data."""
    from lexecon.ledger.chain import LedgerChain

    # Use ledger without persistence for testing
    ledger = LedgerChain()

    # Add test decisions
    ledger.append("decision", {
        "request_id": "req_001",
        "decision": "allow",
        "actor": "system",
        "action": "test_action"
    })

    return ledger


class TestAuditExportService:
    """Tests for AuditExportService."""

    def test_service_initialization(self, export_service):
        """Test service initializes correctly."""
        assert export_service is not None

    def test_create_export_request(self, export_service):
        """Test creating an export request."""
        request = export_service.create_export_request(
            requester="auditor@example.com",
            purpose="Regulatory compliance audit",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON
        )

        assert request is not None
        assert request.export_id.startswith("exp_")
        assert request.requester == "auditor@example.com"
        assert request.purpose == "Regulatory compliance audit"
        assert request.scope == ExportScope.ALL
        assert request.format == ExportFormat.JSON
        assert request.status == ExportStatus.PENDING

    def test_generate_export_all_data(
        self,
        export_service,
        mock_risk_service,
        mock_escalation_service,
        mock_override_service,
        mock_evidence_service,
        mock_compliance_service,
        mock_ledger
    ):
        """Test generating complete export with all data."""
        request = export_service.create_export_request(
            requester="auditor@example.com",
            purpose="Complete audit",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service,
            escalation_service=mock_escalation_service,
            override_service=mock_override_service,
            evidence_service=mock_evidence_service,
            compliance_service=mock_compliance_service,
            ledger=mock_ledger
        )

        assert package is not None
        assert package.export_id == request.export_id
        assert package.format == ExportFormat.JSON
        assert package.size_bytes > 0
        assert package.checksum is not None
        assert request.status == ExportStatus.COMPLETED

        # Check data sections
        assert "risks" in package.data
        assert "escalations" in package.data
        assert "overrides" in package.data
        assert "evidence" in package.data
        assert "compliance" in package.data
        assert "decisions" in package.data
        assert "statistics" in package.data

    def test_export_risk_only(self, export_service, mock_risk_service):
        """Test exporting only risk data."""
        request = export_service.create_export_request(
            requester="risk_analyst@example.com",
            purpose="Risk analysis",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service
        )

        assert package is not None
        assert "risks" in package.data
        assert len(package.data["risks"]) == 2
        # Should not include other data
        assert "escalations" not in package.data
        assert "overrides" not in package.data

    def test_export_with_date_filter(
        self,
        export_service,
        mock_risk_service,
        mock_ledger
    ):
        """Test exporting with date range filter."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=7)
        end_date = now

        request = export_service.create_export_request(
            requester="auditor@example.com",
            purpose="Weekly audit",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
            start_date=start_date,
            end_date=end_date
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service,
            ledger=mock_ledger
        )

        assert package is not None
        assert package.data["export_metadata"]["date_range"]["start"] is not None
        assert package.data["export_metadata"]["date_range"]["end"] is not None

    def test_export_json_format(self, export_service, mock_risk_service):
        """Test JSON export format."""
        request = export_service.create_export_request(
            requester="dev@example.com",
            purpose="Testing",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service
        )

        assert package.format == ExportFormat.JSON
        assert package.content.startswith("{")
        assert "risks" in package.content

    def test_export_csv_format(self, export_service, mock_risk_service):
        """Test CSV export format."""
        request = export_service.create_export_request(
            requester="analyst@example.com",
            purpose="Data analysis",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.CSV
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service
        )

        assert package.format == ExportFormat.CSV
        assert "RISK ASSESSMENTS" in package.content
        assert "risk_id" in package.content

    def test_export_markdown_format(self, export_service, mock_risk_service):
        """Test Markdown export format."""
        request = export_service.create_export_request(
            requester="doc_writer@example.com",
            purpose="Documentation",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.MARKDOWN
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service
        )

        assert package.format == ExportFormat.MARKDOWN
        assert "# Governance Audit Export" in package.content
        assert "## Risk Assessments" in package.content

    def test_export_html_format(self, export_service, mock_risk_service):
        """Test HTML export format."""
        request = export_service.create_export_request(
            requester="reporter@example.com",
            purpose="Report generation",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.HTML
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service
        )

        assert package.format == ExportFormat.HTML
        assert "<!DOCTYPE html>" in package.content
        assert "<h1>Governance Audit Export</h1>" in package.content

    def test_export_statistics_calculation(
        self,
        export_service,
        mock_risk_service,
        mock_escalation_service,
        mock_override_service
    ):
        """Test statistics calculation in export."""
        request = export_service.create_export_request(
            requester="auditor@example.com",
            purpose="Statistics test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service,
            escalation_service=mock_escalation_service,
            override_service=mock_override_service
        )

        stats = package.data["statistics"]
        assert stats["total_risks"] == 2
        assert stats["total_escalations"] == 1
        assert stats["total_overrides"] == 1

    def test_export_checksum_generation(self, export_service, mock_risk_service):
        """Test checksum generation for exports."""
        request = export_service.create_export_request(
            requester="security@example.com",
            purpose="Integrity verification",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service
        )

        assert package.checksum is not None
        assert len(package.checksum) == 64  # SHA-256 hex digest

        # Verify checksum is correct
        import hashlib
        expected_checksum = hashlib.sha256(package.content.encode()).hexdigest()
        assert package.checksum == expected_checksum

    def test_get_export(self, export_service, mock_risk_service):
        """Test retrieving an export by ID."""
        request = export_service.create_export_request(
            requester="user@example.com",
            purpose="Test",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service
        )

        retrieved = export_service.get_export(package.export_id)
        assert retrieved is not None
        assert retrieved.export_id == package.export_id

    def test_get_nonexistent_export(self, export_service):
        """Test retrieving non-existent export."""
        result = export_service.get_export("nonexistent_id")
        assert result is None

    def test_list_exports(self, export_service, mock_risk_service):
        """Test listing exports."""
        # Create multiple exports
        for i in range(3):
            request = export_service.create_export_request(
                requester=f"user{i}@example.com",
                purpose=f"Test {i}",
                scope=ExportScope.RISK_ONLY,
                format=ExportFormat.JSON
            )
            export_service.generate_export(
                request=request,
                risk_service=mock_risk_service
            )

        exports = export_service.list_exports()
        assert len(exports) == 3

    def test_list_exports_by_requester(self, export_service, mock_risk_service):
        """Test filtering exports by requester."""
        # Create exports for different requesters
        request1 = export_service.create_export_request(
            requester="alice@example.com",
            purpose="Test 1",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON
        )
        export_service.generate_export(request=request1, risk_service=mock_risk_service)

        request2 = export_service.create_export_request(
            requester="bob@example.com",
            purpose="Test 2",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON
        )
        export_service.generate_export(request=request2, risk_service=mock_risk_service)

        alice_exports = export_service.list_exports(requester="alice@example.com")
        assert len(alice_exports) == 1
        assert alice_exports[0].request.requester == "alice@example.com"

    def test_export_statistics(self, export_service, mock_risk_service):
        """Test getting overall export statistics."""
        # Create multiple exports
        for i in range(3):
            request = export_service.create_export_request(
                requester=f"user{i}@example.com",
                purpose=f"Test {i}",
                scope=ExportScope.RISK_ONLY,
                format=ExportFormat.JSON if i % 2 == 0 else ExportFormat.CSV
            )
            export_service.generate_export(
                request=request,
                risk_service=mock_risk_service
            )

        stats = export_service.get_export_statistics()
        assert stats["total_exports"] == 3
        assert stats["total_size_bytes"] > 0
        assert "format_breakdown" in stats
        assert stats["format_breakdown"]["json"] == 2
        assert stats["format_breakdown"]["csv"] == 1

    def test_export_record_count(
        self,
        export_service,
        mock_risk_service,
        mock_escalation_service,
        mock_override_service
    ):
        """Test record count in export."""
        request = export_service.create_export_request(
            requester="auditor@example.com",
            purpose="Record count test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service,
            escalation_service=mock_escalation_service,
            override_service=mock_override_service
        )

        assert package.record_count > 0
        # Should have 2 risks + 1 escalation + 1 override = 4 records minimum
        assert package.record_count >= 4

    def test_export_with_metadata(self, export_service, mock_risk_service):
        """Test export with custom metadata."""
        metadata = {
            "compliance_framework": "SOC2",
            "audit_period": "Q4 2023",
            "auditor_name": "John Doe"
        }

        request = export_service.create_export_request(
            requester="auditor@example.com",
            purpose="Compliance audit",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON,
            metadata=metadata
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service
        )

        assert package.metadata == metadata

    def test_export_compliance_data(self, export_service, mock_compliance_service):
        """Test exporting compliance mapping data."""
        request = export_service.create_export_request(
            requester="compliance@example.com",
            purpose="Compliance review",
            scope=ExportScope.COMPLIANCE_ONLY,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            compliance_service=mock_compliance_service
        )

        assert "compliance" in package.data
        compliance_data = package.data["compliance"]
        assert "statistics" in compliance_data
        assert "frameworks" in compliance_data
        assert "soc2" in compliance_data["frameworks"]
        assert "iso27001" in compliance_data["frameworks"]
        assert "gdpr" in compliance_data["frameworks"]

    def test_export_decision_log(self, export_service, mock_ledger):
        """Test exporting decision log."""
        request = export_service.create_export_request(
            requester="auditor@example.com",
            purpose="Decision log review",
            scope=ExportScope.DECISION_LOG_ONLY,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            ledger=mock_ledger
        )

        assert "decisions" in package.data
        assert len(package.data["decisions"]) > 0
        decision = package.data["decisions"][0]
        assert "entry_id" in decision
        assert "timestamp" in decision
        assert "entry_hash" in decision

    def test_multiple_export_formats_same_data(self, export_service, mock_risk_service):
        """Test generating same data in multiple formats."""
        formats = [ExportFormat.JSON, ExportFormat.CSV, ExportFormat.MARKDOWN, ExportFormat.HTML]
        packages = []

        for fmt in formats:
            request = export_service.create_export_request(
                requester="tester@example.com",
                purpose=f"Test {fmt.value} format",
                scope=ExportScope.RISK_ONLY,
                format=fmt
            )
            package = export_service.generate_export(
                request=request,
                risk_service=mock_risk_service
            )
            packages.append(package)

        # All should have data
        assert all(len(p.content) > 0 for p in packages)

        # Each format should be different
        assert len(set(p.content for p in packages)) == len(formats)

    def test_export_size_calculation(self, export_service, mock_risk_service):
        """Test export size is calculated correctly."""
        request = export_service.create_export_request(
            requester="admin@example.com",
            purpose="Size test",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            risk_service=mock_risk_service
        )

        assert package.size_bytes == len(package.content.encode())

    def test_export_empty_services(self, export_service):
        """Test export with no data in services."""
        from lexecon.risk.service import RiskService

        empty_risk_service = RiskService()

        request = export_service.create_export_request(
            requester="tester@example.com",
            purpose="Empty data test",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON
        )

        package = export_service.generate_export(
            request=request,
            risk_service=empty_risk_service
        )

        assert package is not None
        assert len(package.data.get("risks", [])) == 0
        assert package.data["statistics"]["total_risks"] == 0
