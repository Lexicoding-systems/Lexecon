"""Tests for evidence service."""

import pytest
from datetime import datetime, timedelta, timezone

from lexecon.evidence.service import (
    EvidenceService,
    EvidenceConfig,
    ArtifactBuilder,
    generate_artifact_id,
    compute_sha256,
)

# Import canonical governance models
try:
    from model_governance_pack.models import (
        EvidenceArtifact,
        ArtifactType,
        DigitalSignature,
    )

    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False
    pytestmark = pytest.mark.skip("Governance models not available")


class TestArtifactIdGeneration:
    """Tests for artifact ID generation."""

    def test_generate_artifact_id_format(self):
        """Test artifact ID format."""
        artifact_id = generate_artifact_id("risk")

        assert artifact_id.startswith("evd_risk_")
        assert len(artifact_id) == len("evd_risk_") + 8  # 8 hex chars

    def test_generate_artifact_id_uniqueness(self):
        """Test that artifact IDs are unique."""
        ids = {generate_artifact_id("risk") for _ in range(100)}
        assert len(ids) == 100  # All unique


class TestSHA256Computation:
    """Tests for SHA-256 hash computation."""

    def test_compute_sha256_from_string(self):
        """Test computing hash from string."""
        content = "Test content for hashing"
        hash_value = compute_sha256(content)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 hex
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_compute_sha256_from_bytes(self):
        """Test computing hash from bytes."""
        content = b"Test content for hashing"
        hash_value = compute_sha256(content)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_compute_sha256_deterministic(self):
        """Test that hash computation is deterministic."""
        content = "Same content"

        hash1 = compute_sha256(content)
        hash2 = compute_sha256(content)

        assert hash1 == hash2

    def test_compute_sha256_different_content(self):
        """Test that different content produces different hashes."""
        hash1 = compute_sha256("Content 1")
        hash2 = compute_sha256("Content 2")

        assert hash1 != hash2


class TestEvidenceConfig:
    """Tests for evidence configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = EvidenceConfig()

        assert len(config.DEFAULT_RETENTION_PERIODS) == 8  # All artifact types
        assert config.MAX_CONTENT_SIZE == 100 * 1024 * 1024  # 100 MB

    def test_retention_periods_defined(self):
        """Test that retention periods are defined for all types."""
        config = EvidenceConfig()

        for artifact_type in ArtifactType:
            assert artifact_type in config.DEFAULT_RETENTION_PERIODS

    def test_long_retention_for_critical_types(self):
        """Test that critical types have long retention."""
        config = EvidenceConfig()

        # Decision logs, attestations, etc. should be 7+ years
        assert config.DEFAULT_RETENTION_PERIODS[ArtifactType.DECISION_LOG] >= 2555
        assert config.DEFAULT_RETENTION_PERIODS[ArtifactType.ATTESTATION] >= 2555
        assert config.DEFAULT_RETENTION_PERIODS[ArtifactType.SIGNATURE] >= 3650


class TestEvidenceService:
    """Tests for evidence service."""

    @pytest.fixture
    def service(self):
        """Create an evidence service instance."""
        return EvidenceService()

    @pytest.fixture
    def sample_content(self):
        """Sample content for artifacts."""
        return "Sample evidence content for testing"

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service.config is not None
        assert service.enable_signatures is True

    def test_store_artifact_valid(self, service, sample_content):
        """Test storing a valid artifact."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
            related_decision_ids=["dec_01JQXYZ1234567890ABCDEFGH"],
        )

        # Validate against schema
        assert isinstance(artifact, EvidenceArtifact)
        assert artifact.artifact_id.startswith("evd_")
        assert artifact.artifact_type == ArtifactType.DECISION_LOG
        assert len(artifact.sha256_hash) == 64
        assert artifact.source == "test_service"
        assert artifact.is_immutable is True

    def test_store_artifact_generates_hash(self, service, sample_content):
        """Test that storing artifact generates SHA-256 hash."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
        )

        # Hash should match content
        expected_hash = compute_sha256(sample_content)
        assert artifact.sha256_hash == expected_hash

    def test_store_artifact_sets_retention(self, service, sample_content):
        """Test that retention deadline is set."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
        )

        # Should have retention set
        assert artifact.retention_until is not None
        assert artifact.retention_until > datetime.now(timezone.utc)

    def test_store_artifact_custom_retention(self, service, sample_content):
        """Test custom retention period."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
            retention_days=90,
        )

        # Check retention is ~90 days
        expected = datetime.now(timezone.utc) + timedelta(days=90)
        diff = abs((artifact.retention_until - expected).total_seconds())
        assert diff < 60  # Within 1 minute

    def test_store_artifact_too_large(self, service):
        """Test that oversized content is rejected."""
        # Create content larger than limit
        large_content = "x" * (service.config.MAX_CONTENT_SIZE + 1)

        with pytest.raises(ValueError, match="exceeds maximum"):
            service.store_artifact(
                artifact_type=ArtifactType.DECISION_LOG,
                content=large_content,
                source="test_service",
            )

    def test_store_artifact_with_metadata(self, service, sample_content):
        """Test storing artifact with metadata."""
        metadata = {"key1": "value1", "key2": 42}

        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
            metadata=metadata,
        )

        assert artifact.metadata == metadata

    def test_get_artifact(self, service, sample_content):
        """Test retrieving artifact by ID."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
        )

        retrieved = service.get_artifact(artifact.artifact_id)
        assert retrieved is not None
        assert retrieved.artifact_id == artifact.artifact_id

    def test_get_artifact_not_found(self, service):
        """Test retrieving non-existent artifact."""
        retrieved = service.get_artifact("evd_nonexistent_12345678")
        assert retrieved is None

    def test_verify_artifact_integrity_valid(self, service, sample_content):
        """Test verifying artifact integrity with matching content."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
        )

        # Verify with same content
        assert service.verify_artifact_integrity(artifact.artifact_id, sample_content) is True

    def test_verify_artifact_integrity_invalid(self, service, sample_content):
        """Test verifying artifact integrity with mismatched content."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
        )

        # Verify with different content
        assert service.verify_artifact_integrity(artifact.artifact_id, "different content") is False

    def test_verify_artifact_integrity_not_found(self, service, sample_content):
        """Test verifying non-existent artifact."""
        with pytest.raises(ValueError, match="not found"):
            service.verify_artifact_integrity("evd_nonexistent_12345678", sample_content)

    def test_get_artifacts_for_decision(self, service, sample_content):
        """Test getting all artifacts for a decision."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Store multiple artifacts
        artifact1 = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
            related_decision_ids=[decision_id],
        )

        artifact2 = service.store_artifact(
            artifact_type=ArtifactType.CONTEXT_CAPTURE,
            content="Additional context",
            source="test_service",
            related_decision_ids=[decision_id],
        )

        artifacts = service.get_artifacts_for_decision(decision_id)
        assert len(artifacts) == 2
        assert artifacts[0].artifact_id == artifact1.artifact_id
        assert artifacts[1].artifact_id == artifact2.artifact_id

    def test_get_artifacts_for_control(self, service, sample_content):
        """Test getting all artifacts for a compliance control."""
        control_id = "ctrl_soc2_001"

        service.store_artifact(
            artifact_type=ArtifactType.ATTESTATION,
            content=sample_content,
            source="test_service",
            related_control_ids=[control_id],
        )

        artifacts = service.get_artifacts_for_control(control_id)
        assert len(artifacts) == 1
        assert control_id in artifacts[0].related_control_ids

    def test_list_artifacts_no_filter(self, service, sample_content):
        """Test listing all artifacts."""
        # Store multiple artifacts
        for i in range(3):
            service.store_artifact(
                artifact_type=ArtifactType.DECISION_LOG,
                content=f"Content {i}",
                source="test_service",
            )

        artifacts = service.list_artifacts()
        assert len(artifacts) == 3

    def test_list_artifacts_by_type(self, service, sample_content):
        """Test filtering artifacts by type."""
        service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content="Decision log",
            source="test_service",
        )
        service.store_artifact(
            artifact_type=ArtifactType.ATTESTATION,
            content="Attestation",
            source="test_service",
        )

        decision_logs = service.list_artifacts(artifact_type=ArtifactType.DECISION_LOG)
        assert len(decision_logs) == 1
        assert decision_logs[0].artifact_type == ArtifactType.DECISION_LOG

    def test_list_artifacts_by_source(self, service, sample_content):
        """Test filtering artifacts by source."""
        service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content="Content",
            source="service_a",
        )
        service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content="Content",
            source="service_b",
        )

        artifacts = service.list_artifacts(source="service_a")
        assert len(artifacts) == 1
        assert artifacts[0].source == "service_a"

    def test_list_artifacts_by_time_range(self, service, sample_content):
        """Test filtering artifacts by time range."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc) + timedelta(hours=1)

        service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content="Content",
            source="test_service",
        )

        artifacts = service.list_artifacts(start_time=start_time, end_time=end_time)
        assert len(artifacts) >= 1

    def test_get_artifacts_needing_retention(self, service, sample_content):
        """Test getting artifacts approaching retention deadline."""
        # Create artifact with short retention
        service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content="Content",
            source="test_service",
            retention_days=10,  # Short retention
        )

        # Check for artifacts needing retention (within 30 days)
        needing_retention = service.get_artifacts_needing_retention(days_until_expiry=30)
        assert len(needing_retention) >= 1

    def test_export_artifact_lineage(self, service, sample_content):
        """Test exporting artifact lineage for a decision."""
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Store multiple artifacts
        service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content="Decision log",
            source="decision_service",
            related_decision_ids=[decision_id],
        )
        service.store_artifact(
            artifact_type=ArtifactType.CONTEXT_CAPTURE,
            content="Context",
            source="context_service",
            related_decision_ids=[decision_id],
        )

        lineage = service.export_artifact_lineage(decision_id)

        assert lineage["decision_id"] == decision_id
        assert lineage["artifact_count"] == 2
        assert len(lineage["artifacts"]) == 2
        assert all("sha256_hash" in a for a in lineage["artifacts"])
        assert all("is_immutable" in a for a in lineage["artifacts"])

    def test_sign_artifact(self, service, sample_content):
        """Test adding digital signature to artifact."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.ATTESTATION,
            content=sample_content,
            source="test_service",
        )

        # Sign artifact
        signed = service.sign_artifact(
            artifact_id=artifact.artifact_id,
            signer_id="act_human_user:signer",
            signature="base64_encoded_signature_here",
            algorithm="RSA-SHA256",
        )

        assert signed.digital_signature is not None
        assert signed.digital_signature.signer_id == "act_human_user:signer"
        assert signed.digital_signature.algorithm == "RSA-SHA256"
        assert signed.digital_signature.signed_at is not None

    def test_sign_artifact_already_signed(self, service, sample_content):
        """Test that artifact cannot be signed twice."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.ATTESTATION,
            content=sample_content,
            source="test_service",
        )

        # Sign once
        service.sign_artifact(
            artifact_id=artifact.artifact_id,
            signer_id="act_human_user:signer",
            signature="signature1",
        )

        # Try to sign again
        with pytest.raises(ValueError, match="already signed"):
            service.sign_artifact(
                artifact_id=artifact.artifact_id,
                signer_id="act_human_user:signer2",
                signature="signature2",
            )

    def test_sign_artifact_not_found(self, service):
        """Test signing non-existent artifact."""
        with pytest.raises(ValueError, match="not found"):
            service.sign_artifact(
                artifact_id="evd_nonexistent_12345678",
                signer_id="act_human_user:signer",
                signature="signature",
            )

    def test_sign_artifact_disabled(self, sample_content):
        """Test that signing can be disabled."""
        service = EvidenceService(enable_signatures=False)

        artifact = service.store_artifact(
            artifact_type=ArtifactType.ATTESTATION,
            content=sample_content,
            source="test_service",
        )

        with pytest.raises(ValueError, match="not enabled"):
            service.sign_artifact(
                artifact_id=artifact.artifact_id,
                signer_id="act_human_user:signer",
                signature="signature",
            )

    def test_get_statistics(self, service, sample_content):
        """Test getting service statistics."""
        # Store various artifacts
        service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content="Decision 1",
            source="test_service",
            related_decision_ids=["dec_001"],
        )
        service.store_artifact(
            artifact_type=ArtifactType.ATTESTATION,
            content="Attestation 1",
            source="test_service",
            related_control_ids=["ctrl_001"],
        )

        stats = service.get_statistics()

        assert stats["total_artifacts"] == 2
        assert stats["total_size_bytes"] > 0
        assert "decision_log" in stats["artifact_types"]
        assert "attestation" in stats["artifact_types"]
        assert stats["decisions_with_evidence"] == 1
        assert stats["controls_with_evidence"] == 1

    def test_artifact_immutability(self, service, sample_content):
        """Test that artifacts are immutable."""
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=sample_content,
            source="test_service",
        )

        # Artifact should be marked immutable
        assert artifact.is_immutable is True

        # Re-retrieve should have same hash
        retrieved = service.get_artifact(artifact.artifact_id)
        assert retrieved.sha256_hash == artifact.sha256_hash


class TestArtifactBuilder:
    """Tests for artifact builder helper."""

    @pytest.fixture
    def service(self):
        """Create an evidence service instance."""
        return EvidenceService()

    def test_builder_basic(self, service):
        """Test basic artifact builder usage."""
        artifact = (
            ArtifactBuilder(
                artifact_type=ArtifactType.DECISION_LOG,
                content="Test content",
                source="test_service",
            )
            .link_to_decision("dec_001")
            .with_content_type("application/json")
            .build(service)
        )

        assert artifact.artifact_type == ArtifactType.DECISION_LOG
        assert "dec_001" in artifact.related_decision_ids
        assert artifact.content_type == "application/json"

    def test_builder_multiple_links(self, service):
        """Test builder with multiple links."""
        artifact = (
            ArtifactBuilder(
                artifact_type=ArtifactType.ATTESTATION,
                content="Test",
                source="test_service",
            )
            .link_to_decision("dec_001")
            .link_to_decision("dec_002")
            .link_to_control("ctrl_001")
            .build(service)
        )

        assert len(artifact.related_decision_ids) == 2
        assert "dec_001" in artifact.related_decision_ids
        assert "dec_002" in artifact.related_decision_ids
        assert "ctrl_001" in artifact.related_control_ids

    def test_builder_with_metadata(self, service):
        """Test builder with metadata."""
        artifact = (
            ArtifactBuilder(
                artifact_type=ArtifactType.DECISION_LOG,
                content="Test",
                source="test_service",
            )
            .with_metadata("key1", "value1")
            .with_metadata("key2", 42)
            .build(service)
        )

        assert artifact.metadata["key1"] == "value1"
        assert artifact.metadata["key2"] == 42

    def test_builder_with_retention(self, service):
        """Test builder with retention."""
        artifact = (
            ArtifactBuilder(
                artifact_type=ArtifactType.DECISION_LOG,
                content="Test",
                source="test_service",
            )
            .with_retention(365)
            .build(service)
        )

        # Should have ~365 day retention
        expected = datetime.now(timezone.utc) + timedelta(days=365)
        diff = abs((artifact.retention_until - expected).total_seconds())
        assert diff < 60  # Within 1 minute


class TestIntegrationWorkflows:
    """Integration tests for complete evidence workflows."""

    def test_complete_evidence_workflow(self):
        """Test complete workflow from storage to verification."""
        service = EvidenceService()

        # 1. Store artifact
        content = "Important decision evidence"
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content=content,
            source="decision_service",
            related_decision_ids=["dec_01JQXYZ1234567890ABCDEFGH"],
            content_type="application/json",
            metadata={"action": "data_export", "actor": "user@example.com"},
        )

        # 2. Verify artifact created correctly
        assert artifact.artifact_id.startswith("evd_")
        assert artifact.is_immutable is True

        # 3. Verify integrity
        assert service.verify_artifact_integrity(artifact.artifact_id, content) is True

        # 4. Retrieve by decision
        artifacts = service.get_artifacts_for_decision("dec_01JQXYZ1234567890ABCDEFGH")
        assert len(artifacts) == 1

        # 5. Export lineage
        lineage = service.export_artifact_lineage("dec_01JQXYZ1234567890ABCDEFGH")
        assert lineage["artifact_count"] == 1

    def test_multi_artifact_lineage(self):
        """Test building complete artifact lineage for a decision."""
        service = EvidenceService()
        decision_id = "dec_01JQXYZ1234567890ABCDEFGH"

        # Store artifacts from different sources
        service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content="Decision record",
            source="decision_service",
            related_decision_ids=[decision_id],
        )

        service.store_artifact(
            artifact_type=ArtifactType.CONTEXT_CAPTURE,
            content="Decision context",
            source="context_service",
            related_decision_ids=[decision_id],
        )

        service.store_artifact(
            artifact_type=ArtifactType.ATTESTATION,
            content="Human attestation",
            source="override_service",
            related_decision_ids=[decision_id],
        )

        # Export complete lineage
        lineage = service.export_artifact_lineage(decision_id)

        assert lineage["artifact_count"] == 3
        assert len(set(a["artifact_type"] for a in lineage["artifacts"])) == 3
        assert all(a["is_immutable"] for a in lineage["artifacts"])

    def test_signed_artifact_workflow(self):
        """Test workflow with digital signatures."""
        service = EvidenceService(enable_signatures=True)

        # Store artifact
        artifact = service.store_artifact(
            artifact_type=ArtifactType.ATTESTATION,
            content="Critical attestation requiring signature",
            source="attestation_service",
        )

        # Sign artifact
        signed = service.sign_artifact(
            artifact_id=artifact.artifact_id,
            signer_id="act_human_user:executive_john",
            signature="mock_signature_base64",
            algorithm="RSA-SHA256",
        )

        # Verify signature present
        assert signed.digital_signature is not None
        assert signed.digital_signature.signer_id == "act_human_user:executive_john"

        # Statistics should reflect signed artifact
        stats = service.get_statistics()
        assert stats["signed_artifacts"] == 1


class TestAppendOnlyEvidenceStore:
    """Tests for AppendOnlyEvidenceStore wrapper."""

    def test_enable_on_already_wrapped_store(self):
        """Test enabling append-only mode when already wrapped with AppendOnlyStore."""
        from lexecon.evidence.append_only_store import AppendOnlyEvidenceStore, AppendOnlyStore

        # Create evidence service
        service = EvidenceService()

        # Create append-only wrapper with enabled=True (this wraps _artifacts)
        append_store = AppendOnlyEvidenceStore(service, enabled=True)
        assert append_store.enabled
        assert isinstance(service._artifacts, AppendOnlyStore)

        # Disable it
        append_store.disable()
        assert not append_store.enabled

        # Store an artifact while disabled
        artifact = service.store_artifact(
            artifact_type=ArtifactType.DECISION_LOG,
            content="Test artifact",
            source="test",
        )

        # Re-enable - this should call the else branch at line 193
        append_store.enable()
        assert append_store.enabled

        # Verify append-only enforcement works
        from lexecon.evidence.append_only_store import AppendOnlyViolationError
        with pytest.raises(AppendOnlyViolationError):
            service._artifacts[artifact.artifact_id] = artifact  # Try to update
