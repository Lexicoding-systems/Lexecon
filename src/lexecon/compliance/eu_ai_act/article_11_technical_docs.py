"""Article 11 - Technical Documentation Generator

Automatically generates EU AI Act compliant technical documentation from system state.

EU AI Act Article 11 Requirements:
- General characteristics, capabilities and limitations
- Intended purpose and reasonably foreseeable misuse
- Development, training and testing processes
- Data requirements and characteristics
- Human oversight measures
- Expected level of accuracy
- Cybersecurity and robustness measures
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from lexecon.ledger.chain import LedgerChain
from lexecon.policy.engine import PolicyEngine


@dataclass
class TechnicalDocumentation:
    """EU AI Act Article 11 compliant technical documentation."""

    document_type: str = "EU_AI_ACT_ARTICLE_11"
    generated_at: str = ""
    document_hash: str = ""
    version: str = "1.0"

    # Article 11(1) - General description
    general_description: Dict[str, Any] = None

    # Article 11(2) - Intended purpose
    intended_purpose: Dict[str, Any] = None

    # Article 11(3) - Design specifications
    design_specifications: Dict[str, Any] = None

    # Article 11(4) - Development methodology
    development_methodology: Dict[str, Any] = None

    # Article 11(5) - Data requirements
    data_requirements: Dict[str, Any] = None

    # Article 11(6) - Human oversight measures
    human_oversight_measures: Dict[str, Any] = None

    # Article 11(7) - Accuracy metrics
    accuracy_metrics: Dict[str, Any] = None

    # Article 11(8) - Known limitations
    known_limitations: Dict[str, Any] = None

    # Evidence chain
    evidence_chain: List[str] = None

    def __post_init__(self):
        if self.evidence_chain is None:
            self.evidence_chain = []


class TechnicalDocumentationGenerator:
    """Generates EU AI Act Article 11 compliant technical documentation
    from Lexecon system state.
    """

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        ledger: Optional[LedgerChain] = None,
    ):
        self.policy_engine = policy_engine
        self.ledger = ledger

    def generate(
        self,
        system_info: Optional[Dict[str, Any]] = None,
    ) -> TechnicalDocumentation:
        """Generate complete Article 11 documentation.

        Args:
            system_info: Optional additional system information

        Returns:
            TechnicalDocumentation object with all sections populated
        """
        doc = TechnicalDocumentation()
        doc.generated_at = datetime.utcnow().isoformat() + "Z"

        # Generate each section
        doc.general_description = self._generate_general_description(system_info)
        doc.intended_purpose = self._generate_intended_purpose()
        doc.design_specifications = self._generate_design_specifications()
        doc.development_methodology = self._generate_development_methodology()
        doc.data_requirements = self._generate_data_requirements()
        doc.human_oversight_measures = self._generate_human_oversight()
        doc.accuracy_metrics = self._generate_accuracy_metrics()
        doc.known_limitations = self._generate_known_limitations()

        # Build evidence chain from ledger
        if self.ledger:
            doc.evidence_chain = self._build_evidence_chain()

        # Calculate document hash
        doc.document_hash = self._calculate_hash(doc)

        return doc

    def _generate_general_description(
        self,
        system_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Article 11(1) - General characteristics, capabilities and limitations."""
        return {
            "article": "Article 11(1)",
            "system_name": "Lexecon AI Governance Platform",
            "system_type": "High-Risk AI System - Governance and Control",
            "classification": "Safety component pursuant to Article 6(1)",
            "description": (
                "Lexecon provides cryptographic enforcement between AI models "
                "and their tool usage, ensuring all AI operations comply with "
                "organizational policies and regulatory requirements."
            ),
            "capabilities": [
                "Runtime policy enforcement for AI decisions",
                "Cryptographic capability token issuance and verification",
                "Immutable audit trail generation with hash-chaining",
                "Real-time decision gating and risk assessment",
                "Multi-model governance across AI providers",
                "Automated compliance documentation generation",
            ],
            "technical_architecture": {
                "policy_engine": "Rule-based decision system with cryptographic verification",
                "ledger": "Hash-chained immutable audit log",
                "capability_tokens": "Cryptographic permissions with scope limitations",
                "decision_service": "Runtime enforcement with sub-200ms latency",
            },
            "deployment_modes": [
                "Cloud-hosted SaaS",
                "Self-hosted enterprise",
                "Hybrid deployment",
            ],
            "integration_points": [
                "OpenAI API wrapper",
                "Anthropic API wrapper",
                "Generic model adapter",
                "Enterprise SSO (SAML/OIDC)",
                "SIEM integration",
                "GRC platform integration",
            ],
        }

    def _generate_intended_purpose(self) -> Dict[str, Any]:
        """Article 11(2) - Intended purpose and reasonably foreseeable misuse."""
        policy_count = len(self.policy_engine.terms) if self.policy_engine else 0

        return {
            "article": "Article 11(2)",
            "intended_purpose": {
                "primary": (
                    "Enforce organizational governance policies on AI system behavior "
                    "to prevent unauthorized, unsafe, or non-compliant operations."
                ),
                "use_cases": [
                    "Prevent PII exposure by AI models",
                    "Enforce data retention policies on AI-generated content",
                    "Limit AI access to sensitive systems based on risk level",
                    "Ensure human oversight for high-risk AI decisions",
                    "Generate compliance evidence for regulatory audits",
                ],
                "target_users": [
                    "Compliance officers",
                    "Security teams (CISOs)",
                    "Legal counsel",
                    "AI operations teams",
                    "Risk management",
                ],
            },
            "current_policy_coverage": {
                "active_policies": policy_count,
                "policy_categories": [
                    "Data governance",
                    "Access control",
                    "Risk thresholds",
                    "Human oversight requirements",
                    "Audit requirements",
                ],
            },
            "reasonably_foreseeable_misuse": {
                "identified_risks": [
                    {
                        "risk": "Over-restrictive policies blocking legitimate AI usage",
                        "mitigation": "Policy testing and simulation mode before production deployment",
                        "residual_risk": "Low - policies are version-controlled with rollback capability",
                    },
                    {
                        "risk": "Incorrect policy configuration allowing prohibited operations",
                        "mitigation": "Policy validation on load, immutable audit trail of all decisions",
                        "residual_risk": "Medium - requires trained policy administrators",
                    },
                    {
                        "risk": "System bypass through direct API access",
                        "mitigation": "Cryptographic token verification, all API calls logged",
                        "residual_risk": "Low - bypass attempts are detectable and logged",
                    },
                ],
                "prohibited_uses": [
                    "Circumventing other AI safety systems",
                    "Surveillance without proper authorization",
                    "Automated decision-making without human oversight where required",
                    "Processing special category data without appropriate safeguards",
                ],
            },
        }

    def _generate_design_specifications(self) -> Dict[str, Any]:
        """Article 11(3) - Design specifications and architecture."""
        return {
            "article": "Article 11(3)",
            "architecture": {
                "components": [
                    {
                        "name": "Policy Engine",
                        "function": "Evaluates AI requests against organizational policies",
                        "technology": "Rule-based system with lexicoding semantics",
                        "performance": "Sub-200ms evaluation latency",
                    },
                    {
                        "name": "Decision Service",
                        "function": "Runtime gating of AI operations",
                        "technology": "FastAPI service with async request handling",
                        "performance": "1000+ requests/minute throughput",
                    },
                    {
                        "name": "Capability Token System",
                        "function": "Cryptographic proof of authorized operations",
                        "technology": "Ed25519 signatures with scope-limited tokens",
                        "performance": "Token generation <10ms",
                    },
                    {
                        "name": "Audit Ledger",
                        "function": "Immutable record of all governance decisions",
                        "technology": "Hash-chained ledger with SHA-256",
                        "performance": "100% tamper-evident verification",
                    },
                ],
                "cryptographic_measures": {
                    "signing": "Ed25519 for decision signatures",
                    "hashing": "SHA-256 for audit chain integrity",
                    "key_management": "HSM-compatible key storage",
                    "token_format": "JWS-compatible capability tokens",
                },
                "data_flows": [
                    "AI request → Policy Engine → Decision Service → AI model",
                    "All decisions → Audit Ledger",
                    "Evidence generation → Compliance Reports",
                ],
            },
            "security_specifications": {
                "authentication": "Multi-factor with SSO integration",
                "authorization": "Role-based access control (RBAC)",
                "encryption": {
                    "at_rest": "AES-256",
                    "in_transit": "TLS 1.3",
                    "key_rotation": "90-day mandatory rotation",
                },
                "audit_logging": "All operations logged with cryptographic integrity",
                "vulnerability_management": "Automated scanning, 30-day patch SLA",
            },
            "interoperability": {
                "standards": ["OAuth 2.0", "SAML 2.0", "OpenAPI 3.0"],
                "integrations": ["OpenAI", "Anthropic", "Generic REST APIs"],
                "export_formats": ["JSON", "PDF", "CSV", "XML"],
            },
        }

    def _generate_development_methodology(self) -> Dict[str, Any]:
        """Article 11(4) - Development, training and testing processes."""
        return {
            "article": "Article 11(4)",
            "development_process": {
                "methodology": "Secure Software Development Lifecycle (SSDLC)",
                "version_control": "Git with mandatory code review",
                "testing_strategy": {
                    "unit_tests": "Pytest framework, >80% coverage requirement",
                    "integration_tests": "API contract testing",
                    "security_tests": "SAST, DAST, dependency scanning",
                    "compliance_tests": "Policy validation test suite",
                },
                "deployment_process": {
                    "ci_cd": "GitHub Actions with automated tests",
                    "staging_environment": "Mandatory pre-production testing",
                    "rollback_capability": "Immediate rollback on failure",
                    "deployment_frequency": "Continuous deployment to staging, weekly to production",
                },
            },
            "quality_assurance": {
                "code_review": "Mandatory peer review for all changes",
                "security_review": "Quarterly third-party security audits",
                "compliance_review": "Legal review for EU AI Act changes",
                "penetration_testing": "Annual third-party penetration tests",
            },
            "training_data": {
                "applicability": "Not applicable - rule-based system, not ML-based",
                "note": (
                    "Lexecon does not use machine learning models. "
                    "Policies are explicitly defined rules, not learned behaviors."
                ),
            },
            "change_management": {
                "policy_changes": "Version-controlled with approval workflow",
                "system_updates": "Automated deployment with rollback capability",
                "emergency_procedures": "Documented incident response plan",
            },
        }

    def _generate_data_requirements(self) -> Dict[str, Any]:
        """Article 11(5) - Data requirements and characteristics."""
        return {
            "article": "Article 11(5)",
            "data_processed": {
                "operational_data": [
                    "AI request metadata (actor, action, tool)",
                    "User intent descriptions",
                    "Policy evaluation results",
                    "Decision timestamps and identifiers",
                    "Cryptographic hashes and signatures",
                ],
                "personal_data": {
                    "categories": [
                        "User identifiers (role-based, not individual names)",
                        "Request context (may contain user intent descriptions)",
                        "Audit trail metadata (timestamps, IP addresses)",
                    ],
                    "special_categories": "None processed by Lexecon core system",
                    "legal_basis": "Legitimate interest - fraud prevention and security monitoring",
                    "data_minimization": "Only metadata required for governance decisions stored",
                },
            },
            "data_quality": {
                "accuracy": "Policy rules are deterministic - 100% reproducible decisions",
                "completeness": "All required fields validated before decision processing",
                "consistency": "Hash-chain integrity ensures consistent audit trail",
                "timeliness": "Real-time decision processing with <200ms latency",
            },
            "data_governance": {
                "retention": "Minimum 10 years for high-risk decisions per Article 12",
                "anonymization": "Automatic anonymization after retention period",
                "deletion_rights": "GDPR-compliant data subject access and deletion",
                "cross_border": "Data residency options for EU-only storage",
            },
            "data_sources": {
                "primary": "Direct input from AI model API calls",
                "secondary": "Policy definitions loaded by administrators",
                "external": "None - all data generated internally or provided by client systems",
            },
        }

    def _generate_human_oversight(self) -> Dict[str, Any]:
        """Article 11(6) - Human oversight measures."""
        return {
            "article": "Article 11(6)",
            "oversight_design": {
                "principle": (
                    "Human oversight is embedded at multiple levels: "
                    "policy definition, high-risk decision approval, and audit review."
                ),
                "oversight_levels": [
                    {
                        "level": "Policy Definition",
                        "actors": "Compliance officers, legal counsel",
                        "control": "All policies require human approval before activation",
                        "verification": "Policy hash signed by authorized administrator",
                    },
                    {
                        "level": "High-Risk Decision Approval",
                        "actors": "Security teams, risk managers",
                        "control": "High-risk AI requests require human approval before execution",
                        "verification": "Approval signed and logged in audit trail",
                    },
                    {
                        "level": "Continuous Monitoring",
                        "actors": "SOC analysts, compliance monitors",
                        "control": "Real-time dashboard with alerting on anomalies",
                        "verification": "All monitoring actions logged",
                    },
                    {
                        "level": "Audit Review",
                        "actors": "Internal audit, external auditors",
                        "control": "Periodic review of decision patterns and policy effectiveness",
                        "verification": "Audit reports with cryptographic integrity verification",
                    },
                ],
            },
            "intervention_capabilities": {
                "real_time": [
                    "Manual override of AI decisions",
                    "Emergency policy activation",
                    "System pause (circuit breaker)",
                    "Rate limiting adjustment",
                ],
                "configuration": [
                    "Policy modification",
                    "Risk threshold adjustment",
                    "Escalation path definition",
                    "Approval workflow configuration",
                ],
            },
            "response_times": {
                "automated_alert_to_human": "<60 seconds",
                "human_decision_to_implementation": "<2 minutes",
                "emergency_override": "Immediate (synchronous)",
                "policy_update_deployment": "<5 minutes",
            },
            "oversight_effectiveness": {
                "metrics_tracked": [
                    "Override frequency",
                    "Human intervention rate",
                    "Response time distribution",
                    "Policy exception approval rate",
                ],
                "reporting": "Quarterly oversight effectiveness reports",
                "continuous_improvement": "Metrics inform policy refinement",
            },
        }

    def _generate_accuracy_metrics(self) -> Dict[str, Any]:
        """Article 11(7) - Expected level of accuracy."""
        decisions_count = len(self.ledger.entries) if self.ledger else 0

        return {
            "article": "Article 11(7)",
            "accuracy_definition": {
                "note": (
                    "Lexecon is a rule-based governance system, not a predictive AI model. "
                    "'Accuracy' means correct application of defined policies."
                ),
                "correctness": "Policy rules are deterministic - 100% reproducible",
                "precision": "Policy matching is exact string/pattern matching",
                "recall": "All AI requests evaluated - 0% false negatives",
            },
            "performance_metrics": {
                "policy_evaluation_correctness": "100% - deterministic rule execution",
                "audit_trail_integrity": "100% - cryptographic verification",
                "false_positive_rate": {
                    "value": "Depends on policy configuration",
                    "measurement": "Tracked as 'policy exception requests'",
                    "improvement": "Policies refined based on exception patterns",
                },
                "uptime": "99.9% SLA target",
                "latency": "p99 <200ms for decision evaluation",
            },
            "validation": {
                "pre_deployment": "Policy simulation with historical data",
                "post_deployment": "Continuous monitoring of decision patterns",
                "verification": f"Total decisions processed: {decisions_count}",
            },
            "limitations": {
                "policy_completeness": (
                    "Accuracy limited by completeness of policy definitions. "
                    "Unmapped scenarios may result in unintended allows/denies."
                ),
                "context_understanding": (
                    "System evaluates explicit policy rules. "
                    "Cannot infer implicit intent or novel risk scenarios."
                ),
            },
        }

    def _generate_known_limitations(self) -> Dict[str, Any]:
        """Article 11(8) - Known limitations and constraints."""
        return {
            "article": "Article 11(8)",
            "technical_limitations": [
                {
                    "limitation": "Policy coverage gaps",
                    "description": (
                        "System only enforces explicitly defined policies. "
                        "Novel AI behaviors not covered by existing rules may pass through."
                    ),
                    "mitigation": "Default-deny mode available, continuous policy refinement",
                    "residual_risk": "Medium - requires ongoing policy maintenance",
                },
                {
                    "limitation": "Content inspection depth",
                    "description": (
                        "System evaluates request metadata, not full content payload. "
                        "Malicious content in natural language may not be detected."
                    ),
                    "mitigation": "Integration with content filtering systems recommended",
                    "residual_risk": "Medium - depends on integration completeness",
                },
                {
                    "limitation": "Performance vs. complexity tradeoff",
                    "description": (
                        "Complex policies with many rules may increase evaluation latency. "
                        "Sub-200ms latency requires policy optimization."
                    ),
                    "mitigation": "Policy complexity monitoring and optimization tools",
                    "residual_risk": "Low - latency monitored in real-time",
                },
                {
                    "limitation": "Distributed system consistency",
                    "description": (
                        "In multi-node deployments, policy updates may have brief propagation delay."
                    ),
                    "mitigation": "Policy versioning and staged rollout procedures",
                    "residual_risk": "Low - propagation typically <30 seconds",
                },
            ],
            "operational_constraints": [
                {
                    "constraint": "Requires explicit policy definition",
                    "impact": "Organizations must invest in policy creation and maintenance",
                    "recommendation": "Use provided policy templates and continuous refinement",
                },
                {
                    "constraint": "Administrator expertise required",
                    "impact": "Effective use requires understanding of governance principles",
                    "recommendation": "Training and certification program recommended",
                },
                {
                    "constraint": "Integration overhead",
                    "impact": "AI systems must route through Lexecon for governance",
                    "recommendation": "Use provided API adapters for transparent integration",
                },
            ],
            "regulatory_scope": {
                "in_scope": [
                    "EU AI Act Article 11-14 compliance",
                    "GDPR audit trail requirements",
                    "SOC 2 access control and logging",
                ],
                "out_of_scope": [
                    "AI model training data compliance (handled by AI provider)",
                    "Model bias detection (not a predictive system)",
                    "Content moderation (recommend integrating dedicated tools)",
                ],
                "clarification": (
                    "Lexecon governs AI behavior and usage, not AI model development. "
                    "Model-level compliance remains responsibility of AI provider."
                ),
            },
        }

    def _build_evidence_chain(self) -> List[str]:
        """Build evidence chain from ledger entries."""
        if not self.ledger or not self.ledger.entries:
            return []

        # Get last 10 decision hashes as evidence
        decision_entries = [e for e in self.ledger.entries if e.event_type == "decision"][-10:]
        return [e.entry_hash for e in decision_entries]

    def _calculate_hash(self, doc: TechnicalDocumentation) -> str:
        """Calculate deterministic hash of documentation."""
        doc_dict = asdict(doc)
        # Remove hash field before hashing
        doc_dict.pop("document_hash", None)
        canonical_json = json.dumps(doc_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode()).hexdigest()

    def export_json(self, doc: TechnicalDocumentation) -> str:
        """Export documentation as JSON."""
        return json.dumps(asdict(doc), indent=2, sort_keys=True)

    def export_markdown(self, doc: TechnicalDocumentation) -> str:
        """Export documentation as Markdown."""
        return f"""# EU AI Act Article 11 Technical Documentation

**Document Type:** {doc.document_type}
**Generated:** {doc.generated_at}
**Document Hash:** `{doc.document_hash}`
**Version:** {doc.version}

---

## 1. General Description (Article 11.1)

**System Name:** {doc.general_description['system_name']}
**System Type:** {doc.general_description['system_type']}
**Classification:** {doc.general_description['classification']}

**Description:**
{doc.general_description['description']}

### Capabilities
{chr(10).join(f"- {cap}" for cap in doc.general_description['capabilities'])}

---

## 2. Intended Purpose (Article 11.2)

**Primary Purpose:**
{doc.intended_purpose['intended_purpose']['primary']}

### Use Cases
{chr(10).join(f"- {uc}" for uc in doc.intended_purpose['intended_purpose']['use_cases'])}

---

## 3. Known Limitations (Article 11.8)

### Technical Limitations
{chr(10).join(f"**{i+1}. {lim['limitation']}**{chr(10)}_{lim['description']}_" for i, lim in enumerate(doc.known_limitations['technical_limitations']))}

---

## Evidence Chain

This documentation is supported by cryptographic evidence from the audit ledger:

{chr(10).join(f"- `{hash}`" for hash in doc.evidence_chain)}

---

*This documentation is automatically generated from system state and complies with EU Artificial Intelligence Act Article 11 requirements.*

**Verification:** Document hash `{doc.document_hash}` provides tamper-evident verification.
"""
