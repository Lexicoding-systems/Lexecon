"""This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/resource.json
Schema ID: https://lexecon.io/schemas/resource.json
"""

from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class ResourceClassification(str, Enum):
    """Resource classification level enumeration."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    CRITICAL = "critical"


class ResourceType(str, Enum):
    """Resource type enumeration."""

    DATA = "data"
    SYSTEM = "system"
    CAPABILITY = "capability"
    API = "api"
    FILE = "file"
    DATABASE = "database"
    SERVICE = "service"


class Resource(BaseModel):
    """Lexecon Resource

    Data, system, or capability that is the target of an action.
    """

    resource_id: Annotated[
        str,
        Field(
            pattern=r"^res_[a-z_]+:.+$",
            description="Unique resource identifier",
        ),
    ]

    classification: Annotated[
        ResourceClassification,
        Field(
            description="Data classification level",
        ),
    ]

    name: Annotated[
        str,
        Field(
            description="Resource name",
        ),
    ]

    resource_type: Annotated[
        Optional[ResourceType],
        Field(
            default=None,
            description="Type of resource",
        ),
    ]

    description: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Resource description",
        ),
    ]

    owner_actor_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Actor who owns this resource",
        ),
    ]

    compliance_tags: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Compliance-relevant tags (pii, phi, financial)",
        ),
    ]

    retention_days: Annotated[
        Optional[int],
        Field(
            default=None,
            description="Data retention period in days",
        ),
    ]

    is_encrypted: Annotated[
        Optional[bool],
        Field(
            default=None,
            description="Whether resource is encrypted at rest",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
