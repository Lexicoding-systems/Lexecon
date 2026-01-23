"""This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/evidence_artifact.json
Schema ID: https://lexecon.io/schemas/evidence_artifact.json
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import AnyUrl, BaseModel, Field


class ArtifactType(str, Enum):
    """Artifact type enumeration."""

    DECISION_LOG = "decision_log"
    POLICY_SNAPSHOT = "policy_snapshot"
    CONTEXT_CAPTURE = "context_capture"
    SCREENSHOT = "screenshot"
    ATTESTATION = "attestation"
    SIGNATURE = "signature"
    AUDIT_TRAIL = "audit_trail"
    EXTERNAL_REPORT = "external_report"


class DigitalSignature(BaseModel):
    """Digital signature details."""

    algorithm: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Signature algorithm",
        ),
    ]

    signature: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Signature value",
        ),
    ]

    signer_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Signer identifier",
        ),
    ]

    signed_at: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="When signature was created",
        ),
    ]


class EvidenceArtifact(BaseModel):
    """Lexecon Evidence Artifact

    Immutable record supporting audit defensibility.
    """

    artifact_id: Annotated[
        str,
        Field(
            pattern=r"^evd_[a-z]+_[a-f0-9]{8}$",
            description="Unique artifact identifier",
        ),
    ]

    artifact_type: Annotated[
        ArtifactType,
        Field(
            description="Type of evidence",
        ),
    ]

    sha256_hash: Annotated[
        str,
        Field(
            pattern=r"^[a-f0-9]{64}$",
            description="SHA-256 hash of content",
        ),
    ]

    created_at: Annotated[
        datetime,
        Field(
            description="When artifact was created",
        ),
    ]

    source: Annotated[
        str,
        Field(
            description="System/process that created artifact",
        ),
    ]

    content_type: Annotated[
        Optional[str],
        Field(
            default=None,
            description="MIME type of content",
        ),
    ]

    size_bytes: Annotated[
        Optional[int],
        Field(
            default=None,
            description="Content size in bytes",
        ),
    ]

    storage_uri: Annotated[
        Optional[AnyUrl],
        Field(
            default=None,
            description="Where artifact is stored",
        ),
    ]

    related_decision_ids: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Decisions this evidence supports",
        ),
    ]

    related_control_ids: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Compliance controls this satisfies",
        ),
    ]

    digital_signature: Annotated[
        Optional[DigitalSignature],
        Field(
            default=None,
            description="Optional digital signature",
        ),
    ]

    retention_until: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="Retention deadline",
        ),
    ]

    is_immutable: Annotated[
        Optional[bool],
        Field(
            default=True,
            description="Whether artifact can be modified",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
