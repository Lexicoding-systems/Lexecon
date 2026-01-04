"""
This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/policy.json
Schema ID: https://lexecon.io/schemas/policy.json
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class PolicyMode(str, Enum):
    """Policy evaluation mode enumeration."""

    PERMISSIVE = "permissive"
    STRICT = "strict"
    PARANOID = "paranoid"


class TermType(str, Enum):
    """Term type enumeration."""

    ACTOR = "actor"
    ACTION = "action"
    RESOURCE = "resource"
    DATA_CLASS = "data_class"


class RelationType(str, Enum):
    """Relation type enumeration."""

    PERMITS = "permits"
    FORBIDS = "forbids"
    REQUIRES = "requires"


class Term(BaseModel):
    """
    Policy term definition.

    Defined terms (actors, actions, resources).
    """

    id: Annotated[
        str,
        Field(
            description="Term identifier",
        ),
    ]

    type: Annotated[
        TermType,
        Field(
            description="Term type",
        ),
    ]

    name: Annotated[
        str,
        Field(
            description="Term name",
        ),
    ]

    description: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Term description",
        ),
    ]

    attributes: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Term attributes",
        ),
    ]


class Relation(BaseModel):
    """
    Policy relation definition.

    Permission/prohibition rules.
    """

    type: Annotated[
        RelationType,
        Field(
            description="Relation type",
        ),
    ]

    subject: Annotated[
        str,
        Field(
            description="Subject of the relation",
        ),
    ]

    action: Annotated[
        str,
        Field(
            description="Action in the relation",
        ),
    ]

    object: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Object of the relation",
        ),
    ]

    conditions: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Conditions for the relation",
        ),
    ]

    justification: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Justification for the relation",
        ),
    ]


class Constraint(BaseModel):
    """
    Policy constraint definition.

    Conditional constraints.
    """

    name: Annotated[
        str,
        Field(
            description="Constraint name",
        ),
    ]

    condition: Annotated[
        str,
        Field(
            description="Constraint condition",
        ),
    ]

    action: Annotated[
        str,
        Field(
            description="Action to take when condition is met",
        ),
    ]

    justification: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Justification for the constraint",
        ),
    ]


class Policy(BaseModel):
    """
    Lexecon Policy

    Declarative specification of permitted, forbidden, and conditionally-allowed behaviors.
    """

    policy_id: Annotated[
        str,
        Field(
            pattern=r"^pol_[a-z0-9_]+_v[0-9]+$",
            description="Unique policy identifier",
        ),
    ]

    name: Annotated[
        str,
        Field(
            min_length=3,
            max_length=128,
            description="Human-readable policy name",
        ),
    ]

    version: Annotated[
        str,
        Field(
            pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$",
            description="Semantic version",
        ),
    ]

    mode: Annotated[
        PolicyMode,
        Field(
            description="Policy evaluation mode",
        ),
    ]

    terms: Annotated[
        list[Term],
        Field(
            description="Defined terms (actors, actions, resources)",
        ),
    ]

    relations: Annotated[
        list[Relation],
        Field(
            description="Permission/prohibition rules",
        ),
    ]

    description: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Policy description and purpose",
        ),
    ]

    compliance_frameworks: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Associated compliance frameworks",
        ),
    ]

    constraints: Annotated[
        Optional[list[Constraint]],
        Field(
            default=None,
            description="Conditional constraints",
        ),
    ]

    effective_from: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="When policy becomes active",
        ),
    ]

    effective_until: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="When policy expires",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
