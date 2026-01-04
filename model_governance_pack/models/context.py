"""
This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/context.json
Schema ID: https://lexecon.io/schemas/context.json
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class DeploymentEnvironment(str, Enum):
    """Deployment environment enumeration."""

    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"


class Environment(BaseModel):
    """Environment metadata."""

    deployment: Annotated[
        Optional[DeploymentEnvironment],
        Field(
            default=None,
            description="Deployment environment",
        ),
    ]

    region: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Region",
        ),
    ]

    network_zone: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Network zone",
        ),
    ]


class Temporal(BaseModel):
    """Temporal context."""

    is_business_hours: Annotated[
        Optional[bool],
        Field(
            default=None,
            description="Whether within business hours",
        ),
    ]

    day_of_week: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Day of week",
        ),
    ]

    timezone: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Timezone",
        ),
    ]


class Behavioral(BaseModel):
    """Behavioral signals."""

    request_rate: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Request rate",
        ),
    ]

    anomaly_score: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Anomaly score",
        ),
    ]

    session_action_count: Annotated[
        Optional[int],
        Field(
            default=None,
            description="Session action count",
        ),
    ]


class Context(BaseModel):
    """
    Lexecon Context

    Situational metadata accompanying a governance request.
    """

    context_id: Annotated[
        str,
        Field(
            pattern=r"^ctx_.+$",
            description="Unique context identifier",
        ),
    ]

    session_id: Annotated[
        str,
        Field(
            description="Session this context belongs to",
        ),
    ]

    timestamp: Annotated[
        datetime,
        Field(
            description="Context capture time",
        ),
    ]

    user_intent: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Stated user intent",
        ),
    ]

    environment: Annotated[
        Optional[Environment],
        Field(
            default=None,
            description="Environment metadata",
        ),
    ]

    temporal: Annotated[
        Optional[Temporal],
        Field(
            default=None,
            description="Temporal context",
        ),
    ]

    behavioral: Annotated[
        Optional[Behavioral],
        Field(
            default=None,
            description="Behavioral signals",
        ),
    ]

    prior_decisions: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Recent decision IDs in this session",
        ),
    ]

    custom: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Custom context attributes",
        ),
    ]
