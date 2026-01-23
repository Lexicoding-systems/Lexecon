"""This model is a derived runtime binding of the canonical governance JSON schema.
The JSON schema remains the authoritative source of truth.
This file exists solely to enforce contract correctness at runtime.

Schema source: /model_governance_pack/schemas/compliance_control.json
Schema ID: https://lexecon.io/schemas/compliance_control.json
"""

from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class ComplianceFramework(str, Enum):
    """Compliance framework enumeration."""

    SOC2 = "soc2"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    NIST_CSF = "nist_csf"
    FEDRAMP = "fedramp"
    CCPA = "ccpa"


class ComplianceControl(BaseModel):
    """Lexecon Compliance Control

    Governance requirement derived from regulatory frameworks.
    """

    control_id: Annotated[
        str,
        Field(
            pattern=r"^ctl_[a-z0-9_]+:.+$",
            description="Unique control identifier",
        ),
    ]

    framework: Annotated[
        ComplianceFramework,
        Field(
            description="Compliance framework",
        ),
    ]

    control_ref: Annotated[
        str,
        Field(
            description="Framework-specific control reference (e.g., CC6.1)",
        ),
    ]

    name: Annotated[
        str,
        Field(
            description="Control name",
        ),
    ]

    description: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Control requirement description",
        ),
    ]

    category: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Control category within framework",
        ),
    ]

    policy_mappings: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Policy IDs that implement this control",
        ),
    ]

    evidence_requirements: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Required evidence types for audit",
        ),
    ]

    test_procedure: Annotated[
        Optional[str],
        Field(
            default=None,
            description="How to test control effectiveness",
        ),
    ]

    is_active: Annotated[
        Optional[bool],
        Field(
            default=True,
            description="Whether control is currently enforced",
        ),
    ]

    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(
            default=None,
            description="Extensible metadata",
        ),
    ]
