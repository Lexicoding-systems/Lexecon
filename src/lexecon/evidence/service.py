"""Evidence Service - Centralized trust layer for governance artifacts.

Provides immutable evidence storage with:
- SHA-256 hash generation for integrity verification
- Schema validation for all artifacts
- Support for all artifact types
- Optional digital signatures
- Decision linkage and reverse lookup
- Exportable artifact lineage
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

# Import canonical governance models
try:
    from model_governance_pack.models import (
        ArtifactType,
        DigitalSignature,
        EvidenceArtifact,
    )

    GOVERNANCE_MODELS_AVAILABLE = True
except ImportError:
    GOVERNANCE_MODELS_AVAILABLE = False
    EvidenceArtifact = None
    ArtifactType = None
    DigitalSignature = None


def generate_artifact_id(artifact_type: str) -> str:
    """Generate an evidence artifact ID.

    Format: evd_<type>_<8_hex_chars>
    Removes underscores from type to match schema pattern.
    """
    # Remove underscores from artifact type to match pattern ^evd_[a-z]+_[a-f0-9]{8}$
    type_without_underscores = artifact_type.replace("_", "")
    hex_suffix = uuid.uuid4().hex[:8]
    return f"evd_{type_without_underscores}_{hex_suffix}"


def compute_sha256(content: Union[str, bytes]) -> str:
    """Compute SHA-256 hash of content.

    Args:
        content: String or bytes to hash

    Returns:
        Hex-encoded SHA-256 hash (64 chars)
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    return hashlib.sha256(content).hexdigest()


class EvidenceConfig:
    """Configuration for evidence service."""

    # Default retention periods by artifact type (in days)
    DEFAULT_RETENTION_PERIODS = {
        ArtifactType.DECISION_LOG: 2555,  # 7 years
        ArtifactType.POLICY_SNAPSHOT: 2555,  # 7 years
        ArtifactType.CONTEXT_CAPTURE: 365,  # 1 year
        ArtifactType.SCREENSHOT: 365,  # 1 year
        ArtifactType.ATTESTATION: 2555,  # 7 years
        ArtifactType.SIGNATURE: 3650,  # 10 years
        ArtifactType.AUDIT_TRAIL: 2555,  # 7 years
        ArtifactType.EXTERNAL_REPORT: 2555,  # 7 years
    }

    # Maximum content size (in bytes)
    MAX_CONTENT_SIZE = 100 * 1024 * 1024  # 100 MB


class EvidenceService:
    """Evidence artifact storage service.

    Centralized trust layer for storing immutable evidence
    artifacts with integrity guarantees and audit trail.
    """

    def __init__(
        self,
        config: Optional[EvidenceConfig] = None,
        enable_signatures: bool = True,
    ):
        """Initialize the evidence service.

        Args:
            config: Optional custom configuration
            enable_signatures: Whether to support digital signatures
        """
        if not GOVERNANCE_MODELS_AVAILABLE:
            raise RuntimeError(
                "Governance models not available. Install model_governance_pack.",
            )

        self.config = config or EvidenceConfig()
        self.enable_signatures = enable_signatures

        # In-memory storage (immutable records)
        self._artifacts: Dict[str, EvidenceArtifact] = {}
        self._decision_index: Dict[str, List[str]] = {}  # decision_id -> artifact_ids
        self._control_index: Dict[str, List[str]] = {}  # control_id -> artifact_ids
        self._type_index: Dict[ArtifactType, List[str]] = {}  # type -> artifact_ids

    def store_artifact(
        self,
        artifact_type: "ArtifactType",
        content: Union[str, bytes],
        source: str,
        related_decision_ids: Optional[List[str]] = None,
        related_control_ids: Optional[List[str]] = None,
        content_type: Optional[str] = None,
        storage_uri: Optional[str] = None,
        retention_days: Optional[int] = None,
        digital_signature: Optional["DigitalSignature"] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "EvidenceArtifact":
        """Store an evidence artifact.

        Validates via schema, generates SHA-256 hash, and creates
        immutable record with all linkages.

        Args:
            artifact_type: Type of evidence artifact
            content: Artifact content (string or bytes)
            source: System/process that created artifact
            related_decision_ids: Decision IDs this evidence supports
            related_control_ids: Compliance control IDs this satisfies
            content_type: MIME type of content
            storage_uri: Optional external storage location
            retention_days: Optional retention period (overrides default)
            digital_signature: Optional digital signature
            metadata: Optional extensible metadata

        Returns:
            EvidenceArtifact object validated against canonical schema

        Raises:
            ValueError: If validation fails or content too large
        """
        # Convert content to bytes for hashing
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content

        # Check content size
        if len(content_bytes) > self.config.MAX_CONTENT_SIZE:
            raise ValueError(
                f"Content size {len(content_bytes)} exceeds maximum {self.config.MAX_CONTENT_SIZE}",
            )

        # Generate SHA-256 hash
        sha256_hash = compute_sha256(content_bytes)

        # Generate artifact ID
        artifact_id = generate_artifact_id(artifact_type.value)

        # Calculate retention deadline
        retention_until = None
        if retention_days is None:
            retention_days = self.config.DEFAULT_RETENTION_PERIODS.get(artifact_type)

        if retention_days:
            retention_until = datetime.now(timezone.utc) + timedelta(days=retention_days)

        # Create artifact (validates against schema)
        artifact = EvidenceArtifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            sha256_hash=sha256_hash,
            created_at=datetime.now(timezone.utc),
            source=source,
            content_type=content_type,
            size_bytes=len(content_bytes),
            storage_uri=storage_uri,
            related_decision_ids=related_decision_ids or [],
            related_control_ids=related_control_ids or [],
            digital_signature=digital_signature,
            retention_until=retention_until,
            is_immutable=True,
            metadata=metadata,
        )

        # Store artifact (immutable)
        self._artifacts[artifact_id] = artifact

        # Update indexes for fast lookup
        self._index_artifact(artifact)

        return artifact

    def get_artifact(self, artifact_id: str) -> Optional["EvidenceArtifact"]:
        """Retrieve an artifact by ID.

        Returns immutable artifact record.
        """
        return self._artifacts.get(artifact_id)

    def verify_artifact_integrity(
        self,
        artifact_id: str,
        content: Union[str, bytes],
    ) -> bool:
        """Verify artifact integrity by recomputing hash.

        Args:
            artifact_id: Artifact ID to verify
            content: Content to verify against stored hash

        Returns:
            True if hash matches, False otherwise

        Raises:
            ValueError: If artifact not found
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")

        # Recompute hash
        computed_hash = compute_sha256(content)

        # Compare with stored hash
        return computed_hash == artifact.sha256_hash

    def get_artifacts_for_decision(self, decision_id: str) -> List["EvidenceArtifact"]:
        """Get all artifacts linked to a decision.

        Args:
            decision_id: Decision ID

        Returns:
            List of EvidenceArtifact objects in chronological order
        """
        artifact_ids = self._decision_index.get(decision_id, [])
        artifacts = [self._artifacts[aid] for aid in artifact_ids]

        # Sort by created_at (oldest first)
        artifacts.sort(key=lambda a: a.created_at)

        return artifacts

    def get_artifacts_for_control(self, control_id: str) -> List["EvidenceArtifact"]:
        """Get all artifacts linked to a compliance control.

        Args:
            control_id: Compliance control ID

        Returns:
            List of EvidenceArtifact objects
        """
        artifact_ids = self._control_index.get(control_id, [])
        artifacts = [self._artifacts[aid] for aid in artifact_ids]

        # Sort by created_at (oldest first)
        artifacts.sort(key=lambda a: a.created_at)

        return artifacts

    def list_artifacts(
        self,
        artifact_type: Optional["ArtifactType"] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List["EvidenceArtifact"]:
        """List artifacts with optional filtering.

        Args:
            artifact_type: Filter by artifact type
            source: Filter by source
            start_time: Filter artifacts created after this time
            end_time: Filter artifacts created before this time
            limit: Maximum number of results

        Returns:
            List of EvidenceArtifact objects
        """
        # Start with type-filtered or all artifacts
        if artifact_type:
            artifact_ids = self._type_index.get(artifact_type, [])
            artifacts = [self._artifacts[aid] for aid in artifact_ids]
        else:
            artifacts = list(self._artifacts.values())

        # Apply additional filters
        if source:
            artifacts = [a for a in artifacts if a.source == source]

        if start_time:
            artifacts = [a for a in artifacts if a.created_at >= start_time]

        if end_time:
            artifacts = [a for a in artifacts if a.created_at <= end_time]

        # Sort by created_at descending (most recent first)
        artifacts.sort(key=lambda a: a.created_at, reverse=True)

        return artifacts[:limit]

    def get_artifacts_needing_retention(
        self,
        days_until_expiry: int = 30,
    ) -> List["EvidenceArtifact"]:
        """Get artifacts approaching retention deadline.

        Args:
            days_until_expiry: Threshold in days

        Returns:
            List of artifacts approaching retention deadline
        """
        threshold = datetime.now(timezone.utc) + timedelta(days=days_until_expiry)
        artifacts = []

        for artifact in self._artifacts.values():
            if artifact.retention_until and artifact.retention_until <= threshold:
                artifacts.append(artifact)

        # Sort by retention deadline (most urgent first)
        artifacts.sort(key=lambda a: a.retention_until)

        return artifacts

    def export_artifact_lineage(
        self,
        decision_id: str,
    ) -> Dict[str, Any]:
        """Export complete artifact lineage for a decision.

        Provides audit-ready export with all evidence,
        hashes, and metadata for the decision.

        Args:
            decision_id: Decision ID to export lineage for

        Returns:
            Dictionary with complete artifact lineage
        """
        artifacts = self.get_artifacts_for_decision(decision_id)

        return {
            "decision_id": decision_id,
            "artifact_count": len(artifacts),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": [
                {
                    "artifact_id": a.artifact_id,
                    "artifact_type": a.artifact_type.value,
                    "sha256_hash": a.sha256_hash,
                    "created_at": a.created_at.isoformat(),
                    "source": a.source,
                    "size_bytes": a.size_bytes,
                    "is_immutable": a.is_immutable,
                    "has_signature": a.digital_signature is not None,
                    "retention_until": (
                        a.retention_until.isoformat() if a.retention_until else None
                    ),
                    "metadata": a.metadata,
                }
                for a in artifacts
            ],
        }


    def sign_artifact(
        self,
        artifact_id: str,
        signer_id: str,
        signature: str,
        algorithm: str = "RSA-SHA256",
    ) -> "EvidenceArtifact":
        """Add digital signature to an artifact.

        Creates new version of artifact with signature.
        Original artifact remains unchanged (immutability).

        Args:
            artifact_id: Artifact ID to sign
            signer_id: Actor ID of signer
            signature: Signature value (base64 encoded)
            algorithm: Signature algorithm

        Returns:
            New EvidenceArtifact with signature

        Raises:
            ValueError: If artifact not found or signatures not enabled
        """
        if not self.enable_signatures:
            raise ValueError("Digital signatures not enabled")

        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")

        if artifact.digital_signature:
            raise ValueError(f"Artifact {artifact_id} already signed")

        # Create digital signature
        digital_signature = DigitalSignature(
            algorithm=algorithm,
            signature=signature,
            signer_id=signer_id,
            signed_at=datetime.now(timezone.utc),
        )

        # Create new artifact with signature (immutability preserved)
        signed_artifact = artifact.model_copy(
            update={"digital_signature": digital_signature},
        )

        # Replace in storage (allowed because it's adding signature)
        self._artifacts[artifact_id] = signed_artifact

        return signed_artifact

    def get_statistics(self) -> Dict[str, Any]:
        """Get evidence service statistics.

        Returns:
            Dictionary with statistics
        """
        total_artifacts = len(self._artifacts)
        total_size = sum(a.size_bytes or 0 for a in self._artifacts.values())

        type_counts = {}
        for artifact_type in ArtifactType:
            count = len(self._type_index.get(artifact_type, []))
            if count > 0:
                type_counts[artifact_type.value] = count

        signed_count = sum(
            1 for a in self._artifacts.values() if a.digital_signature is not None
        )

        return {
            "total_artifacts": total_artifacts,
            "total_size_bytes": total_size,
            "artifact_types": type_counts,
            "signed_artifacts": signed_count,
            "decisions_with_evidence": len(self._decision_index),
            "controls_with_evidence": len(self._control_index),
        }

    def _index_artifact(self, artifact: "EvidenceArtifact") -> None:
        """Index artifact for fast lookup.

        Args:
            artifact: Artifact to index
        """
        # Index by decision IDs
        if artifact.related_decision_ids:
            for decision_id in artifact.related_decision_ids:
                if decision_id not in self._decision_index:
                    self._decision_index[decision_id] = []
                self._decision_index[decision_id].append(artifact.artifact_id)

        # Index by control IDs
        if artifact.related_control_ids:
            for control_id in artifact.related_control_ids:
                if control_id not in self._control_index:
                    self._control_index[control_id] = []
                self._control_index[control_id].append(artifact.artifact_id)

        # Index by type
        if artifact.artifact_type not in self._type_index:
            self._type_index[artifact.artifact_type] = []
        self._type_index[artifact.artifact_type].append(artifact.artifact_id)


class ArtifactBuilder:
    """Helper class for building evidence artifacts with fluent API."""

    def __init__(
        self,
        artifact_type: "ArtifactType",
        content: Union[str, bytes],
        source: str,
    ):
        """Initialize artifact builder.

        Args:
            artifact_type: Type of artifact
            content: Artifact content
            source: Source system/process
        """
        self.artifact_type = artifact_type
        self.content = content
        self.source = source
        self.related_decision_ids: List[str] = []
        self.related_control_ids: List[str] = []
        self.content_type: Optional[str] = None
        self.storage_uri: Optional[str] = None
        self.retention_days: Optional[int] = None
        self.digital_signature: Optional[DigitalSignature] = None
        self.metadata: Dict[str, Any] = {}

    def link_to_decision(self, decision_id: str) -> "ArtifactBuilder":
        """Link artifact to a decision."""
        self.related_decision_ids.append(decision_id)
        return self

    def link_to_control(self, control_id: str) -> "ArtifactBuilder":
        """Link artifact to a compliance control."""
        self.related_control_ids.append(control_id)
        return self

    def with_content_type(self, content_type: str) -> "ArtifactBuilder":
        """Set content type."""
        self.content_type = content_type
        return self

    def with_storage_uri(self, storage_uri: str) -> "ArtifactBuilder":
        """Set storage URI."""
        self.storage_uri = storage_uri
        return self

    def with_retention(self, days: int) -> "ArtifactBuilder":
        """Set retention period."""
        self.retention_days = days
        return self

    def with_metadata(self, key: str, value: Any) -> "ArtifactBuilder":
        """Add metadata."""
        self.metadata[key] = value
        return self

    def build(self, service: EvidenceService) -> "EvidenceArtifact":
        """Build and store the artifact.

        Args:
            service: EvidenceService to store in

        Returns:
            Created EvidenceArtifact
        """
        return service.store_artifact(
            artifact_type=self.artifact_type,
            content=self.content,
            source=self.source,
            related_decision_ids=self.related_decision_ids or None,
            related_control_ids=self.related_control_ids or None,
            content_type=self.content_type,
            storage_uri=self.storage_uri,
            retention_days=self.retention_days,
            digital_signature=self.digital_signature,
            metadata=self.metadata or None,
        )
