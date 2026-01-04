# Lexecon Governance Primitives Specification

**Version:** 1.0.0
**Status:** Canonical
**Last Updated:** 2026-01-04

---

## 1. Domain Glossary

### 1.1 Decision

A **Decision** is an immutable record of a governance evaluation outcome. It captures whether a proposed action was approved, denied, escalated, or conditionally permitted, along with the reasoning chain and evidence that led to that outcome.

**Purpose:** Provides audit trail, enables post-hoc review, and supports compliance reporting.

**Lifecycle:** `pending` → `evaluated` → `finalized` (immutable after finalization)

---

### 1.2 Policy

A **Policy** is a declarative specification of permitted, forbidden, and conditionally-allowed behaviors. Policies define the rules that govern actor-action-resource relationships within the system.

**Purpose:** Encodes organizational governance intent in machine-readable form.

**Composition:** Policies contain terms (actors, actions, resources), relations (permits/forbids), and constraints (conditional rules).

---

### 1.3 Actor

An **Actor** is any entity capable of initiating or participating in governed actions. Actors include AI agents, human users, automated systems, and organizational roles.

**Purpose:** Identifies the subject of governance decisions and enables role-based access control.

**Types:** `ai_agent`, `human_user`, `system_service`, `organizational_role`, `external_party`

---

### 1.4 Action

An **Action** is a discrete, auditable operation that an actor may request to perform. Actions are the verbs of governance—the operations that policies permit or forbid.

**Purpose:** Defines the granular operations subject to governance control.

**Categories:** `read`, `write`, `execute`, `transmit`, `delete`, `approve`, `escalate`

---

### 1.5 Resource

A **Resource** is any data, system, or capability that is the target of an action. Resources are classified by sensitivity, ownership, and compliance requirements.

**Purpose:** Defines what is being accessed or modified, enabling data-centric governance.

**Classification Levels:** `public`, `internal`, `confidential`, `restricted`, `critical`

---

### 1.6 Context

**Context** is the situational metadata that accompanies a governance request. It includes temporal, environmental, behavioral, and session information that may influence policy evaluation.

**Purpose:** Enables context-aware policy decisions (time-of-day, location, risk signals).

**Scope:** Request-scoped (not persisted beyond decision lifecycle).

---

### 1.7 Risk

**Risk** is a quantified assessment of potential harm associated with an action. It combines likelihood and impact scores with categorical risk dimensions.

**Purpose:** Enables risk-based policy escalation and prioritized human review.

**Dimensions:** `security`, `privacy`, `compliance`, `operational`, `reputational`, `financial`

---

### 1.8 Compliance Control

A **Compliance Control** is a governance requirement derived from regulatory frameworks (SOC 2, HIPAA, GDPR, etc.). Controls map external obligations to internal policy constraints.

**Purpose:** Ensures governance aligns with regulatory requirements and supports compliance audits.

**Mapping:** One control may map to multiple policy constraints; multiple frameworks may share controls.

---

### 1.9 Override

An **Override** is an authorized exception to normal policy evaluation. Overrides require explicit justification, elevated approval, and enhanced audit logging.

**Purpose:** Enables business continuity while maintaining accountability for exceptions.

**Types:** `emergency_bypass`, `executive_override`, `time_limited_exception`, `risk_accepted`

---

### 1.10 Escalation

An **Escalation** is a routing of a governance decision to a higher authority when automated evaluation cannot proceed or risk thresholds are exceeded.

**Purpose:** Ensures human oversight for ambiguous or high-risk scenarios.

**Triggers:** Risk threshold exceeded, policy conflict detected, explicit escalation rule, actor request.

---

### 1.11 Evidence Artifact

An **Evidence Artifact** is an immutable record that supports audit defensibility. Artifacts include logs, screenshots, hashes, attestations, and any material relevant to proving governance compliance.

**Purpose:** Provides cryptographically verifiable proof for auditors and legal review.

**Integrity:** All artifacts include SHA-256 hash, timestamp, and optional digital signature.

---

## 2. Canonical Naming Conventions

### 2.1 Identifier Patterns

| Primitive | Pattern | Example |
|-----------|---------|---------|
| Decision | `dec_{ulid}` | `dec_01HQXK5M8N2P3R4S5T6V7W8X9Y` |
| Policy | `pol_{org}_{name}_{version}` | `pol_acme_data_access_v2` |
| Actor | `act_{type}:{identifier}` | `act_ai:claude_agent_01` |
| Action | `axn_{category}:{operation}` | `axn_write:file_create` |
| Resource | `res_{class}:{path}` | `res_pii:customer/profiles` |
| Context | `ctx_{session_id}` | `ctx_sess_abc123` |
| Risk | `rsk_{decision_id}` | `rsk_dec_01HQX...` |
| Compliance Control | `ctl_{framework}:{control_id}` | `ctl_soc2:CC6.1` |
| Override | `ovr_{decision_id}_{seq}` | `ovr_dec_01HQX..._001` |
| Escalation | `esc_{decision_id}` | `esc_dec_01HQX...` |
| Evidence Artifact | `evd_{type}_{hash_prefix}` | `evd_log_a1b2c3d4` |

### 2.2 Field Naming Rules

- **snake_case** for all field names
- **Timestamps:** ISO 8601 format with timezone (`2026-01-04T12:00:00Z`)
- **Enums:** lowercase with underscores (`risk_accepted`, `human_user`)
- **Boolean fields:** Prefixed with `is_`, `has_`, or `requires_`
- **Arrays:** Plural form (`actors`, `conditions`, `artifacts`)

---

## 3. JSON Schemas

### 3.1 Decision Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/decision.json",
  "title": "Lexecon Decision",
  "type": "object",
  "required": [
    "decision_id",
    "request_id",
    "actor_id",
    "action_id",
    "outcome",
    "timestamp",
    "policy_ids"
  ],
  "properties": {
    "decision_id": {
      "type": "string",
      "pattern": "^dec_[A-Z0-9]{26}$",
      "description": "Unique decision identifier (ULID format)"
    },
    "request_id": {
      "type": "string",
      "description": "Correlation ID linking to original request"
    },
    "actor_id": {
      "type": "string",
      "pattern": "^act_[a-z_]+:.+$",
      "description": "Actor who requested the action"
    },
    "action_id": {
      "type": "string",
      "pattern": "^axn_[a-z_]+:.+$",
      "description": "Action that was evaluated"
    },
    "resource_id": {
      "type": "string",
      "pattern": "^res_[a-z_]+:.+$",
      "description": "Target resource of the action"
    },
    "outcome": {
      "type": "string",
      "enum": ["approved", "denied", "escalated", "conditional"],
      "description": "Decision outcome"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "When decision was made"
    },
    "policy_ids": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "description": "Policies evaluated for this decision"
    },
    "reasoning": {
      "type": "string",
      "description": "Human-readable explanation of decision"
    },
    "risk_assessment": {
      "$ref": "#/definitions/risk_ref",
      "description": "Associated risk assessment"
    },
    "conditions": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Conditions attached to conditional approval"
    },
    "evidence_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Evidence artifacts supporting this decision"
    },
    "context_snapshot": {
      "type": "object",
      "description": "Frozen context at decision time"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  },
  "definitions": {
    "risk_ref": {
      "type": "string",
      "pattern": "^rsk_dec_[A-Z0-9]{26}$"
    }
  }
}
```

### 3.2 Policy Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/policy.json",
  "title": "Lexecon Policy",
  "type": "object",
  "required": [
    "policy_id",
    "name",
    "version",
    "mode",
    "terms",
    "relations"
  ],
  "properties": {
    "policy_id": {
      "type": "string",
      "pattern": "^pol_[a-z0-9_]+_v[0-9]+$",
      "description": "Unique policy identifier"
    },
    "name": {
      "type": "string",
      "minLength": 3,
      "maxLength": 128,
      "description": "Human-readable policy name"
    },
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
      "description": "Semantic version"
    },
    "mode": {
      "type": "string",
      "enum": ["permissive", "strict", "paranoid"],
      "description": "Policy evaluation mode"
    },
    "terms": {
      "type": "array",
      "items": { "$ref": "#/definitions/term" },
      "description": "Defined terms (actors, actions, resources)"
    },
    "relations": {
      "type": "array",
      "items": { "$ref": "#/definitions/relation" },
      "description": "Permission/prohibition rules"
    },
    "description": {
      "type": "string",
      "description": "Policy description and purpose"
    },
    "compliance_frameworks": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Associated compliance frameworks"
    },
    "constraints": {
      "type": "array",
      "items": { "$ref": "#/definitions/constraint" },
      "description": "Conditional constraints"
    },
    "effective_from": {
      "type": "string",
      "format": "date-time",
      "description": "When policy becomes active"
    },
    "effective_until": {
      "type": "string",
      "format": "date-time",
      "description": "When policy expires"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  },
  "definitions": {
    "term": {
      "type": "object",
      "required": ["id", "type", "name"],
      "properties": {
        "id": { "type": "string" },
        "type": { "type": "string", "enum": ["actor", "action", "resource", "data_class"] },
        "name": { "type": "string" },
        "description": { "type": "string" },
        "attributes": { "type": "object" }
      }
    },
    "relation": {
      "type": "object",
      "required": ["type", "subject", "action"],
      "properties": {
        "type": { "type": "string", "enum": ["permits", "forbids", "requires"] },
        "subject": { "type": "string" },
        "action": { "type": "string" },
        "object": { "type": "string" },
        "conditions": { "type": "array", "items": { "type": "string" } },
        "justification": { "type": "string" }
      }
    },
    "constraint": {
      "type": "object",
      "required": ["name", "condition", "action"],
      "properties": {
        "name": { "type": "string" },
        "condition": { "type": "string" },
        "action": { "type": "string" },
        "justification": { "type": "string" }
      }
    }
  }
}
```

### 3.3 Actor Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/actor.json",
  "title": "Lexecon Actor",
  "type": "object",
  "required": [
    "actor_id",
    "actor_type",
    "name"
  ],
  "properties": {
    "actor_id": {
      "type": "string",
      "pattern": "^act_[a-z_]+:.+$",
      "description": "Unique actor identifier"
    },
    "actor_type": {
      "type": "string",
      "enum": ["ai_agent", "human_user", "system_service", "organizational_role", "external_party"],
      "description": "Classification of actor"
    },
    "name": {
      "type": "string",
      "description": "Display name"
    },
    "description": {
      "type": "string",
      "description": "Actor description"
    },
    "parent_actor_id": {
      "type": "string",
      "description": "Hierarchical parent (for delegation)"
    },
    "roles": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Assigned roles"
    },
    "trust_level": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Trust score (0-100)"
    },
    "is_active": {
      "type": "boolean",
      "default": true,
      "description": "Whether actor is currently active"
    },
    "attributes": {
      "type": "object",
      "description": "Type-specific attributes"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  }
}
```

### 3.4 Action Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/action.json",
  "title": "Lexecon Action",
  "type": "object",
  "required": [
    "action_id",
    "category",
    "operation"
  ],
  "properties": {
    "action_id": {
      "type": "string",
      "pattern": "^axn_[a-z_]+:.+$",
      "description": "Unique action identifier"
    },
    "category": {
      "type": "string",
      "enum": ["read", "write", "execute", "transmit", "delete", "approve", "escalate"],
      "description": "Action category"
    },
    "operation": {
      "type": "string",
      "description": "Specific operation name"
    },
    "description": {
      "type": "string",
      "description": "Human-readable description"
    },
    "risk_weight": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10,
      "description": "Inherent risk weight (1-10)"
    },
    "is_reversible": {
      "type": "boolean",
      "description": "Whether action can be undone"
    },
    "requires_confirmation": {
      "type": "boolean",
      "default": false,
      "description": "Requires explicit user confirmation"
    },
    "parameters_schema": {
      "type": "object",
      "description": "JSON Schema for action parameters"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  }
}
```

### 3.5 Resource Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/resource.json",
  "title": "Lexecon Resource",
  "type": "object",
  "required": [
    "resource_id",
    "classification",
    "name"
  ],
  "properties": {
    "resource_id": {
      "type": "string",
      "pattern": "^res_[a-z_]+:.+$",
      "description": "Unique resource identifier"
    },
    "classification": {
      "type": "string",
      "enum": ["public", "internal", "confidential", "restricted", "critical"],
      "description": "Data classification level"
    },
    "name": {
      "type": "string",
      "description": "Resource name"
    },
    "resource_type": {
      "type": "string",
      "enum": ["data", "system", "capability", "api", "file", "database", "service"],
      "description": "Type of resource"
    },
    "description": {
      "type": "string",
      "description": "Resource description"
    },
    "owner_actor_id": {
      "type": "string",
      "description": "Actor who owns this resource"
    },
    "compliance_tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Compliance-relevant tags (pii, phi, financial)"
    },
    "retention_days": {
      "type": "integer",
      "description": "Data retention period in days"
    },
    "is_encrypted": {
      "type": "boolean",
      "description": "Whether resource is encrypted at rest"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  }
}
```

### 3.6 Context Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/context.json",
  "title": "Lexecon Context",
  "type": "object",
  "required": [
    "context_id",
    "session_id",
    "timestamp"
  ],
  "properties": {
    "context_id": {
      "type": "string",
      "pattern": "^ctx_.+$",
      "description": "Unique context identifier"
    },
    "session_id": {
      "type": "string",
      "description": "Session this context belongs to"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Context capture time"
    },
    "user_intent": {
      "type": "string",
      "description": "Stated user intent"
    },
    "environment": {
      "type": "object",
      "properties": {
        "deployment": { "type": "string", "enum": ["production", "staging", "development"] },
        "region": { "type": "string" },
        "network_zone": { "type": "string" }
      },
      "description": "Environment metadata"
    },
    "temporal": {
      "type": "object",
      "properties": {
        "is_business_hours": { "type": "boolean" },
        "day_of_week": { "type": "string" },
        "timezone": { "type": "string" }
      },
      "description": "Temporal context"
    },
    "behavioral": {
      "type": "object",
      "properties": {
        "request_rate": { "type": "number" },
        "anomaly_score": { "type": "number" },
        "session_action_count": { "type": "integer" }
      },
      "description": "Behavioral signals"
    },
    "prior_decisions": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Recent decision IDs in this session"
    },
    "custom": {
      "type": "object",
      "description": "Custom context attributes"
    }
  }
}
```

### 3.7 Risk Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/risk.json",
  "title": "Lexecon Risk Assessment",
  "type": "object",
  "required": [
    "risk_id",
    "decision_id",
    "overall_score",
    "timestamp"
  ],
  "properties": {
    "risk_id": {
      "type": "string",
      "pattern": "^rsk_dec_.+$",
      "description": "Unique risk assessment identifier"
    },
    "decision_id": {
      "type": "string",
      "description": "Associated decision"
    },
    "overall_score": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "description": "Aggregate risk score (1-100)"
    },
    "risk_level": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"],
      "description": "Categorical risk level"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Assessment timestamp"
    },
    "dimensions": {
      "type": "object",
      "properties": {
        "security": { "type": "integer", "minimum": 0, "maximum": 100 },
        "privacy": { "type": "integer", "minimum": 0, "maximum": 100 },
        "compliance": { "type": "integer", "minimum": 0, "maximum": 100 },
        "operational": { "type": "integer", "minimum": 0, "maximum": 100 },
        "reputational": { "type": "integer", "minimum": 0, "maximum": 100 },
        "financial": { "type": "integer", "minimum": 0, "maximum": 100 }
      },
      "description": "Risk scores by dimension"
    },
    "likelihood": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Probability of harm (0-1)"
    },
    "impact": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5,
      "description": "Severity of potential harm (1-5)"
    },
    "factors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "weight": { "type": "number" },
          "value": { "type": "number" }
        }
      },
      "description": "Contributing risk factors"
    },
    "mitigations_applied": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Mitigations factored into score"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  }
}
```

### 3.8 Compliance Control Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/compliance_control.json",
  "title": "Lexecon Compliance Control",
  "type": "object",
  "required": [
    "control_id",
    "framework",
    "control_ref",
    "name"
  ],
  "properties": {
    "control_id": {
      "type": "string",
      "pattern": "^ctl_[a-z0-9_]+:.+$",
      "description": "Unique control identifier"
    },
    "framework": {
      "type": "string",
      "enum": ["soc2", "hipaa", "gdpr", "pci_dss", "iso27001", "nist_csf", "fedramp", "ccpa"],
      "description": "Compliance framework"
    },
    "control_ref": {
      "type": "string",
      "description": "Framework-specific control reference (e.g., CC6.1)"
    },
    "name": {
      "type": "string",
      "description": "Control name"
    },
    "description": {
      "type": "string",
      "description": "Control requirement description"
    },
    "category": {
      "type": "string",
      "description": "Control category within framework"
    },
    "policy_mappings": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Policy IDs that implement this control"
    },
    "evidence_requirements": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Required evidence types for audit"
    },
    "test_procedure": {
      "type": "string",
      "description": "How to test control effectiveness"
    },
    "is_active": {
      "type": "boolean",
      "default": true,
      "description": "Whether control is currently enforced"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  }
}
```

### 3.9 Override Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/override.json",
  "title": "Lexecon Override",
  "type": "object",
  "required": [
    "override_id",
    "decision_id",
    "override_type",
    "authorized_by",
    "justification",
    "timestamp"
  ],
  "properties": {
    "override_id": {
      "type": "string",
      "pattern": "^ovr_dec_.+$",
      "description": "Unique override identifier"
    },
    "decision_id": {
      "type": "string",
      "description": "Decision being overridden"
    },
    "override_type": {
      "type": "string",
      "enum": ["emergency_bypass", "executive_override", "time_limited_exception", "risk_accepted"],
      "description": "Type of override"
    },
    "authorized_by": {
      "type": "string",
      "description": "Actor ID who authorized override"
    },
    "justification": {
      "type": "string",
      "minLength": 20,
      "description": "Required justification (min 20 chars)"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "When override was granted"
    },
    "original_outcome": {
      "type": "string",
      "enum": ["denied", "escalated"],
      "description": "What the decision was before override"
    },
    "new_outcome": {
      "type": "string",
      "enum": ["approved", "conditional"],
      "description": "Outcome after override"
    },
    "expires_at": {
      "type": "string",
      "format": "date-time",
      "description": "When time-limited override expires"
    },
    "scope": {
      "type": "object",
      "properties": {
        "is_one_time": { "type": "boolean" },
        "applies_to_policy": { "type": "string" },
        "applies_to_actor": { "type": "string" }
      },
      "description": "Override scope limitations"
    },
    "review_required_by": {
      "type": "string",
      "format": "date-time",
      "description": "When override must be reviewed"
    },
    "evidence_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Supporting evidence for override"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  }
}
```

### 3.10 Escalation Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/escalation.json",
  "title": "Lexecon Escalation",
  "type": "object",
  "required": [
    "escalation_id",
    "decision_id",
    "trigger",
    "escalated_to",
    "status",
    "created_at"
  ],
  "properties": {
    "escalation_id": {
      "type": "string",
      "pattern": "^esc_dec_.+$",
      "description": "Unique escalation identifier"
    },
    "decision_id": {
      "type": "string",
      "description": "Decision that triggered escalation"
    },
    "trigger": {
      "type": "string",
      "enum": ["risk_threshold", "policy_conflict", "explicit_rule", "actor_request", "anomaly_detected"],
      "description": "What triggered the escalation"
    },
    "escalated_to": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "description": "Actor IDs to review"
    },
    "status": {
      "type": "string",
      "enum": ["pending", "acknowledged", "resolved", "expired"],
      "description": "Escalation status"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "When escalation was created"
    },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"],
      "description": "Escalation priority"
    },
    "sla_deadline": {
      "type": "string",
      "format": "date-time",
      "description": "When response is required"
    },
    "acknowledged_at": {
      "type": "string",
      "format": "date-time",
      "description": "When escalation was acknowledged"
    },
    "acknowledged_by": {
      "type": "string",
      "description": "Actor who acknowledged"
    },
    "resolved_at": {
      "type": "string",
      "format": "date-time",
      "description": "When escalation was resolved"
    },
    "resolution": {
      "type": "object",
      "properties": {
        "outcome": { "type": "string", "enum": ["approved", "denied", "deferred"] },
        "resolved_by": { "type": "string" },
        "notes": { "type": "string" }
      },
      "description": "Resolution details"
    },
    "context_summary": {
      "type": "string",
      "description": "Summary for reviewer"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  }
}
```

### 3.11 Evidence Artifact Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://lexecon.io/schemas/evidence_artifact.json",
  "title": "Lexecon Evidence Artifact",
  "type": "object",
  "required": [
    "artifact_id",
    "artifact_type",
    "sha256_hash",
    "created_at",
    "source"
  ],
  "properties": {
    "artifact_id": {
      "type": "string",
      "pattern": "^evd_[a-z]+_[a-f0-9]{8}$",
      "description": "Unique artifact identifier"
    },
    "artifact_type": {
      "type": "string",
      "enum": ["decision_log", "policy_snapshot", "context_capture", "screenshot", "attestation", "signature", "audit_trail", "external_report"],
      "description": "Type of evidence"
    },
    "sha256_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "SHA-256 hash of content"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "When artifact was created"
    },
    "source": {
      "type": "string",
      "description": "System/process that created artifact"
    },
    "content_type": {
      "type": "string",
      "description": "MIME type of content"
    },
    "size_bytes": {
      "type": "integer",
      "description": "Content size in bytes"
    },
    "storage_uri": {
      "type": "string",
      "format": "uri",
      "description": "Where artifact is stored"
    },
    "related_decision_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Decisions this evidence supports"
    },
    "related_control_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Compliance controls this satisfies"
    },
    "digital_signature": {
      "type": "object",
      "properties": {
        "algorithm": { "type": "string" },
        "signature": { "type": "string" },
        "signer_id": { "type": "string" },
        "signed_at": { "type": "string", "format": "date-time" }
      },
      "description": "Optional digital signature"
    },
    "retention_until": {
      "type": "string",
      "format": "date-time",
      "description": "Retention deadline"
    },
    "is_immutable": {
      "type": "boolean",
      "default": true,
      "description": "Whether artifact can be modified"
    },
    "metadata": {
      "type": "object",
      "description": "Extensible metadata"
    }
  }
}
```

---

## 4. Primitive Mapping Table

### 4.1 Backend Module Mapping

| Primitive | Backend Module | Primary Table | API Endpoint |
|-----------|----------------|---------------|--------------|
| Decision | `lexecon.decision` | `decisions` | `/api/v1/decisions` |
| Policy | `lexecon.policy` | `policies` | `/api/v1/policies` |
| Actor | `lexecon.identity` | `actors` | `/api/v1/actors` |
| Action | `lexecon.capability` | `actions` | `/api/v1/actions` |
| Resource | `lexecon.capability` | `resources` | `/api/v1/resources` |
| Context | `lexecon.decision` | (embedded) | (via decision) |
| Risk | `lexecon.decision` | `risk_assessments` | `/api/v1/risks` |
| Compliance Control | `lexecon.compliance` | `compliance_controls` | `/api/v1/controls` |
| Override | `lexecon.responsibility` | `overrides` | `/api/v1/overrides` |
| Escalation | `lexecon.responsibility` | `escalations` | `/api/v1/escalations` |
| Evidence Artifact | `lexecon.ledger` | `evidence_artifacts` | `/api/v1/evidence` |

### 4.2 UI Surface Mapping

| Primitive | Governance UI | Runtime UI | Executive UI |
|-----------|---------------|------------|--------------|
| **Decision** | Decision history browser | Real-time decision feed | Decision analytics dashboard |
| **Policy** | Policy editor, version diff | Active policy indicator | Policy coverage report |
| **Actor** | Actor registry, role mgmt | Actor context panel | Actor activity heatmap |
| **Action** | Action catalog editor | Action request log | Action frequency charts |
| **Resource** | Resource classification UI | Resource access indicator | Data exposure summary |
| **Context** | Context template editor | Live context display | — |
| **Risk** | Risk threshold config | Risk score badge | Risk trend dashboard |
| **Compliance Control** | Control mapping editor | Control status indicator | Compliance posture report |
| **Override** | Override policy config | Override request form | Override audit report |
| **Escalation** | Escalation rules editor | Escalation queue | SLA compliance metrics |
| **Evidence Artifact** | Evidence config | — | Audit export builder |

### 4.3 Audit Export Mapping

| Primitive | Export Format | SOC 2 Evidence | HIPAA Relevance | GDPR Article |
|-----------|---------------|----------------|-----------------|--------------|
| Decision | JSON, CSV, PDF | CC6.1, CC7.2 | Access audit | Art. 30 |
| Policy | JSON, YAML, PDF | CC1.1, CC5.2 | Policy documentation | Art. 24 |
| Actor | JSON, CSV | CC6.1, CC6.2 | User identification | Art. 4(1) |
| Action | JSON, CSV | CC6.1, CC7.1 | Activity logging | Art. 30 |
| Resource | JSON, CSV | CC6.1 | Asset inventory | Art. 30 |
| Context | JSON (embedded) | CC7.2 | Circumstance logging | — |
| Risk | JSON, PDF | CC3.1, CC4.1 | Risk assessment | Art. 35 |
| Compliance Control | JSON, PDF, Excel | All CC categories | All safeguards | Art. 5, 32 |
| Override | JSON, PDF | CC6.1, CC6.8 | Emergency access | Art. 32 |
| Escalation | JSON, CSV | CC2.2, CC7.3 | Incident management | Art. 33 |
| Evidence Artifact | Native + hash | All (proof) | All (proof) | Art. 5(2) |

---

## 5. Field Reference Summary

### 5.1 Required vs Optional Fields by Primitive

| Primitive | Required Fields | Optional Fields |
|-----------|-----------------|-----------------|
| **Decision** | `decision_id`, `request_id`, `actor_id`, `action_id`, `outcome`, `timestamp`, `policy_ids` | `resource_id`, `reasoning`, `risk_assessment`, `conditions`, `evidence_ids`, `context_snapshot`, `metadata` |
| **Policy** | `policy_id`, `name`, `version`, `mode`, `terms`, `relations` | `description`, `compliance_frameworks`, `constraints`, `effective_from`, `effective_until`, `metadata` |
| **Actor** | `actor_id`, `actor_type`, `name` | `description`, `parent_actor_id`, `roles`, `trust_level`, `is_active`, `attributes`, `metadata` |
| **Action** | `action_id`, `category`, `operation` | `description`, `risk_weight`, `is_reversible`, `requires_confirmation`, `parameters_schema`, `metadata` |
| **Resource** | `resource_id`, `classification`, `name` | `resource_type`, `description`, `owner_actor_id`, `compliance_tags`, `retention_days`, `is_encrypted`, `metadata` |
| **Context** | `context_id`, `session_id`, `timestamp` | `user_intent`, `environment`, `temporal`, `behavioral`, `prior_decisions`, `custom` |
| **Risk** | `risk_id`, `decision_id`, `overall_score`, `timestamp` | `risk_level`, `dimensions`, `likelihood`, `impact`, `factors`, `mitigations_applied`, `metadata` |
| **Compliance Control** | `control_id`, `framework`, `control_ref`, `name` | `description`, `category`, `policy_mappings`, `evidence_requirements`, `test_procedure`, `is_active`, `metadata` |
| **Override** | `override_id`, `decision_id`, `override_type`, `authorized_by`, `justification`, `timestamp` | `original_outcome`, `new_outcome`, `expires_at`, `scope`, `review_required_by`, `evidence_ids`, `metadata` |
| **Escalation** | `escalation_id`, `decision_id`, `trigger`, `escalated_to`, `status`, `created_at` | `priority`, `sla_deadline`, `acknowledged_at`, `acknowledged_by`, `resolved_at`, `resolution`, `context_summary`, `metadata` |
| **Evidence Artifact** | `artifact_id`, `artifact_type`, `sha256_hash`, `created_at`, `source` | `content_type`, `size_bytes`, `storage_uri`, `related_decision_ids`, `related_control_ids`, `digital_signature`, `retention_until`, `is_immutable`, `metadata` |

---

## 6. Extensibility Guidelines

### 6.1 Adding Custom Fields

All primitives include a `metadata` object for custom fields:

```json
{
  "metadata": {
    "custom_field_1": "value",
    "org_specific": { "department": "engineering" }
  }
}
```

### 6.2 Extending Enums

When adding new enum values:
1. Add to schema with backwards-compatible default
2. Update all UI components that render the enum
3. Add migration for existing records if needed
4. Document in changelog

### 6.3 Version Compatibility

- Schema versions follow semantic versioning
- Breaking changes require major version bump
- All exports include schema version for parsing

---

## 7. Audit Defensibility Checklist

For each governed action, ensure:

- [ ] **Decision recorded** with all required fields
- [ ] **Policy version** captured at decision time
- [ ] **Actor identity** verified and logged
- [ ] **Context snapshot** preserved with decision
- [ ] **Risk assessment** attached if score > threshold
- [ ] **Evidence artifacts** generated and hashed
- [ ] **Override justification** documented if applicable
- [ ] **Escalation trail** complete if routed to human
- [ ] **Timestamps** use UTC with timezone indicator
- [ ] **Immutability** enforced post-finalization

---

*Document maintained by Lexecon Governance Team*
