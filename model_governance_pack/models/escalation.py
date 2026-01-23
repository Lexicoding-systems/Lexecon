"""This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/escalation.json
Schema ID: https://lexecon.io/schemas/escalation.json
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class EscalationTrigger(str, Enum):
    """Escalation trigger enumeration."""

    RISK_THRESHOLD = "risk_threshold"
    POLICY_CONFLICT = "policy_conflict"
    EXPLICIT_RULE = "explicit_rule"
    ACTOR_REQUEST = "actor_request"
    ANOMALY_DETECTED = "anomaly_detected"


class EscalationStatus(str, Enum):
    """Escalation status enumeration."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class EscalationPriority(str, Enum):
    """Escalation priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionOutcome(str, Enum):
    """Resolution outcome enumeration."""

    APPROVED = "approved"
    DENIED = "denied"
    DEFERRED = "deferred"


class Resolution(BaseModel):
    """Resolution details."""

    outcome: Annotated[
        Optional[ResolutionOutcome],
        Field(
            default=None,
            description="Resolution outcome",
        ),
    ]

    resolved_by: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Actor who resolved",
        ),
    ]

    notes: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Resolution notes",
        ),
    ]


class Escalation(BaseModel):
    """Lexecon Escalation

    Routing of a governance decision to a higher authority.
    """

    escalation_id: Annotated[
        str,
        Field(
            pattern=r"^esc_dec_.+$",
            description="Unique escalation identifier",
        ),
    ]

    decision_id: Annotated[
        str,
        Field(
            description="Decision that triggered escalation",
        ),
    ]

    trigger: Annotated[
        EscalationTrigger,
        Field(
            description="What triggered the escalation",
        ),
    ]

    escalated_to: Annotated[
        list[str],
        Field(
            min_length=1,
            description="Actor IDs to review",
        ),
    ]

    status: Annotated[
        EscalationStatus,
        Field(
            description="Escalation status",
        ),
    ]

    created_at: Annotated[
        datetime,
        Field(
            description="When escalation was created",
        ),
    ]

    priority: Annotated[
        Optional[EscalationPriority],
        Field(
            default=None,
            description="Escalation priority",
        ),
    ]

    sla_deadline: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="When response is required",
        ),
    ]

    acknowledged_at: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="When escalation was acknowledged",
        ),
    ]

    acknowledged_by: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Actor who acknowledged",
        ),
    ]

    resolved_at: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="When escalation was resolved",
        ),
    ]

    resolution: Annotated[
        Optional[Resolution],
        Field(
            default=None,
            description="Resolution details",
        ),
    ]

    context_summary: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Summary for reviewer",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
