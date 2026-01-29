# Policy Engine Conformance Specification

**Version:** 1.0.0  
**Date:** 2026-01-29  
**Status:** Final

---

## 1. Scope

This document specifies the canonical behavior of the Lexecon Policy Engine for conformance testing and third-party implementations.

---

## 2. Policy Modes

### 2.1 STRICT Mode (Default)
- **Behavior:** Deny unless explicitly permitted
- **Use Case:** Production systems, high-risk environments
- **Evaluation Rules:**
  1. If any `forbids` relation matches → DENY
  2. If any `permits` relation matches → ALLOW
  3. Otherwise → DENY

### 2.2 PERMISSIVE Mode
- **Behavior:** Allow unless explicitly forbidden
- **Use Case:** Development, testing environments
- **Evaluation Rules:**
  1. If any `forbids` relation matches → DENY
  2. Otherwise → ALLOW

### 2.3 PARANOID Mode
- **Behavior:** Deny high-risk without explicit confirmation
- **Use Case:** Critical systems, regulatory compliance
- **Evaluation Rules:**
  1. Same as STRICT
  2. Risk level ≥ 80 requires human confirmation

---

## 3. Relation Precedence

```
forbids > permits > default
```

A `forbids` relation always takes precedence over a `permits` relation for the same actor/action pair.

---

## 4. Canonical Test Cases

### 4.1 Basic Evaluation

| Test | Mode | Actor | Action | Relations | Expected |
|------|------|-------|--------|-----------|----------|
| TC-001 | STRICT | unknown | unknown | (none) | DENY |
| TC-002 | PERMISSIVE | unknown | unknown | (none) | ALLOW |
| TC-003 | STRICT | user | read | permits(user, read) | ALLOW |
| TC-004 | STRICT | user | delete | forbids(user, delete) | DENY |
| TC-005 | STRICT | user | mixed | permits + forbids | DENY |

### 4.2 Determinism Requirements

- Policy hash must be identical for identical policy content
- Evaluation result must be identical for identical inputs
- Hash must change when policy is modified

### 4.3 Term Identifier Format

- Actors: `actor:{name}` or `act_{name}`
- Actions: `action:{name}` or `axn_{name}`
- Resources: `resource:{name}` or `res_{name}`
- Data Classes: `data:{name}` or `data_{name}`

---

## 5. Conformance Validation

Implementations must pass all test cases in `tests/test_policy.py` and `tests/test_coverage_comprehensive.py`.

---

## 6. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-29 | Initial specification |
