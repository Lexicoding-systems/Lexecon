"""This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/override.json
Schema ID: https://lexecon.io/schemas/override.json
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class OverrideType(str, Enum):
    """Override type enumeration."""

    EMERGENCY_BYPASS = "emergency_bypass"
    EXECUTIVE_OVERRIDE = "executive_override"
    TIME_LIMITED_EXCEPTION = "time_limited_exception"
    RISK_ACCEPTED = "risk_accepted"


class OriginalOutcome(str, Enum):
    """Original outcome enumeration."""

    DENIED = "denied"
    ESCALATED = "escalated"


class NewOutcome(str, Enum):
    """New outcome enumeration."""

    APPROVED = "approved"
    CONDITIONAL = "conditional"


class OverrideScope(BaseModel):
    """Override scope limitations."""

    is_one_time: Annotated[
        Optional[bool],
        Field(
            default=None,
            description="Whether override is one-time only",
        ),
    ]

    applies_to_policy: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Policy this override applies to",
        ),
    ]

    applies_to_actor: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Actor this override applies to",
        ),
    ]


class Override(BaseModel):
    """Lexecon Override

    Authorized exception to normal policy evaluation.
    """

    override_id: Annotated[
        str,
        Field(
            pattern=r"^ovr_dec_.+$",
            description="Unique override identifier",
        ),
    ]

    decision_id: Annotated[
        str,
        Field(
            description="Decision being overridden",
        ),
    ]

    override_type: Annotated[
        OverrideType,
        Field(
            description="Type of override",
        ),
    ]

    authorized_by: Annotated[
        str,
        Field(
            description="Actor ID who authorized override",
        ),
    ]

    justification: Annotated[
        str,
        Field(
            min_length=20,
            description="Required justification (min 20 chars)",
        ),
    ]

    timestamp: Annotated[
        datetime,
        Field(
            description="When override was granted",
        ),
    ]

    original_outcome: Annotated[
        Optional[OriginalOutcome],
        Field(
            default=None,
            description="What the decision was before override",
        ),
    ]

    new_outcome: Annotated[
        Optional[NewOutcome],
        Field(
            default=None,
            description="Outcome after override",
        ),
    ]

    expires_at: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="When time-limited override expires",
        ),
    ]

    scope: Annotated[
        Optional[OverrideScope],
        Field(
            default=None,
            description="Override scope limitations",
        ),
    ]

    review_required_by: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="When override must be reviewed",
        ),
    ]

    evidence_ids: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Supporting evidence for override",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
