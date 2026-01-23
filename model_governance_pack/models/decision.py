"""This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/decision.json
Schema ID: https://lexecon.io/schemas/decision.json
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class DecisionOutcome(str, Enum):
    """Decision outcome enumeration."""

    APPROVED = "approved"
    DENIED = "denied"
    ESCALATED = "escalated"
    CONDITIONAL = "conditional"


class Decision(BaseModel):
    """Lexecon Decision

    Immutable record of a governance evaluation outcome.
    """

    decision_id: Annotated[
        str,
        Field(
            pattern=r"^dec_[A-Z0-9]{26}$",
            description="Unique decision identifier (ULID format)",
        ),
    ]

    request_id: Annotated[
        str,
        Field(
            description="Correlation ID linking to original request",
        ),
    ]

    actor_id: Annotated[
        str,
        Field(
            pattern=r"^act_[a-z_]+:.+$",
            description="Actor who requested the action",
        ),
    ]

    action_id: Annotated[
        str,
        Field(
            pattern=r"^axn_[a-z_]+:.+$",
            description="Action that was evaluated",
        ),
    ]

    outcome: Annotated[
        DecisionOutcome,
        Field(
            description="Decision outcome",
        ),
    ]

    timestamp: Annotated[
        datetime,
        Field(
            description="When decision was made (ISO 8601)",
        ),
    ]

    policy_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="Policies evaluated for this decision",
        ),
    ]

    resource_id: Annotated[
        Optional[str],
        Field(
            default=None,
            pattern=r"^res_[a-z_]+:.+$",
            description="Target resource of the action",
        ),
    ]

    reasoning: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Human-readable explanation of decision",
        ),
    ]

    risk_assessment: Annotated[
        Optional[str],
        Field(
            default=None,
            pattern=r"^rsk_dec_.+$",
            description="Reference to associated risk assessment",
        ),
    ]

    conditions: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Conditions attached to conditional approval",
        ),
    ]

    evidence_ids: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Evidence artifacts supporting this decision",
        ),
    ]

    context_snapshot: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Frozen context at decision time",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
