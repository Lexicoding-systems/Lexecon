# Lexecon System Overview

## What Lexecon Is

Lexecon is **human oversight infrastructure for AI systems**. It provides the governance layer that sits between AI decision-making and production deployment, ensuring that high-risk decisions receive appropriate human review, all interventions are auditable, and organizations can demonstrate alignment with their stated governance policies.

Lexecon implements a closed-loop governance workflow:

```
Decision → Risk Assessment → (if high risk) → Escalation → Human Review
                                                    ↓
                                          Approve / Reject / Override
                                                    ↓
                                            Evidence Artifact
                                                    ↓
                                              Immutable Ledger
                                                    ↓
                                            Compliance Mapping
                                                    ↓
                                              Audit Export
```

### Core Capabilities

**Risk Assessment**: Multi-dimensional risk scoring (financial, reputational, safety, operational) with configurable thresholds and uncertainty quantification.

**Escalation Workflow**: Tiered human review routing with SLA tracking, resolution workflows, and intervention budget management.

**Override Governance**: Typed, justified overrides with mandatory authorization trails for legitimate policy exceptions.

**Evidence Linking**: Cryptographically-hashed evidence artifacts linked to decisions, creating tamper-evident audit chains.

**Compliance Mapping**: Explicit control-to-evidence mappings for regulatory frameworks (SOC 2, ISO 27001, GDPR).

**Audit Export**: Deterministic, reproducible audit packages with integrity verification.

---

## What Lexecon Is Not

**Not a model safety layer**: Lexecon does not fine-tune models, filter outputs, or implement prompt guardrails. It governs the decision process, not the model itself.

**Not a compliance certification tool**: Lexecon provides evidence and control mappings to support compliance efforts. It does not certify or guarantee regulatory compliance.

**Not a monitoring dashboard**: While Lexecon includes basic dashboards, it is not a comprehensive observability or APM tool.

**Not an access control system**: Lexecon tracks governance decisions but is not a replacement for authentication, authorization, or identity management systems.

---

## The Closed-Loop Model

Lexecon enforces a governance loop where every AI decision flows through defined checkpoints:

### 1. Decision Entry
AI system makes a decision and submits it to Lexecon with context.

### 2. Risk Assessment
Multi-dimensional risk scoring evaluates the decision against configured thresholds:
- Financial impact
- Reputational risk
- Safety concerns
- Operational consequences
- Uncertainty level

### 3. Conditional Escalation
If risk exceeds thresholds, decision escalates to appropriate human reviewer tier (L1/L2/L3/Executive).

### 4. Human Intervention
Reviewer receives context-rich summary and decides:
- **Approve**: Allow decision to proceed
- **Reject**: Block decision
- **Modify**: Approve with conditions
- **Escalate**: Route to higher authority

### 5. Override Path (Exceptional)
Authorized actors can override policies with:
- Typed override (policy/risk_acceptance/emergency/testing)
- Mandatory justification
- Duration limits
- Authorization trail

### 6. Evidence Capture
All governance events produce **EvidenceArtifacts**:
- SHA-256 hashed
- Linked to decision IDs
- Linked to control IDs
- Immutable once created

### 7. Immutable Ledger
Evidence artifacts append to tamper-evident ledger, creating reconstructable decision history.

### 8. Compliance Mapping
Evidence artifacts automatically map to relevant controls in configured frameworks, demonstrating coverage.

### 9. Audit Export
Generate time-scoped, cryptographically-verified audit packages containing complete decision histories.

---

## Primary Use Cases

**Pre-deployment governance**: Route high-stakes AI decisions to human review before taking action.

**Regulatory audit preparation**: Generate complete, verifiable audit trails for compliance assessments.

**Incident investigation**: Reconstruct decision chains to understand what happened and why.

**Policy effectiveness measurement**: Analyze escalation patterns, override frequency, and risk trends.

---

## Architecture Summary

**Services Layer**:
- RiskAssessmentService
- EscalationService
- OverrideService
- EvidenceService
- ComplianceMappingService
- AuditExportService

**Data Layer**:
- ImmutableLedger (decision log)
- EvidenceStore (artifact storage)
- ComplianceMapping (control linkage)

**API Layer**:
- REST API (FastAPI)
- Webhook support for integrations

**UI Layer**:
- Governance dashboard
- Escalation queue
- Override management
- Audit export wizard

See `docs/architecture/closed_loop.mmd` for detailed component diagram.

---

## Documentation Map

### Foundational Specifications
- **`docs/GOVERNANCE_PRIMITIVES_SPEC.md`**: Canonical data model and primitives (Decision, Risk, Escalation, Override, EvidenceArtifact)
- **`/model_governance_pack/schemas/*.json`**: JSON schemas (source of truth for data contracts)

### Design Philosophy
- **`docs/HUMAN_CENTERED_GOVERNANCE_UX.md`**: UX principles for calm-first, intervention-budget-aware interfaces
- **`docs/AUDIT_PACKET_SPEC.md`**: Audit package structure, determinism guarantees, and verification

### Enterprise Readiness
- **`docs/ENTERPRISE_READINESS_GAPS.md`**: Gap analysis, competitive positioning, and roadmap

### Integration & Operations
- **`docs/DEMO_SCRIPT.md`**: 10-15 minute walkthrough for evaluation
- **`docs/API_VERSIONING.md`**: API stability and deprecation policy
- **`docs/SECURITY_POSTURE.md`**: Threat model, controls, and limitations

### Trust Artifacts
- **`docs/AUDIT_VERIFICATION.md`**: Audit package integrity verification
- **`docs/BUYER_EVALUATION_CHECKLIST.md`**: Evaluation guide for procurement

---

## Implementation Status

**Complete (Phases 1-8)**:
- ✓ Risk Assessment Service
- ✓ Escalation Service
- ✓ Override Service
- ✓ Evidence Service
- ✓ REST API Layer
- ✓ Governance Dashboard
- ✓ Compliance Mapping
- ✓ Audit Export Pipeline

**In Progress (Phases 9-11)**:
- Externalization (documentation, demo scripts)
- Procurement signals (security posture, verification tooling)
- Optional hardening (append-only storage, determinism tests)

**Future Considerations**:
- Security hardening (OAuth/OIDC, RBAC, encryption at rest)
- Database backend (PostgreSQL with persistence)
- Observability (Prometheus, OpenTelemetry, alerting)
- Kubernetes deployment (Helm charts, horizontal scaling)
- Multi-tenancy (tenant isolation, resource quotas)

---

## Quick Start

1. **Install**: `pip install -e .`
2. **Run server**: `python -m lexecon.api.server`
3. **Access dashboard**: `http://localhost:8000`
4. **Follow demo**: See `docs/DEMO_SCRIPT.md`

---

## Design Principles

**Evidence over claims**: Demonstrate alignment through explicit control mappings and artifact linkage, not assertions.

**Calm by default**: Minimize interruptions; reserve alerts for decisions requiring human judgment.

**Audit-first architecture**: Every governance action produces verifiable, tamper-evident records.

**Progressive disclosure**: Show summaries first, provide detail on demand.

**Human-centered**: Protect reviewer cognitive capacity through intervention budgets and batching.

---

## Questions Lexecon Answers

**For Engineers**: "Did this decision go through appropriate review?"

**For Compliance Officers**: "Can we demonstrate control effectiveness for [framework]?"

**For Auditors**: "What evidence exists for decisions in [time period]?"

**For Risk Managers**: "What patterns exist in escalations and overrides?"

**For Executives**: "How effective is our AI governance in practice?"
