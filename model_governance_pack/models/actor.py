"""
This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/actor.json
Schema ID: https://lexecon.io/schemas/actor.json
"""

from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class ActorType(str, Enum):
    """Actor type enumeration."""

    AI_AGENT = "ai_agent"
    HUMAN_USER = "human_user"
    SYSTEM_SERVICE = "system_service"
    ORGANIZATIONAL_ROLE = "organizational_role"
    EXTERNAL_PARTY = "external_party"


class Actor(BaseModel):
    """
    Lexecon Actor

    Entity capable of initiating or participating in governed actions.
    """

    actor_id: Annotated[
        str,
        Field(
            pattern=r"^act_[a-z_]+:.+$",
            description="Unique actor identifier",
        ),
    ]

    actor_type: Annotated[
        ActorType,
        Field(
            description="Classification of actor",
        ),
    ]

    name: Annotated[
        str,
        Field(
            description="Display name",
        ),
    ]

    description: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Actor description",
        ),
    ]

    parent_actor_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Hierarchical parent (for delegation)",
        ),
    ]

    roles: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Assigned roles",
        ),
    ]

    trust_level: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=0,
            le=100,
            description="Trust score (0-100)",
        ),
    ]

    is_active: Annotated[
        Optional[bool],
        Field(
            default=True,
            description="Whether actor is currently active",
        ),
    ]

    attributes: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Type-specific attributes",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
