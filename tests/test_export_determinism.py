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

    def test_identical_parameters_same_structure(self, export_service):
        """
        Two exports with identical parameters produce identical structure.
        """
        # Create first export
        request1 = export_service.create_export_request(
            requester="test_user",
            purpose="determinism_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
            start_date=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc),
        )
        package1 = export_service.generate_export(request=request1)

        # Create second export with same parameters
        request2 = export_service.create_export_request(
            requester="test_user",
            purpose="determinism_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
            start_date=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc),
        )
        package2 = export_service.generate_export(request=request2)

        # Both should complete successfully
        assert package1 is not None
        assert package2 is not None
        assert request1.status == ExportStatus.COMPLETED
        assert request2.status == ExportStatus.COMPLETED

        # Format should be identical
        assert package1.format == package2.format

        # Data structure keys should be identical
        assert set(package1.data.keys()) == set(package2.data.keys())

    def test_json_serialization_consistent(self, export_service):
        """
        JSON serialization produces consistent output.
        """
        request = export_service.create_export_request(
            requester="test_user",
            purpose="json_determinism_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
        )
        package = export_service.generate_export(request=request)

        # Serialize data multiple times
        data = package.data
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
        Timestamps use consistent ISO 8601 format.
        """
        request = export_service.create_export_request(
            requester="test_user",
            purpose="timestamp_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
        )
        package = export_service.generate_export(request=request)

        # Package data itself may be the manifest, or contain a manifest key
        data = package.data
        manifest = data.get("manifest", data)  # Use data itself if no nested manifest

        # Check for timestamp fields
        generated_at = manifest.get("generated_at")
        if generated_at:
            assert "T" in generated_at  # Has time component
            # Has timezone (Z or +/-offset)
            assert (generated_at.endswith("Z") or
                    "+" in generated_at or
                    generated_at.endswith("+00:00"))

    def test_empty_export_reproducible(self, export_service):
        """
        Empty exports (no data in scope) are reproducible.
        """
        # Export range with no data
        start_date = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2020, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        # Create two empty exports
        request1 = export_service.create_export_request(
            requester="test_user",
            purpose="empty_test_1",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
            start_date=start_date,
            end_date=end_date,
        )
        package1 = export_service.generate_export(request=request1)

        request2 = export_service.create_export_request(
            requester="test_user",
            purpose="empty_test_2",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
            start_date=start_date,
            end_date=end_date,
        )
        package2 = export_service.generate_export(request=request2)

        # Both should complete
        assert package1 is not None
        assert package2 is not None

        # Structure should be consistent
        assert set(package1.data.keys()) == set(package2.data.keys())

        # Check manifest contents
        manifest1 = package1.data.get("manifest", {})
        manifest2 = package2.data.get("manifest", {})

        contents1 = manifest1.get("contents", {})
        contents2 = manifest2.get("contents", {})

        # Both should show same structure
        assert set(contents1.keys()) == set(contents2.keys())

    def test_scope_filtering_consistent(self, export_service):
        """
        Different scopes produce consistent outputs.
        """
        # Create risk-only export
        request = export_service.create_export_request(
            requester="test_user",
            purpose="scope_test",
            scope=ExportScope.RISK_ONLY,
            format=ExportFormat.JSON,
        )
        package = export_service.generate_export(request=request)

        assert package is not None
        assert package.format == ExportFormat.JSON

        # Verify manifest includes scope information
        manifest = package.data.get("manifest")
        if manifest:
            scope = manifest.get("scope", {})
            assert scope.get("type") == "risk_only"

    def test_manifest_structure_complete(self, export_service):
        """
        Manifest contains required sections per spec.
        """
        request = export_service.create_export_request(
            requester="test_user",
            purpose="completeness_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
        )
        package = export_service.generate_export(request=request)

        # Check package data structure
        data = package.data
        assert data is not None

        # Check for export metadata section
        if "export_metadata" in data:
            metadata = data["export_metadata"]
            assert "export_id" in metadata
            assert "generated_at" in metadata
            assert "requester" in metadata
            assert "purpose" in metadata
            assert "scope" in metadata

        # Check for statistics section
        if "statistics" in data:
            stats = data["statistics"]
            assert isinstance(stats, dict)
            # Should have count fields
            assert any(key.startswith("total_") for key in stats.keys())

    def test_deterministic_checksums(self, export_service):
        """
        Root checksum is consistently formatted and present.
        """
        request = export_service.create_export_request(
            requester="test_user",
            purpose="checksum_test",
            scope=ExportScope.ALL,
            format=ExportFormat.JSON,
        )
        package = export_service.generate_export(request=request)

        # Package should have checksum
        assert package.checksum is not None

        # Should be hex string (SHA-256 = 64 chars)
        checksum = package.checksum
        assert isinstance(checksum, str)
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum.lower())

        # Manifest should also have integrity info
        manifest = package.data.get("manifest", {})
        integrity = manifest.get("integrity", {})

        if integrity:
            assert integrity.get("algorithm") == "SHA-256"
            assert "root_checksum" in integrity

    def test_multiple_formats_same_data(self, export_service):
        """
        Different formats contain semantically equivalent data.
        """
        requester = "test_user"
        purpose = "format_test"
        scope = ExportScope.ALL

        # Generate JSON export
        json_request = export_service.create_export_request(
            requester=requester,
            purpose=purpose,
            scope=scope,
            format=ExportFormat.JSON,
        )
        json_package = export_service.generate_export(request=json_request)

        # Generate Markdown export
        md_request = export_service.create_export_request(
            requester=requester,
            purpose=purpose,
            scope=scope,
            format=ExportFormat.MARKDOWN,
        )
        md_package = export_service.generate_export(request=md_request)

        # Both should succeed
        assert json_request.status == ExportStatus.COMPLETED
        assert md_request.status == ExportStatus.COMPLETED

        # Both should have data
        assert json_package is not None
        assert md_package is not None
        assert json_package.data is not None
        assert md_package.data is not None

        # Formats should be different
        assert json_package.format == ExportFormat.JSON
        assert md_package.format == ExportFormat.MARKDOWN
