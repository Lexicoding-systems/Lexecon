# Lexecon Demo Script

**Duration**: 10-15 minutes
**Audience**: Enterprise evaluators, compliance officers, security engineers
**Prerequisites**: Lexecon server running on `http://localhost:8000`

---

## Setup

```bash
# Start the server
python -m lexecon.api.server

# Verify server is running
curl http://localhost:8000/
```

Expected: JSON response with system status and available endpoints.

---

## Demo Flow

### Part 1: High-Risk Decision with Escalation (4 minutes)

**Scenario**: AI system makes a content generation decision that triggers toxicity threshold.

#### Step 1.1: Submit a decision for risk assessment

```bash
curl -X POST http://localhost:8000/risk/assess \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "dec_demo_001",
    "actor": "ai_system_v2",
    "action": "generate_content",
    "timestamp": "2026-01-04T12:00:00Z",
    "decision_context": {
      "user_request": "Generate blog post about controversial topic",
      "model": "claude-3-opus",
      "toxicity_score": 0.85
    },
    "risk_factors": {
      "financial_impact": 0.3,
      "reputational_risk": 0.85,
      "safety_concern": 0.7,
      "operational_impact": 0.2,
      "uncertainty": 0.4
    }
  }'
```

**Expected Output**:
```json
{
  "risk_id": "risk_...",
  "decision_id": "dec_demo_001",
  "aggregate_risk_score": 0.82,
  "risk_level": "HIGH",
  "requires_escalation": true,
  "recommendation": "ESCALATE_TO_HUMAN"
}
```

**Observable**: Risk score exceeds threshold (0.70), triggers escalation recommendation.

---

#### Step 1.2: Create escalation

```bash
curl -X POST http://localhost:8000/escalations/ \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "dec_demo_001",
    "escalation_level": "L2",
    "triggered_by": "risk_assessment",
    "trigger_reason": "Reputational risk score (0.85) exceeds threshold (0.70)",
    "assigned_to": "reviewer_alice",
    "priority": "HIGH",
    "sla_hours": 4
  }'
```

**Expected Output**:
```json
{
  "escalation_id": "esc_...",
  "decision_id": "dec_demo_001",
  "status": "PENDING",
  "assigned_to": "reviewer_alice",
  "created_at": "2026-01-04T12:00:01Z",
  "sla_deadline": "2026-01-04T16:00:01Z"
}
```

**Observable**: Escalation created with SLA tracking.

---

#### Step 1.3: Reviewer resolves escalation (approve)

```bash
curl -X POST http://localhost:8000/escalations/esc_<ID>/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "resolution": "APPROVED",
    "resolver": "reviewer_alice",
    "justification": "Content discusses sensitive topic in educational context. Toxicity score triggered by quoted material, not generated content. Approved for publication with editorial review."
  }'
```

**Expected Output**:
```json
{
  "escalation_id": "esc_...",
  "status": "RESOLVED",
  "resolution": "APPROVED",
  "resolved_at": "2026-01-04T12:05:00Z",
  "resolver": "reviewer_alice"
}
```

**Observable**: Escalation resolved with justification captured.

---

### Part 2: Authorized Override (3 minutes)

**Scenario**: System blocks a decision due to policy, but authorized user creates justified override.

#### Step 2.1: Submit decision that violates policy

```bash
curl -X POST http://localhost:8000/risk/assess \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "dec_demo_002",
    "actor": "test_harness",
    "action": "deploy_model_update",
    "timestamp": "2026-01-04T12:10:00Z",
    "decision_context": {
      "environment": "production",
      "testing_complete": false
    },
    "risk_factors": {
      "financial_impact": 0.8,
      "reputational_risk": 0.9,
      "safety_concern": 0.75,
      "operational_impact": 0.85,
      "uncertainty": 0.6
    }
  }'
```

**Expected Output**: High aggregate risk, requires escalation.

---

#### Step 2.2: Create override with justification

```bash
curl -X POST http://localhost:8000/overrides/ \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "dec_demo_002",
    "override_type": "EMERGENCY",
    "actor": "eng_lead_bob",
    "justification": "Critical production incident requires immediate model rollback. Standard testing procedures bypassed due to ongoing service degradation affecting 10k+ users. Post-incident review scheduled.",
    "duration_hours": 1,
    "authorized_by": "cto_carol"
  }'
```

**Expected Output**:
```json
{
  "override_id": "ovr_dec_...",
  "decision_id": "dec_demo_002",
  "override_type": "EMERGENCY",
  "status": "ACTIVE",
  "actor": "eng_lead_bob",
  "authorized_by": "cto_carol",
  "expires_at": "2026-01-04T13:10:00Z"
}
```

**Observable**: Override created with typed reason, mandatory justification, time limit, and authorization chain.

---

### Part 3: Evidence Artifact with Hash Verification (2 minutes)

**Scenario**: Capture governance event as tamper-evident evidence artifact.

#### Step 3.1: Create evidence artifact

```bash
curl -X POST http://localhost:8000/evidence/ \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_type": "escalation_record",
    "source": "escalation_service",
    "content_type": "application/json",
    "content": "{\"escalation_id\": \"esc_demo_001\", \"resolution\": \"APPROVED\"}",
    "related_decision_ids": ["dec_demo_001"],
    "related_control_ids": ["CC6.1", "Art.32"]
  }'
```

**Expected Output**:
```json
{
  "artifact_id": "evd_...",
  "sha256_hash": "a1b2c3d4...",
  "artifact_type": "escalation_record",
  "created_at": "2026-01-04T12:15:00Z",
  "is_immutable": true
}
```

**Observable**: SHA-256 hash computed and stored; artifact immutable.

---

#### Step 3.2: Verify artifact integrity

```bash
# Retrieve artifact
curl http://localhost:8000/evidence/evd_<ID>

# Compute hash locally and compare
echo -n '<content>' | shasum -a 256
```

**Observable**: Hash matches stored value, proving content has not been tampered with.

---

### Part 4: Audit Export Generation (3 minutes)

**Scenario**: Generate complete audit package for regulatory submission.

#### Step 4.1: Create audit export request

```bash
curl -X POST http://localhost:8000/audit-export/exports \
  -H "Content-Type: application/json" \
  -d '{
    "requester": "compliance_officer_dana",
    "purpose": "Q4 2025 SOC 2 audit preparation",
    "scope": "all",
    "format": "json",
    "start_date": "2026-01-01T00:00:00Z",
    "end_date": "2026-01-04T23:59:59Z",
    "include_deleted": false,
    "metadata": {
      "audit_firm": "Example Auditors LLP",
      "audit_period": "2025-Q4"
    }
  }'
```

**Expected Output**:
```json
{
  "export_id": "exp_...",
  "status": "PENDING",
  "requested_at": "2026-01-04T12:20:00Z"
}
```

---

#### Step 4.2: Generate export

```bash
curl -X POST http://localhost:8000/audit-export/exports/exp_<ID>/generate
```

**Expected Output**:
```json
{
  "export_id": "exp_...",
  "status": "COMPLETED",
  "generated_at": "2026-01-04T12:20:05Z",
  "file_path": "/tmp/lexecon_exports/exp_.../audit_export.json"
}
```

---

#### Step 4.3: Download and inspect export

```bash
curl http://localhost:8000/audit-export/exports/exp_<ID>/download \
  -o audit_export.json

# Inspect manifest
cat audit_export.json | jq '.manifest'
```

**Expected Observable**:
- Manifest with packet metadata
- Root checksum for integrity verification
- Counts: decisions, risks, escalations, overrides, evidence
- Date range covered
- Frameworks included

---

#### Step 4.4: Verify export integrity

```bash
# Extract root checksum from manifest
ROOT_HASH=$(cat audit_export.json | jq -r '.manifest.integrity.root_checksum')

# Verify (future: use CLI tool)
echo "Root hash: $ROOT_HASH"
```

**Observable**: Root checksum present; can be independently verified.

---

### Part 5: Compliance Mapping (2 minutes)

**Scenario**: View how evidence maps to compliance controls.

#### Step 5.1: Query compliance coverage

```bash
curl http://localhost:8000/compliance/frameworks/soc2/coverage
```

**Expected Output**:
```json
{
  "framework_id": "soc2",
  "total_controls": 64,
  "controls_with_evidence": 12,
  "coverage_percentage": 0.19,
  "last_updated": "2026-01-04T12:20:00Z"
}
```

**Observable**: Explicit coverage calculation based on evidence linkage.

---

#### Step 5.2: View specific control evidence

```bash
curl http://localhost:8000/compliance/controls/CC6.1
```

**Expected Output**:
```json
{
  "control_id": "CC6.1",
  "framework": "soc2",
  "description": "Logical and Physical Access Controls",
  "linked_evidence_count": 3,
  "evidence_artifacts": [
    "evd_...",
    "evd_...",
    "evd_..."
  ]
}
```

**Observable**: Evidence artifacts explicitly linked to control; traceability established.

---

## Demo Completion Checklist

After completing the demo, you should have observed:

- [ ] High-risk decision triggered escalation
- [ ] Human reviewer resolved escalation with justification
- [ ] Emergency override created with authorization chain
- [ ] Evidence artifact created with SHA-256 hash
- [ ] Hash integrity verified
- [ ] Audit export generated with manifest
- [ ] Compliance control mapped to evidence
- [ ] All actions traceable via decision IDs

---

## Cleanup (Optional)

```bash
# Stop server
# Press Ctrl+C in server terminal

# Clear demo data (if desired)
# Note: In-memory stores clear on restart
```

---

## Next Steps

After the demo:
1. Review `docs/GOVERNANCE_PRIMITIVES_SPEC.md` for complete data model
2. Explore `docs/AUDIT_PACKET_SPEC.md` for audit package format
3. Check `docs/BUYER_EVALUATION_CHECKLIST.md` for evaluation criteria
4. Review `docs/SECURITY_POSTURE.md` for threat model and controls
