"""This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/action.json
Schema ID: https://lexecon.io/schemas/action.json
"""

from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class ActionCategory(str, Enum):
    """Action category enumeration."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    TRANSMIT = "transmit"
    DELETE = "delete"
    APPROVE = "approve"
    ESCALATE = "escalate"


class Action(BaseModel):
    """Lexecon Action

    Discrete, auditable operation that an actor may request to perform.
    """

    action_id: Annotated[
        str,
        Field(
            pattern=r"^axn_[a-z_]+:.+$",
            description="Unique action identifier",
        ),
    ]

    category: Annotated[
        ActionCategory,
        Field(
            description="Action category",
        ),
    ]

    operation: Annotated[
        str,
        Field(
            description="Specific operation name",
        ),
    ]

    description: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Human-readable description",
        ),
    ]

    risk_weight: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=1,
            le=10,
            description="Inherent risk weight (1-10)",
        ),
    ]

    is_reversible: Annotated[
        Optional[bool],
        Field(
            default=None,
            description="Whether action can be undone",
        ),
    ]

    requires_confirmation: Annotated[
        Optional[bool],
        Field(
            default=False,
            description="Requires explicit user confirmation",
        ),
    ]

    parameters_schema: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="JSON Schema for action parameters",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
