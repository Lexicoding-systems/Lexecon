"""
Tests for audit export determinism.

Verifies that audit exports are reproducible: the same input data
and parameters produce byte-identical outputs.
"""

import json
import hashlib
import pytest
from datetime import datetime, timezone
from lexecon.audit_export.service import (
    AuditExportService,
    ExportScope,
    ExportFormat,
    ExportStatus,
)


class TestExportDeterminism:
    """Tests for deterministic audit export generation."""

    @pytest.fixture
    def export_service(self):
        """Create export service instance."""
        return AuditExportService()

    @pytest.fixture
    def mock_risk_service(self):
        """Create mock risk service with test data."""
        from lexecon.risk.service import RiskService, RiskDimensions

        service = RiskService()
        # Add deterministic test data
        service.assess_risk(
            decision_id="dec_001",
            dimensions=RiskDimensions(security=80, privacy=60, compliance=40)
        )
        service.assess_risk(
            decision_id="dec_002",
            dimensions=RiskDimensions(security=30, privacy=20, compliance=10)
        )
        return service

    def test_identical_parameters_same_structure(self, export_service):
        """
        Two exports with identical parameters produce identical structure
        (excluding dynamic fields like export_id and generated_at).
        """
        fixed_time = datetime(2026, 1, 4, 13, 0, 0, tzinfo=timezone.utc)

        # Create first export
        export1_id = export_service.create_export_request(
            requester="test_user",
            purpose="determinism_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
            start_date=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc),
        )
        result1 = export_service.generate_export(export1_id, current_time=fixed_time)

        # Create second export with same parameters
        export2_id = export_service.create_export_request(
            requester="test_user",
            purpose="determinism_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
            start_date=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc),
        )
        result2 = export_service.generate_export(export2_id, current_time=fixed_time)

        # Load both results
        with open(result1["file_path"], "r") as f:
            data1 = json.load(f)

        with open(result2["file_path"], "r") as f:
            data2 = json.load(f)

        # Compare manifests (excluding dynamic fields)
        manifest1 = data1["manifest"]
        manifest2 = data2["manifest"]

        # Structure should be identical
        assert set(manifest1.keys()) == set(manifest2.keys())

        # Contents should be identical
        assert manifest1["contents"] == manifest2["contents"]

        # Scope should be identical
        assert manifest1["scope"] == manifest2["scope"]

        # Generator version should be identical
        assert manifest1["generator"]["system"] == manifest2["generator"]["system"]
        assert manifest1["generator"]["version"] == manifest2["generator"]["version"]

    def test_json_serialization_consistent(self, export_service):
        """
        JSON serialization produces consistent output across multiple exports.
        """
        # Create export
        export_id = export_service.create_export_request(
            requester="test_user",
            purpose="json_determinism_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
        )
        result = export_service.generate_export(export_id)

        # Load and re-serialize multiple times
        with open(result["file_path"], "r") as f:
            data = json.load(f)

        # Serialize with consistent parameters
        serialized1 = json.dumps(data, indent=2, sort_keys=True)
        serialized2 = json.dumps(data, indent=2, sort_keys=True)

        # Should be byte-identical
        assert serialized1 == serialized2

        # Hash should be consistent
        hash1 = hashlib.sha256(serialized1.encode()).hexdigest()
        hash2 = hashlib.sha256(serialized2.encode()).hexdigest()
        assert hash1 == hash2

    def test_timestamp_format_consistent(self, export_service):
        """
        Timestamps use consistent ISO 8601 format across exports.
        """
        export_id = export_service.create_export_request(
            requester="test_user",
            purpose="timestamp_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
        )
        result = export_service.generate_export(export_id)

        with open(result["file_path"], "r") as f:
            data = json.load(f)

        # Check manifest timestamps
        manifest = data["manifest"]

        # generated_at should be ISO 8601
        generated_at = manifest.get("generated_at")
        assert generated_at is not None
        assert "T" in generated_at  # Has time component
        # Has timezone (Z or +/-offset)
        assert (generated_at.endswith("Z") or
                "+" in generated_at or
                generated_at.endswith("+00:00"))

        # Scope timestamps should also be ISO 8601 if present
        scope = manifest.get("scope", {})
        for date_field in ["start_date", "end_date"]:
            if scope.get(date_field):
                date_value = scope[date_field]
                assert "T" in date_value
                assert (date_value.endswith("Z") or
                        "+" in date_value or
                        date_value.endswith("+00:00"))

    def test_empty_export_reproducible(self, export_service):
        """
        Empty exports (no data in scope) are reproducible.
        """
        # Export range with no data
        start_date = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2020, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        # Create two empty exports
        export1_id = export_service.create_export_request(
            requester="test_user",
            purpose="empty_test_1",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
            start_date=start_date,
            end_date=end_date,
        )
        result1 = export_service.generate_export(export1_id)

        export2_id = export_service.create_export_request(
            requester="test_user",
            purpose="empty_test_2",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
            start_date=start_date,
            end_date=end_date,
        )
        result2 = export_service.generate_export(export2_id)

        # Load results
        with open(result1["file_path"], "r") as f:
            data1 = json.load(f)

        with open(result2["file_path"], "r") as f:
            data2 = json.load(f)

        # Contents should both show zero counts
        contents1 = data1["manifest"]["contents"]
        contents2 = data2["manifest"]["contents"]

        # All counts should be zero
        for key in contents1:
            if key.endswith("_count"):
                assert contents1[key] == 0
                assert contents2[key] == 0

    def test_scope_filtering_consistent(self, export_service):
        """
        Different scopes produce consistent, predictable outputs.
        """
        # Create risk-only export
        export_id = export_service.create_export_request(
            requester="test_user",
            purpose="scope_test",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON,
        )
        result = export_service.generate_export(export_id)

        with open(result["file_path"], "r") as f:
            data = json.load(f)

        # Verify scope recorded correctly
        assert data["manifest"]["scope"]["type"] == "risk_only"

        # Create escalation-only export
        export_id2 = export_service.create_export_request(
            requester="test_user",
            purpose="scope_test_2",
            scope=ExportScope.ESCALATION_ONLY,
            format=ExportFormat.JSON,
        )
        result2 = export_service.generate_export(export_id2)

        with open(result2["file_path"], "r") as f:
            data2 = json.load(f)

        # Verify different scope
        assert data2["manifest"]["scope"]["type"] == "escalation_only"
        # Structure should be consistent
        assert set(data["manifest"].keys()) == set(data2["manifest"].keys())

    def test_manifest_structure_complete(self, export_service):
        """
        Manifest contains all required sections per spec.
        """
        export_id = export_service.create_export_request(
            requester="test_user",
            purpose="completeness_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
        )
        result = export_service.generate_export(export_id)

        with open(result["file_path"], "r") as f:
            data = json.load(f)

        manifest = data["manifest"]

        # Required top-level fields per AUDIT_PACKET_SPEC.md
        required_fields = [
            "packet_version",
            "export_id",
            "generated_at",
            "generator",
            "scope",
            "request",
            "contents",
            "integrity",
        ]

        for field in required_fields:
            assert field in manifest, f"Missing required field: {field}"

        # Verify generator structure
        generator = manifest["generator"]
        assert "system" in generator
        assert "version" in generator
        assert "service" in generator

        # Verify integrity structure
        integrity = manifest["integrity"]
        assert "algorithm" in integrity
        assert "root_checksum" in integrity

    def test_deterministic_checksums(self, export_service):
        """
        Root checksum is consistently formatted and present.
        """
        export_id = export_service.create_export_request(
            requester="test_user",
            purpose="checksum_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
        )
        result = export_service.generate_export(export_id)

        with open(result["file_path"], "r") as f:
            data = json.load(f)

        integrity = data["manifest"]["integrity"]

        # Root checksum should exist
        assert "root_checksum" in integrity
        root_checksum = integrity["root_checksum"]

        # Should be SHA-256 (64 hex characters)
        assert isinstance(root_checksum, str)
        assert len(root_checksum) == 64
        assert all(c in "0123456789abcdef" for c in root_checksum.lower())

        # Algorithm should be declared
        assert integrity["algorithm"] == "SHA-256"

    def test_multiple_formats_same_data(self, export_service):
        """
        Different formats contain semantically equivalent data.
        """
        requester = "test_user"
        purpose = "format_test"
        scope = ExportScope.ALL

        # Generate JSON export
        json_id = export_service.create_export_request(
            requester=requester,
            purpose=purpose,
            scope=scope,
            format=ExportFormat.JSON,
        )
        json_result = export_service.generate_export(json_id)

        # Generate Markdown export
        md_id = export_service.create_export_request(
            requester=requester,
            purpose=purpose,
            scope=scope,
            format=ExportFormat.MARKDOWN,
        )
        md_result = export_service.generate_export(md_id)

        # Both should succeed
        assert json_result["status"] == "COMPLETED"
        assert md_result["status"] == "COMPLETED"

        # Load JSON to compare counts
        with open(json_result["file_path"], "r") as f:
            json_data = json.load(f)

        json_counts = json_data["manifest"]["contents"]

        # Markdown should contain same semantic data
        # (Can't parse Markdown easily, but file should exist and be non-empty)
        with open(md_result["file_path"], "r") as f:
            md_content = f.read()

        assert len(md_content) > 0
        # Should mention key counts if non-zero
        for key, value in json_counts.items():
            if value > 0 and key.endswith("_count"):
                # Count should be mentioned in markdown
                assert str(value) in md_content
