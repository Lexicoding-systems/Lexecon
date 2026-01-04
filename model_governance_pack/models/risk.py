"""
This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/risk.json
Schema ID: https://lexecon.io/schemas/risk.json
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskDimensions(BaseModel):
    """Risk scores by dimension."""

    security: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=0,
            le=100,
            description="Security risk score (0-100)",
        ),
    ]

    privacy: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=0,
            le=100,
            description="Privacy risk score (0-100)",
        ),
    ]

    compliance: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=0,
            le=100,
            description="Compliance risk score (0-100)",
        ),
    ]

    operational: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=0,
            le=100,
            description="Operational risk score (0-100)",
        ),
    ]

    reputational: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=0,
            le=100,
            description="Reputational risk score (0-100)",
        ),
    ]

    financial: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=0,
            le=100,
            description="Financial risk score (0-100)",
        ),
    ]


class RiskFactor(BaseModel):
    """Contributing risk factor."""

    name: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Factor name",
        ),
    ]

    weight: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Factor weight",
        ),
    ]

    value: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Factor value",
        ),
    ]


class Risk(BaseModel):
    """
    Lexecon Risk Assessment

    Quantified assessment of potential harm associated with an action.
    """

    risk_id: Annotated[
        str,
        Field(
            pattern=r"^rsk_dec_.+$",
            description="Unique risk assessment identifier",
        ),
    ]

    decision_id: Annotated[
        str,
        Field(
            description="Associated decision",
        ),
    ]

    overall_score: Annotated[
        int,
        Field(
            ge=1,
            le=100,
            description="Aggregate risk score (1-100)",
        ),
    ]

    timestamp: Annotated[
        datetime,
        Field(
            description="Assessment timestamp",
        ),
    ]

    risk_level: Annotated[
        Optional[RiskLevel],
        Field(
            default=None,
            description="Categorical risk level",
        ),
    ]

    dimensions: Annotated[
        Optional[RiskDimensions],
        Field(
            default=None,
            description="Risk scores by dimension",
        ),
    ]

    likelihood: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0,
            le=1,
            description="Probability of harm (0-1)",
        ),
    ]

    impact: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=1,
            le=5,
            description="Severity of potential harm (1-5)",
        ),
    ]

    factors: Annotated[
        Optional[list[RiskFactor]],
        Field(
            default=None,
            description="Contributing risk factors",
        ),
    ]

    mitigations_applied: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Mitigations factored into score",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
