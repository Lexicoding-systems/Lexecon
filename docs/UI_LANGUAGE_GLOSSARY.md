# UI Language Glossary

## Purpose

This glossary defines approved human-centered language for Lexecon UI elements. It implements the calm-first, intervention-budget-aware principles from `docs/HUMAN_CENTERED_GOVERNANCE_UX.md`.

---

## Core Principles

1. **Calm-first**: Default to quiet, reserve urgency for genuine need
2. **Action-oriented**: Tell users what to do, not just what's wrong
3. **Context-rich**: Explain why, not just what
4. **Honest limitations**: State what we don't know
5. **Avoid false authority**: Use "evidence shows" not "the system guarantees"

---

## Approved Terminology

### Risk Assessment

| Use | Avoid | Rationale |
|-----|-------|-----------|
| Risk score | Threat level | "Score" is neutral; "threat" implies adversary |
| High risk detected | DANGER / CRITICAL | Calm language for serious situations |
| Uncertainty: 0.45 | Confidence: low | Explicit about what we don't know |
| Exceeds threshold | Violates policy | "Exceeds" is factual; "violates" is judgmental |
| Requires review | Blocked pending approval | Focus on action needed |

### Escalations

| Use | Avoid | Rationale |
|-----|-------|-----------|
| Pending review | Awaiting approval | "Review" is broader than "approval" |
| Assigned to [name] | Escalated to [name] | Less alarming; same meaning |
| Resolution needed | Action required | "Needed" softer than "required" |
| Review by [date] | URGENT: Must act by [date] | State deadline calmly |
| No similar cases found | This is unprecedented | Factual, not dramatic |

### Overrides

| Use | Avoid | Rationale |
|-----|-------|-----------|
| Override | Bypass / Circumvent | Neutral term for legitimate action |
| Authorized exception | Policy violation override | Emphasize legitimacy |
| Justification required | Explain why you're doing this | Professional, not accusatory |
| Active for [duration] | Expires in [duration] | Positive framing |
| Recorded for audit | This will be logged | Transparency without threat |

### Evidence & Audit

| Use | Avoid | Rationale |
|-----|-------|-----------|
| Evidence artifact | Proof / Attestation | "Evidence" is neutral |
| Hash verified | Tamper-proof / Secure | Factual statement |
| Integrity check passed | No tampering detected | Positive phrasing |
| Linked to decision [id] | Proves decision [id] | "Linked" is factual |
| Audit package ready | Compliance export complete | Neutral terminology |

### Compliance

| Use | Avoid | Rationale |
|-----|-------|-----------|
| Control mapping | Compliance proof | We map, don't certify |
| Evidence supports control | Satisfies requirement | Evidence-based language |
| Coverage: 67% | 67% compliant | Coverage is measurable |
| No evidence for control | Control not implemented | Evidence absence ≠ non-implementation |
| Framework alignment | Compliance certification | Honest about scope |

---

## Forbidden Phrases

### False Certainty
- ❌ "Guaranteed compliant"
- ❌ "100% secure"
- ❌ "Certified for [regulation]"
- ❌ "Meets all requirements"
- ❌ "Eliminates risk"

### Unnecessarily Alarming
- ❌ "CRITICAL FAILURE"
- ❌ "IMMEDIATE ACTION REQUIRED"
- ❌ "SYSTEM COMPROMISED"
- ❌ "VIOLATION DETECTED"
- ❌ "EMERGENCY OVERRIDE"

### Vague or Unhelpful
- ❌ "An error occurred"
- ❌ "Something went wrong"
- ❌ "Invalid input"
- ❌ "Contact administrator"
- ❌ "Please try again"

---

## Microcopy Examples

### Alert Notifications

**High-Risk Decision**
```
✓ High risk detected (score: 0.87)
Review recommended before proceeding

[View Context] [Assign Reviewer]
```

**Escalation Created**
```
✓ Assigned to Alice for review
Expected response by Jan 4, 4:00 PM

[View Details]
```

**Override Active**
```
✓ Override authorized by Carol
Active for 1 hour (expires 1:30 PM)

[View Justification]
```

---

### Empty States

**No Escalations**
```
No items need review

All decisions within risk thresholds
```

**No Evidence**
```
No evidence artifacts for this period

Try expanding the date range
```

**No Overrides**
```
No active overrides

All decisions following standard workflow
```

---

### Error Messages

**Missing Required Field**
```
Justification required for overrides

This helps maintain audit trail clarity.
Minimum 50 characters.
```

**Action Not Authorized**
```
Override requires authorization level: L3

Your current level: L2
Contact team lead to request this action
```

**Export Generation Failed**
```
Export generation incomplete

Missing data for 3 decisions in selected range.
Try narrowing date range or contact support.
```

---

### Success Confirmations

**Escalation Resolved**
```
✓ Escalation resolved

Decision approved with justification recorded.
Evidence artifact created: evd_a1b2c3
```

**Override Created**
```
✓ Override authorized

Type: Policy exception
Duration: This decision only
Audit record: ovr_dec_x9y8z7
```

**Export Complete**
```
✓ Audit package ready

Format: JSON
Period: Jan 1-4, 2026
Size: 247 KB

[Download] [Verify Integrity]
```

---

### Loading States

**Generating Export**
```
Preparing audit package...

This may take 30-60 seconds for large datasets.
```

**Verifying Integrity**
```
Checking hash chain...

Verifying 156 artifacts.
```

**Loading Dashboard**
```
Loading recent activity...
```

---

## Status Indicators

### Risk Levels

| Level | Color | Icon | Label Text |
|-------|-------|------|------------|
| LOW | Green | ✓ | Low risk |
| MEDIUM | Yellow | ● | Medium risk |
| HIGH | Orange | ⚠ | High risk - review recommended |
| CRITICAL | Red | ⚠ | Critical risk - review required |

### Escalation Status

| Status | Color | Icon | Label Text |
|--------|-------|------|------------|
| PENDING | Blue | ○ | Pending review |
| IN_PROGRESS | Blue | ◐ | In progress |
| RESOLVED | Green | ✓ | Resolved |
| TIMED_OUT | Red | ⊗ | Review deadline passed |

### Override Status

| Status | Color | Icon | Label Text |
|--------|-------|------|------------|
| ACTIVE | Orange | ● | Active |
| EXPIRED | Gray | ○ | Expired |
| REVOKED | Red | ⊗ | Revoked |

---

## Button Labels

### Primary Actions
- "Approve" (not "Accept" or "Allow")
- "Reject" (not "Deny" or "Block")
- "Review" (not "Inspect" or "Check")
- "Create Override" (not "Bypass" or "Force")
- "Generate Export" (not "Create Report")

### Secondary Actions
- "View Details" (not "More Info")
- "View Context" (not "See Reason")
- "View Justification" (not "See Explanation")
- "Assign Reviewer" (not "Escalate")
- "Download" (not "Export" or "Save")

### Tertiary Actions
- "Cancel"
- "Back"
- "Close"
- "Dismiss"
- "Skip"

---

## Form Field Labels

### Required Context
Always include help text for non-obvious fields:

```
Justification *
Why is this override necessary?
Minimum 50 characters required for audit trail.
```

### Optional Fields
Mark optional fields explicitly:

```
Additional Context (optional)
Any supplementary information for reviewers.
```

### Date/Time Fields
Use clear formats:

```
Start Date
Format: YYYY-MM-DD (e.g., 2026-01-04)
```

---

## Accessibility Notes

All UI text must:
- Have sufficient color contrast (WCAG AA minimum)
- Not rely solely on color to convey meaning (use icons + text)
- Provide ARIA labels for screen readers
- Use semantic HTML for structure

Example ARIA label:
```html
<button aria-label="Approve escalation ESC-2847">
  Approve
</button>
```

---

## Implementation Guidelines

### For Developers

1. Check this glossary before writing UI text
2. Use approved terminology consistently
3. Keep messages concise (< 140 characters if possible)
4. Always provide context for actions
5. Test all microcopy with realistic data

### For Designers

1. Reserve red/urgent styling for genuine critical states
2. Use neutral colors (blue, gray) for normal operations
3. Ensure all status indicators have both color and icon
4. Test UI in high-contrast mode
5. Validate accessibility with screen reader

### For Product Managers

1. Review all new UI text against glossary
2. Question any "compliance" or "certified" language
3. Push back on unnecessary urgency
4. Ensure empty states are helpful, not just blank
5. Validate error messages provide actionable guidance
