"""
Compliance Mapping Service - Maps governance primitives to regulatory controls.

Provides regulatory alignment with:
- Framework-specific control mappings (SOC 2, ISO 27001, GDPR, etc.)
- Control satisfaction verification
- Gap analysis and compliance status tracking
- Evidence linkage to compliance requirements
- Automated compliance reporting
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid


class RegulatoryFramework(Enum):
    """Supported regulatory frameworks."""
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    NIST_CSF = "nist_csf"


class ControlStatus(Enum):
    """Compliance control status."""
    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    NON_COMPLIANT = "non_compliant"


class GovernancePrimitive(Enum):
    """Governance primitives from Phases 1-4."""
    RISK_ASSESSMENT = "risk_assessment"
    ESCALATION = "escalation"
    OVERRIDE = "override"
    EVIDENCE_ARTIFACT = "evidence_artifact"
    DECISION_LOG = "decision_log"


@dataclass
class ComplianceControl:
    """Represents a compliance control requirement."""
    control_id: str
    framework: RegulatoryFramework
    title: str
    description: str
    category: str
    required_evidence_types: List[str]
    mapped_primitives: List[GovernancePrimitive]
    status: ControlStatus
    last_verified: Optional[datetime] = None
    verification_notes: Optional[str] = None
    evidence_artifact_ids: List[str] = None

    def __post_init__(self):
        if self.evidence_artifact_ids is None:
            self.evidence_artifact_ids = []


@dataclass
class ControlMapping:
    """Maps a governance primitive to compliance controls."""
    mapping_id: str
    primitive_type: GovernancePrimitive
    primitive_id: str  # e.g., risk_id, escalation_id
    control_ids: List[str]
    framework: RegulatoryFramework
    mapped_at: datetime
    verification_status: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ComplianceReport:
    """Compliance status report for a framework."""
    report_id: str
    framework: RegulatoryFramework
    generated_at: datetime
    total_controls: int
    implemented_controls: int
    verified_controls: int
    non_compliant_controls: int
    compliance_percentage: float
    gaps: List[Dict[str, Any]]
    recommendations: List[str]


class ComplianceMappingService:
    """
    Service for mapping governance primitives to regulatory controls.

    Provides alignment between internal governance mechanisms and
    external compliance requirements.
    """

    # SOC 2 Trust Service Criteria mappings
    SOC2_CONTROLS = {
        "CC6.1": ComplianceControl(
            control_id="CC6.1",
            framework=RegulatoryFramework.SOC2,
            title="Logical and Physical Access Controls",
            description="The entity implements logical access security software, infrastructure, and architectures over protected information assets to protect them from security events.",
            category="Common Criteria",
            required_evidence_types=["decision_log", "override", "audit_trail"],
            mapped_primitives=[
                GovernancePrimitive.OVERRIDE,
                GovernancePrimitive.EVIDENCE_ARTIFACT,
                GovernancePrimitive.DECISION_LOG
            ],
            status=ControlStatus.NOT_IMPLEMENTED
        ),
        "CC7.2": ComplianceControl(
            control_id="CC7.2",
            framework=RegulatoryFramework.SOC2,
            title="Risk Assessment and Mitigation",
            description="The entity monitors system components and the operation of those components for anomalies that are indicative of malicious acts, natural disasters, and errors.",
            category="Common Criteria",
            required_evidence_types=["risk_assessment", "escalation", "evidence_artifact"],
            mapped_primitives=[
                GovernancePrimitive.RISK_ASSESSMENT,
                GovernancePrimitive.ESCALATION,
                GovernancePrimitive.EVIDENCE_ARTIFACT
            ],
            status=ControlStatus.NOT_IMPLEMENTED
        ),
        "CC9.1": ComplianceControl(
            control_id="CC9.1",
            framework=RegulatoryFramework.SOC2,
            title="Risk Mitigation Activities",
            description="The entity identifies, selects, and develops risk mitigation activities for risks arising from potential business disruptions.",
            category="Common Criteria",
            required_evidence_types=["risk_assessment", "escalation", "override"],
            mapped_primitives=[
                GovernancePrimitive.RISK_ASSESSMENT,
                GovernancePrimitive.ESCALATION,
                GovernancePrimitive.OVERRIDE
            ],
            status=ControlStatus.NOT_IMPLEMENTED
        ),
    }

    # ISO 27001 control mappings
    ISO27001_CONTROLS = {
        "A.9.2.1": ComplianceControl(
            control_id="A.9.2.1",
            framework=RegulatoryFramework.ISO27001,
            title="User Registration and De-registration",
            description="A formal user registration and de-registration process shall be implemented to enable assignment of access rights.",
            category="Access Control",
            required_evidence_types=["decision_log", "audit_trail"],
            mapped_primitives=[
                GovernancePrimitive.DECISION_LOG,
                GovernancePrimitive.EVIDENCE_ARTIFACT
            ],
            status=ControlStatus.NOT_IMPLEMENTED
        ),
        "A.12.6.1": ComplianceControl(
            control_id="A.12.6.1",
            framework=RegulatoryFramework.ISO27001,
            title="Management of Technical Vulnerabilities",
            description="Information about technical vulnerabilities of information systems being used shall be obtained in a timely fashion.",
            category="Operations Security",
            required_evidence_types=["risk_assessment", "evidence_artifact"],
            mapped_primitives=[
                GovernancePrimitive.RISK_ASSESSMENT,
                GovernancePrimitive.EVIDENCE_ARTIFACT
            ],
            status=ControlStatus.NOT_IMPLEMENTED
        ),
        "A.16.1.4": ComplianceControl(
            control_id="A.16.1.4",
            framework=RegulatoryFramework.ISO27001,
            title="Assessment of and Decision on Information Security Events",
            description="Information security events shall be assessed and it shall be decided if they are to be classified as information security incidents.",
            category="Incident Management",
            required_evidence_types=["risk_assessment", "escalation", "decision_log"],
            mapped_primitives=[
                GovernancePrimitive.RISK_ASSESSMENT,
                GovernancePrimitive.ESCALATION,
                GovernancePrimitive.DECISION_LOG
            ],
            status=ControlStatus.NOT_IMPLEMENTED
        ),
    }

    # GDPR Article mappings
    GDPR_CONTROLS = {
        "Art.32": ComplianceControl(
            control_id="Art.32",
            framework=RegulatoryFramework.GDPR,
            title="Security of Processing",
            description="Implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk.",
            category="Security",
            required_evidence_types=["risk_assessment", "evidence_artifact", "audit_trail"],
            mapped_primitives=[
                GovernancePrimitive.RISK_ASSESSMENT,
                GovernancePrimitive.EVIDENCE_ARTIFACT
            ],
            status=ControlStatus.NOT_IMPLEMENTED
        ),
        "Art.33": ComplianceControl(
            control_id="Art.33",
            framework=RegulatoryFramework.GDPR,
            title="Notification of Personal Data Breach",
            description="Notify supervisory authority of a personal data breach without undue delay.",
            category="Breach Notification",
            required_evidence_types=["escalation", "evidence_artifact", "decision_log"],
            mapped_primitives=[
                GovernancePrimitive.ESCALATION,
                GovernancePrimitive.EVIDENCE_ARTIFACT,
                GovernancePrimitive.DECISION_LOG
            ],
            status=ControlStatus.NOT_IMPLEMENTED
        ),
        "Art.35": ComplianceControl(
            control_id="Art.35",
            framework=RegulatoryFramework.GDPR,
            title="Data Protection Impact Assessment",
            description="Carry out a DPIA where processing is likely to result in high risk to rights and freedoms.",
            category="Risk Management",
            required_evidence_types=["risk_assessment", "evidence_artifact"],
            mapped_primitives=[
                GovernancePrimitive.RISK_ASSESSMENT,
                GovernancePrimitive.EVIDENCE_ARTIFACT
            ],
            status=ControlStatus.NOT_IMPLEMENTED
        ),
    }

    def __init__(self):
        """Initialize compliance mapping service."""
        self._mappings: Dict[str, ControlMapping] = {}
        self._control_registry: Dict[RegulatoryFramework, Dict[str, ComplianceControl]] = {
            RegulatoryFramework.SOC2: self.SOC2_CONTROLS.copy(),
            RegulatoryFramework.ISO27001: self.ISO27001_CONTROLS.copy(),
            RegulatoryFramework.GDPR: self.GDPR_CONTROLS.copy(),
        }
        self._reports: Dict[str, ComplianceReport] = {}

    def map_primitive_to_controls(
        self,
        primitive_type: GovernancePrimitive,
        primitive_id: str,
        framework: RegulatoryFramework,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ControlMapping:
        """
        Map a governance primitive to relevant compliance controls.

        Args:
            primitive_type: Type of governance primitive
            primitive_id: ID of the primitive instance
            framework: Target regulatory framework
            metadata: Optional additional mapping metadata

        Returns:
            ControlMapping object with identified controls
        """
        # Find all controls that map to this primitive type
        control_ids = []
        if framework in self._control_registry:
            for control_id, control in self._control_registry[framework].items():
                if primitive_type in control.mapped_primitives:
                    control_ids.append(control_id)

        mapping_id = f"map_{framework.value}_{uuid.uuid4().hex[:8]}"
        mapping = ControlMapping(
            mapping_id=mapping_id,
            primitive_type=primitive_type,
            primitive_id=primitive_id,
            control_ids=control_ids,
            framework=framework,
            mapped_at=datetime.now(timezone.utc),
            verification_status="pending",
            metadata=metadata
        )

        self._mappings[mapping_id] = mapping
        return mapping

    def link_evidence_to_control(
        self,
        control_id: str,
        framework: RegulatoryFramework,
        evidence_artifact_id: str
    ) -> bool:
        """
        Link an evidence artifact to a compliance control.

        Args:
            control_id: Compliance control ID
            framework: Regulatory framework
            evidence_artifact_id: Evidence artifact ID

        Returns:
            True if linked successfully
        """
        if framework not in self._control_registry:
            return False

        control = self._control_registry[framework].get(control_id)
        if not control:
            return False

        if evidence_artifact_id not in control.evidence_artifact_ids:
            control.evidence_artifact_ids.append(evidence_artifact_id)

        return True

    def verify_control(
        self,
        control_id: str,
        framework: RegulatoryFramework,
        notes: Optional[str] = None
    ) -> bool:
        """
        Mark a control as verified.

        Args:
            control_id: Compliance control ID
            framework: Regulatory framework
            notes: Optional verification notes

        Returns:
            True if verification successful
        """
        if framework not in self._control_registry:
            return False

        control = self._control_registry[framework].get(control_id)
        if not control:
            return False

        control.status = ControlStatus.VERIFIED
        control.last_verified = datetime.now(timezone.utc)
        control.verification_notes = notes

        return True

    def get_control_status(
        self,
        control_id: str,
        framework: RegulatoryFramework
    ) -> Optional[ComplianceControl]:
        """
        Get the current status of a compliance control.

        Args:
            control_id: Compliance control ID
            framework: Regulatory framework

        Returns:
            ComplianceControl object or None
        """
        if framework not in self._control_registry:
            return None

        return self._control_registry[framework].get(control_id)

    def list_controls(
        self,
        framework: RegulatoryFramework,
        status: Optional[ControlStatus] = None,
        category: Optional[str] = None
    ) -> List[ComplianceControl]:
        """
        List compliance controls with optional filtering.

        Args:
            framework: Regulatory framework
            status: Optional filter by status
            category: Optional filter by category

        Returns:
            List of ComplianceControl objects
        """
        if framework not in self._control_registry:
            return []

        controls = list(self._control_registry[framework].values())

        if status:
            controls = [c for c in controls if c.status == status]

        if category:
            controls = [c for c in controls if c.category == category]

        return controls

    def analyze_gaps(
        self,
        framework: RegulatoryFramework
    ) -> List[Dict[str, Any]]:
        """
        Analyze compliance gaps for a framework.

        Args:
            framework: Regulatory framework

        Returns:
            List of gap analysis results
        """
        if framework not in self._control_registry:
            return []

        gaps = []
        for control_id, control in self._control_registry[framework].items():
            if control.status in [ControlStatus.NOT_IMPLEMENTED, ControlStatus.NON_COMPLIANT]:
                gaps.append({
                    "control_id": control_id,
                    "title": control.title,
                    "category": control.category,
                    "status": control.status.value,
                    "required_evidence_types": control.required_evidence_types,
                    "mapped_primitives": [p.value for p in control.mapped_primitives],
                    "severity": "high" if control.status == ControlStatus.NON_COMPLIANT else "medium"
                })

        return gaps

    def generate_compliance_report(
        self,
        framework: RegulatoryFramework
    ) -> ComplianceReport:
        """
        Generate comprehensive compliance report for a framework.

        Args:
            framework: Regulatory framework

        Returns:
            ComplianceReport with status and recommendations
        """
        if framework not in self._control_registry:
            raise ValueError(f"Framework {framework.value} not supported")

        controls = list(self._control_registry[framework].values())
        total = len(controls)
        implemented = len([c for c in controls if c.status == ControlStatus.IMPLEMENTED])
        verified = len([c for c in controls if c.status == ControlStatus.VERIFIED])
        non_compliant = len([c for c in controls if c.status == ControlStatus.NON_COMPLIANT])

        compliance_percentage = ((implemented + verified) / total * 100) if total > 0 else 0

        gaps = self.analyze_gaps(framework)

        recommendations = []
        if non_compliant > 0:
            recommendations.append(f"Address {non_compliant} non-compliant controls immediately")
        if compliance_percentage < 80:
            recommendations.append(f"Increase compliance coverage from {compliance_percentage:.1f}% to at least 80%")
        if verified < implemented:
            recommendations.append(f"Verify {implemented - verified} implemented controls")

        report_id = f"rpt_{framework.value}_{uuid.uuid4().hex[:8]}"
        report = ComplianceReport(
            report_id=report_id,
            framework=framework,
            generated_at=datetime.now(timezone.utc),
            total_controls=total,
            implemented_controls=implemented,
            verified_controls=verified,
            non_compliant_controls=non_compliant,
            compliance_percentage=compliance_percentage,
            gaps=gaps,
            recommendations=recommendations
        )

        self._reports[report_id] = report
        return report

    def get_framework_coverage(
        self,
        framework: RegulatoryFramework
    ) -> Dict[str, Any]:
        """
        Get coverage statistics for a framework.

        Args:
            framework: Regulatory framework

        Returns:
            Dictionary with coverage statistics
        """
        if framework not in self._control_registry:
            return {}

        controls = list(self._control_registry[framework].values())
        total = len(controls)

        status_counts = {}
        for status in ControlStatus:
            count = len([c for c in controls if c.status == status])
            status_counts[status.value] = count

        # Group by category
        categories = {}
        for control in controls:
            if control.category not in categories:
                categories[control.category] = {"total": 0, "verified": 0}
            categories[control.category]["total"] += 1
            if control.status == ControlStatus.VERIFIED:
                categories[control.category]["verified"] += 1

        return {
            "framework": framework.value,
            "total_controls": total,
            "status_breakdown": status_counts,
            "categories": categories,
            "overall_compliance": (status_counts.get("verified", 0) / total * 100) if total > 0 else 0
        }

    def get_primitive_mappings(
        self,
        primitive_id: str
    ) -> List[ControlMapping]:
        """
        Get all control mappings for a primitive.

        Args:
            primitive_id: Governance primitive ID

        Returns:
            List of ControlMapping objects
        """
        return [
            mapping for mapping in self._mappings.values()
            if mapping.primitive_id == primitive_id
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall compliance mapping statistics.

        Returns:
            Dictionary with statistics
        """
        total_mappings = len(self._mappings)
        frameworks_tracked = len(self._control_registry)

        total_controls = sum(
            len(controls) for controls in self._control_registry.values()
        )

        verified_controls = sum(
            len([c for c in controls.values() if c.status == ControlStatus.VERIFIED])
            for controls in self._control_registry.values()
        )

        return {
            "total_mappings": total_mappings,
            "frameworks_tracked": frameworks_tracked,
            "total_controls": total_controls,
            "verified_controls": verified_controls,
            "frameworks": list(self._control_registry.keys()),
            "overall_verification_rate": (verified_controls / total_controls * 100) if total_controls > 0 else 0
        }
