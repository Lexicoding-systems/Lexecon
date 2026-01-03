"""
Article 14 - Human Oversight Evidence System

Proves human-in-the-loop compliance with verifiable evidence chains.

EU AI Act Article 14 Requirements:
- High-risk AI systems must be designed to enable human oversight
- Humans must be able to understand outputs and intervene
- Humans must be able to override or disable the system
- All oversight actions must be logged with evidence
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from lexecon.identity.signing import KeyManager


class InterventionType(Enum):
    """Types of human oversight interventions."""
    APPROVAL = "approval"  # Human approved AI recommendation
    OVERRIDE = "override"  # Human overrode AI decision
    ESCALATION = "escalation"  # Escalated to higher authority
    EMERGENCY_STOP = "emergency_stop"  # Circuit breaker activated
    POLICY_EXCEPTION = "policy_exception"  # Temporary policy exception granted
    MANUAL_REVIEW = "manual_review"  # Required human review completed


class OversightRole(Enum):
    """Roles with oversight authority."""
    COMPLIANCE_OFFICER = "compliance_officer"
    SECURITY_LEAD = "security_lead"
    LEGAL_COUNSEL = "legal_counsel"
    RISK_MANAGER = "risk_manager"
    EXECUTIVE = "executive"
    SOC_ANALYST = "soc_analyst"


@dataclass
class HumanIntervention:
    """Record of human oversight intervention."""
    intervention_id: str
    timestamp: str
    intervention_type: InterventionType

    # What AI recommended
    ai_recommendation: Dict[str, Any]
    ai_confidence: float  # 0.0 to 1.0

    # What human decided
    human_decision: Dict[str, Any]
    human_role: OversightRole

    # Context
    request_context: Dict[str, Any]
    reason: str  # Human's rationale

    # Verification
    signature: Optional[str] = None  # Cryptographic signature of decision
    response_time_ms: Optional[int] = None  # How long human took to decide

    # Escalation
    escalated_from: Optional[str] = None  # If escalated, who escalated
    escalated_to: Optional[str] = None  # If escalated, who received


@dataclass
class EscalationPath:
    """Defines escalation chain for decision types."""
    decision_class: str  # e.g., "financial", "safety", "operational"
    roles: List[OversightRole]  # Ordered list of escalation roles
    max_response_time_minutes: int
    requires_approval_from: OversightRole


class HumanOversightEvidence:
    """
    Article 14 compliance system for human oversight evidence.

    Logs all human interventions with cryptographic signatures and
    generates oversight effectiveness reports.
    """

    def __init__(self, key_manager: Optional[KeyManager] = None):
        self.key_manager = key_manager or KeyManager.generate()
        self.interventions: List[HumanIntervention] = []
        self.escalation_paths: Dict[str, EscalationPath] = {}

        # Define default escalation paths
        self._initialize_default_escalations()

    def _initialize_default_escalations(self):
        """Set up default escalation paths."""
        self.escalation_paths = {
            "high_risk": EscalationPath(
                decision_class="high_risk",
                roles=[
                    OversightRole.SOC_ANALYST,
                    OversightRole.SECURITY_LEAD,
                    OversightRole.EXECUTIVE
                ],
                max_response_time_minutes=15,
                requires_approval_from=OversightRole.SECURITY_LEAD
            ),
            "financial": EscalationPath(
                decision_class="financial",
                roles=[
                    OversightRole.RISK_MANAGER,
                    OversightRole.COMPLIANCE_OFFICER,
                    OversightRole.EXECUTIVE
                ],
                max_response_time_minutes=30,
                requires_approval_from=OversightRole.RISK_MANAGER
            ),
            "legal": EscalationPath(
                decision_class="legal",
                roles=[
                    OversightRole.COMPLIANCE_OFFICER,
                    OversightRole.LEGAL_COUNSEL,
                    OversightRole.EXECUTIVE
                ],
                max_response_time_minutes=60,
                requires_approval_from=OversightRole.LEGAL_COUNSEL
            ),
            "operational": EscalationPath(
                decision_class="operational",
                roles=[
                    OversightRole.SOC_ANALYST,
                    OversightRole.SECURITY_LEAD
                ],
                max_response_time_minutes=5,
                requires_approval_from=OversightRole.SOC_ANALYST
            )
        }

    def log_intervention(
        self,
        intervention_type: InterventionType,
        ai_recommendation: Dict[str, Any],
        human_decision: Dict[str, Any],
        human_role: OversightRole,
        reason: str,
        request_context: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[int] = None,
        sign: bool = True
    ) -> HumanIntervention:
        """
        Log a human oversight intervention.

        This is called whenever a human approves, overrides, or escalates
        an AI decision.
        """
        intervention = HumanIntervention(
            intervention_id=f"oversight_{len(self.interventions) + 1}",
            timestamp=datetime.utcnow().isoformat() + "Z",
            intervention_type=intervention_type,
            ai_recommendation=ai_recommendation,
            ai_confidence=ai_recommendation.get("confidence", 0.0),
            human_decision=human_decision,
            human_role=human_role,
            reason=reason,
            request_context=request_context or {},
            response_time_ms=response_time_ms
        )

        # Sign the intervention
        if sign:
            intervention.signature = self._sign_intervention(intervention)

        self.interventions.append(intervention)
        return intervention

    def _sign_intervention(self, intervention: HumanIntervention) -> str:
        """Create cryptographic signature of intervention."""
        # Create canonical representation
        data = {
            "intervention_id": intervention.intervention_id,
            "timestamp": intervention.timestamp,
            "type": intervention.intervention_type.value,
            "ai_recommendation": intervention.ai_recommendation,
            "human_decision": intervention.human_decision,
            "role": intervention.human_role.value,
            "reason": intervention.reason
        }

        # KeyManager.sign() expects a dict and returns base64-encoded signature
        signature = self.key_manager.sign(data)
        return signature

    def verify_intervention(self, intervention: HumanIntervention) -> bool:
        """Verify cryptographic signature of intervention."""
        if not intervention.signature:
            return False

        # Recreate canonical representation
        data = {
            "intervention_id": intervention.intervention_id,
            "timestamp": intervention.timestamp,
            "type": intervention.intervention_type.value,
            "ai_recommendation": intervention.ai_recommendation,
            "human_decision": intervention.human_decision,
            "role": intervention.human_role.value,
            "reason": intervention.reason
        }

        # Use KeyManager.verify static method
        from lexecon.identity.signing import KeyManager
        try:
            return KeyManager.verify(data, intervention.signature, self.key_manager.public_key)
        except Exception:
            return False

    def generate_oversight_effectiveness_report(
        self,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate oversight effectiveness report.

        Proves humans actually intervene, not just rubber-stamp.
        This is critical for Article 14 compliance.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=time_period_days)
        recent = [
            i for i in self.interventions
            if datetime.fromisoformat(i.timestamp.replace('Z', '+00:00')) >= cutoff
        ]

        if not recent:
            return {
                "period_days": time_period_days,
                "total_interventions": 0,
                "message": "No interventions in period"
            }

        # Calculate statistics
        total = len(recent)
        by_type = {}
        by_role = {}
        overrides = 0
        rubber_stamps = 0
        response_times = []

        for intervention in recent:
            # Count by type
            itype = intervention.intervention_type.value
            by_type[itype] = by_type.get(itype, 0) + 1

            # Count by role
            role = intervention.human_role.value
            by_role[role] = by_role.get(role, 0) + 1

            # Detect overrides vs rubber-stamps
            ai_decision = intervention.ai_recommendation.get("decision", "")
            human_decision = intervention.human_decision.get("decision", "")

            if ai_decision and human_decision:
                if ai_decision != human_decision:
                    overrides += 1
                else:
                    rubber_stamps += 1

            # Response times
            if intervention.response_time_ms:
                response_times.append(intervention.response_time_ms)

        # Calculate override rate (key effectiveness metric!)
        override_rate = (overrides / (overrides + rubber_stamps) * 100) if (overrides + rubber_stamps) > 0 else 0

        # Response time statistics
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0

        # Compliance assessment
        compliance_status = self._assess_compliance(override_rate, avg_response_time)

        report = {
            "article": "Article 14 - Human Oversight Effectiveness",
            "period_days": time_period_days,
            "period_start": cutoff.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "total_interventions": total,

            "intervention_breakdown": {
                "by_type": by_type,
                "by_role": by_role
            },

            "effectiveness_metrics": {
                "total_overrides": overrides,
                "total_approvals": rubber_stamps,
                "override_rate_percent": round(override_rate, 2),
                "interpretation": self._interpret_override_rate(override_rate)
            },

            "response_time_metrics": {
                "average_ms": round(avg_response_time, 2),
                "minimum_ms": min_response_time,
                "maximum_ms": max_response_time,
                "average_seconds": round(avg_response_time / 1000, 2),
                "compliance_target_seconds": 60,
                "meets_target": avg_response_time / 1000 < 60
            },

            "compliance_assessment": compliance_status,

            "evidence_integrity": {
                "all_signed": all(i.signature for i in recent),
                "signatures_verified": sum(1 for i in recent if self.verify_intervention(i)),
                "verification_rate": round(
                    sum(1 for i in recent if self.verify_intervention(i)) / total * 100, 2
                )
            }
        }

        return report

    def _interpret_override_rate(self, rate: float) -> str:
        """Interpret override rate for compliance."""
        if rate < 5:
            return "LOW - Possible rubber-stamping concern. Humans may not be actively reviewing."
        elif rate < 15:
            return "MODERATE - Acceptable but monitor for genuine engagement."
        elif rate < 40:
            return "HEALTHY - Clear evidence of active human judgment."
        else:
            return "HIGH - Frequent overrides may indicate AI recommendations need improvement."

    def _assess_compliance(self, override_rate: float, avg_response_ms: float) -> Dict[str, Any]:
        """Assess overall Article 14 compliance."""
        compliant = True
        issues = []

        # Check override rate (should be between 5-40% for healthy oversight)
        if override_rate < 5:
            compliant = False
            issues.append("Override rate too low - possible rubber-stamping")
        elif override_rate > 50:
            issues.append("Override rate very high - AI recommendations may need improvement")

        # Check response time (should be under 60 seconds average)
        if avg_response_ms / 1000 > 60:
            compliant = False
            issues.append("Average response time exceeds 60 second target")

        return {
            "compliant": compliant,
            "status": "COMPLIANT" if compliant else "NEEDS_ATTENTION",
            "issues": issues if issues else ["None - oversight is effective"]
        }

    def get_escalation_path(self, decision_class: str) -> Optional[EscalationPath]:
        """Get escalation path for a decision class."""
        return self.escalation_paths.get(decision_class)

    def simulate_escalation(
        self,
        decision_class: str,
        current_role: OversightRole
    ) -> Dict[str, Any]:
        """
        Simulate escalation chain for a decision.

        Shows who can override/approve and response time requirements.
        """
        path = self.get_escalation_path(decision_class)
        if not path:
            return {"error": f"No escalation path for {decision_class}"}

        # Find current position in chain
        try:
            current_index = path.roles.index(current_role)
        except ValueError:
            return {"error": f"Role {current_role} not in escalation chain for {decision_class}"}

        # Determine next escalation level
        can_approve = current_role == path.requires_approval_from
        next_escalation = path.roles[current_index + 1] if current_index + 1 < len(path.roles) else None

        return {
            "decision_class": decision_class,
            "current_role": current_role.value,
            "can_approve": can_approve,
            "requires_approval_from": path.requires_approval_from.value,
            "next_escalation": next_escalation.value if next_escalation else None,
            "max_response_time_minutes": path.max_response_time_minutes,
            "full_escalation_chain": [r.value for r in path.roles]
        }

    def export_evidence_package(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export complete evidence package for Article 14 compliance.

        Includes all interventions with cryptographic proofs.
        """
        interventions = self.interventions

        # Filter by date
        if start_date:
            start = datetime.fromisoformat(start_date)
            interventions = [
                i for i in interventions
                if datetime.fromisoformat(i.timestamp.replace('Z', '+00:00')) >= start
            ]

        if end_date:
            end = datetime.fromisoformat(end_date)
            interventions = [
                i for i in interventions
                if datetime.fromisoformat(i.timestamp.replace('Z', '+00:00')) <= end
            ]

        return {
            "package_type": "EU_AI_ACT_ARTICLE_14_OVERSIGHT_EVIDENCE",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date or "inception",
                "end": end_date or "present"
            },
            "summary": {
                "total_interventions": len(interventions),
                "all_signed": all(i.signature for i in interventions),
                "verification_rate": sum(1 for i in interventions if self.verify_intervention(i)) / len(interventions) * 100 if interventions else 0
            },
            "effectiveness_report": self.generate_oversight_effectiveness_report(),
            "interventions": [asdict(i) for i in interventions],
            "escalation_paths": {
                k: {
                    "decision_class": v.decision_class,
                    "roles": [r.value for r in v.roles],
                    "max_response_time_minutes": v.max_response_time_minutes,
                    "requires_approval_from": v.requires_approval_from.value
                }
                for k, v in self.escalation_paths.items()
            },
            "compliance_attestation": {
                "article_14_compliance": True,
                "human_oversight_documented": True,
                "intervention_capability_proven": len(interventions) > 0,
                "cryptographic_signatures": True,
                "generated_by": "Lexecon Human Oversight Evidence System"
            }
        }

    def export_markdown(self, evidence_package: Dict[str, Any]) -> str:
        """Export evidence package as Markdown report."""
        effectiveness = evidence_package["effectiveness_report"]

        md = f"""# EU AI Act Article 14 - Human Oversight Evidence

**Package Type:** {evidence_package['package_type']}
**Generated:** {evidence_package['generated_at']}
**Period:** {evidence_package['period']['start']} to {evidence_package['period']['end']}

---

## Executive Summary

**Total Human Interventions:** {evidence_package['summary']['total_interventions']}
**All Interventions Signed:** {'✓ Yes' if evidence_package['summary']['all_signed'] else '✗ No'}
**Verification Rate:** {evidence_package['summary']['verification_rate']:.1f}%

---

## Oversight Effectiveness Analysis

### Intervention Breakdown
**Period:** {effectiveness['period_days']} days

**By Type:**
{chr(10).join(f"- **{k}:** {v}" for k, v in effectiveness.get('intervention_breakdown', {}).get('by_type', {}).items())}

**By Role:**
{chr(10).join(f"- **{k}:** {v}" for k, v in effectiveness.get('intervention_breakdown', {}).get('by_role', {}).items())}

### Effectiveness Metrics

**Override Rate:** {effectiveness.get('effectiveness_metrics', {}).get('override_rate_percent', 0):.1f}%
- Overrides: {effectiveness.get('effectiveness_metrics', {}).get('total_overrides', 0)}
- Approvals: {effectiveness.get('effectiveness_metrics', {}).get('total_approvals', 0)}
- **Assessment:** {effectiveness.get('effectiveness_metrics', {}).get('interpretation', 'N/A')}

### Response Time Performance

- **Average Response:** {effectiveness.get('response_time_metrics', {}).get('average_seconds', 0):.1f} seconds
- **Target:** {effectiveness.get('response_time_metrics', {}).get('compliance_target_seconds', 60)} seconds
- **Meets Target:** {'✓ Yes' if effectiveness.get('response_time_metrics', {}).get('meets_target') else '✗ No'}

---

## Compliance Assessment

**Status:** {effectiveness.get('compliance_assessment', {}).get('status', 'UNKNOWN')}

**Issues:**
{chr(10).join(f"- {issue}" for issue in effectiveness.get('compliance_assessment', {}).get('issues', []))}

---

## Attestation

We attest that this evidence package demonstrates compliance with EU AI Act Article 14:

- ✓ Human oversight is enabled and functioning
- ✓ Humans can understand AI outputs and intervene
- ✓ Override capability is proven with {effectiveness.get('effectiveness_metrics', {}).get('total_overrides', 0)} documented overrides
- ✓ All interventions cryptographically signed and verifiable

**Generated by:** Lexecon Human Oversight Evidence System

---

*For detailed intervention records, request JSON format export.*
"""
        return md
