# Human-Centered Governance UX

## Design Philosophy

Lexecon's governance UX is built on a fundamental insight: **effective AI oversight requires humans who are alert, informed, and empowered—not exhausted, overwhelmed, or disengaged.**

The system is designed to preserve human cognitive resources for decisions that genuinely require human judgment, while providing the context needed to make those decisions well.

---

## Core Principles

### 1. Calm-First Design

The governance interface defaults to quiet. Notifications, alerts, and interventions are the exception, not the norm.

```
┌─────────────────────────────────────────────────────────────────┐
│                     CALM-FIRST HIERARCHY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Level 0: Silent Operation (default)                            │
│  ├── System operating within parameters                        │
│  ├── No visual interruption                                    │
│  └── Metrics available on-demand                               │
│                                                                 │
│  Level 1: Ambient Awareness                                     │
│  ├── Subtle status indicators                                  │
│  ├── Dashboard updates without alerts                          │
│  └── Trend visualization                                       │
│                                                                 │
│  Level 2: Passive Notification                                  │
│  ├── Badge counts on dashboard                                 │
│  ├── Email summaries (configurable frequency)                  │
│  └── Log entries for audit                                     │
│                                                                 │
│  Level 3: Active Notification                                   │
│  ├── In-app alerts requiring acknowledgment                    │
│  ├── Push notifications (if enabled)                           │
│  └── Escalation to designated reviewers                        │
│                                                                 │
│  Level 4: Blocking Intervention                                 │
│  ├── Modal requiring human decision                            │
│  ├── System pause until resolved                               │
│  └── Multiple notification channels                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Design Rationale**: Most AI system activity is routine. A governance system that alerts on everything trains humans to ignore alerts. By reserving interruptions for genuine decision points, we preserve the human's ability to respond effectively when it matters.

### 2. Progressive Disclosure

Information is revealed in layers, matching the user's current task and expertise level.

```
Layer 1: Summary View
┌──────────────────────────────────────────────────┐
│ ESCALATION #ESC-2847                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Status: Pending Review                           │
│ Risk Level: HIGH (0.87)                          │
│ Trigger: Output toxicity threshold exceeded      │
│                                                  │
│ [View Details] [Approve] [Reject] [Escalate]    │
└──────────────────────────────────────────────────┘

Layer 2: Context View (on "View Details")
┌──────────────────────────────────────────────────┐
│ ESCALATION CONTEXT                               │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Decision ID: dec_a1b2c3d4                        │
│ Timestamp: 2026-01-04T12:34:56Z                  │
│                                                  │
│ Risk Assessment:                                 │
│ ├── Toxicity Score: 0.87 (threshold: 0.70)      │
│ ├── Confidence: 0.92                             │
│ └── Model: content-safety-v2                     │
│                                                  │
│ Similar Past Decisions: 3 approved, 1 rejected   │
│                                                  │
│ [View Full Audit Trail] [View Similar Cases]     │
└──────────────────────────────────────────────────┘

Layer 3: Full Audit Trail (on request)
┌──────────────────────────────────────────────────┐
│ COMPLETE DECISION HISTORY                        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ [Full timeline with all evidence artifacts,      │
│  risk scores, model outputs, and previous        │
│  human interventions in this decision chain]     │
└──────────────────────────────────────────────────┘
```

**Design Rationale**: Experts need access to full detail. Non-experts need actionable summaries. The same interface serves both by revealing complexity only when requested.

### 3. Intervention Budget

The system tracks and protects human cognitive capacity as a finite resource.

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTERVENTION BUDGET MODEL                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Daily Budget: 20 interruptions per reviewer                    │
│  ├── Critical (blocks workflow): max 3/day                     │
│  ├── High (requires same-day response): max 7/day              │
│  ├── Medium (requires 48h response): max 10/day                │
│  └── Overflow: queued or auto-routed                           │
│                                                                 │
│  Budget Enforcement:                                            │
│  ├── Near-limit: escalations routed to backup reviewers        │
│  ├── At-limit: only critical items interrupt                   │
│  └── Over-limit: auto-escalate to team lead + alert            │
│                                                                 │
│  Budget Recovery:                                               │
│  ├── Resolved items restore partial budget                     │
│  ├── Batch processing encouraged for similar items             │
│  └── Deferred items don't count against daily budget           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Configuration Example**:
```python
InterventionBudget(
    reviewer_id="reviewer_alice",
    daily_limits={
        "critical": 3,
        "high": 7,
        "medium": 10,
        "low": float("inf")  # No limit on low-priority
    },
    recovery_rate=0.5,  # Resolving an item restores 50% of its cost
    overflow_behavior="route_to_backup",
    backup_reviewers=["reviewer_bob", "team_lead_carol"]
)
```

**Design Rationale**: Alert fatigue is a real phenomenon that degrades oversight quality. By explicitly budgeting interventions, the system forces prioritization and prevents the cognitive exhaustion that leads to rubber-stamping.

---

## UX Patterns by Domain

### Alert UX

Alerts are the primary mechanism for bringing items to human attention. Their design directly impacts oversight effectiveness.

#### Alert Anatomy

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠ HIGH RISK DECISION REQUIRES REVIEW                    12:34 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Decision: Content generation for user request                  │
│  Risk Score: 0.84 (HIGH)                                        │
│                                                                 │
│  Why This Alert:                                                │
│  └── Toxicity score (0.84) exceeds threshold (0.70)            │
│                                                                 │
│  Recommended Action: Review output before delivery              │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐   │
│  │   Approve   │ │   Reject    │ │  Request More Context   │   │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘   │
│                                                                 │
│  [Snooze 1h] [Delegate] [View Full Context]                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Alert Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Explain the trigger** | "Why This Alert" section explains what threshold was crossed |
| **Suggest action** | Recommended action based on similar past decisions |
| **Enable quick resolution** | Primary actions visible without scrolling |
| **Allow deferral** | Snooze and delegate options for non-critical items |
| **Support investigation** | "View Full Context" for deeper analysis |

#### Alert Batching

Related alerts are grouped to reduce interruption count:

```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 BATCH REVIEW: 5 Similar Escalations                   12:34 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Common Pattern: Content safety threshold (toxicity)            │
│  Risk Range: 0.71 - 0.84                                        │
│  Time Range: Last 2 hours                                       │
│                                                                 │
│  Quick Actions:                                                 │
│  ┌───────────────────┐ ┌───────────────────┐                   │
│  │   Approve All     │ │   Review Each     │                   │
│  └───────────────────┘ └───────────────────┘                   │
│                                                                 │
│  Items:                                                         │
│  ├── ESC-2847: Score 0.84 [Approve] [Reject]                   │
│  ├── ESC-2848: Score 0.78 [Approve] [Reject]                   │
│  ├── ESC-2849: Score 0.75 [Approve] [Reject]                   │
│  ├── ESC-2850: Score 0.73 [Approve] [Reject]                   │
│  └── ESC-2851: Score 0.71 [Approve] [Reject]                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Escalation UX

Escalations require human judgment on AI system decisions. The UX must provide sufficient context for informed decisions without overwhelming.

#### Escalation Queue

```
┌─────────────────────────────────────────────────────────────────┐
│ ESCALATION QUEUE                                    Alice (12) │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Filter: [All ▼] [Pending ▼] [Last 24h ▼]    Sort: [Priority ▼]│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🔴 CRITICAL  ESC-2852  Content Policy Violation   2m ago   ││
│  │    Auto-blocked output requires human release               ││
│  │    [Review Now]                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🟠 HIGH      ESC-2847  Toxicity Threshold         15m ago  ││
│  │    Score 0.84 exceeds 0.70 threshold                        ││
│  │    [Review] [Batch with Similar]                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🟡 MEDIUM    ESC-2840  Uncertainty High           1h ago   ││
│  │    Model confidence 0.45 below threshold 0.60               ││
│  │    [Review] [Defer to Expert]                               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Showing 3 of 12 pending                          [Load More]  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Escalation Resolution

```
┌─────────────────────────────────────────────────────────────────┐
│ RESOLVE ESCALATION ESC-2847                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Your Decision:                                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ○ APPROVE - Allow the original decision to proceed         ││
│  │   └── The content is acceptable despite the score          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ○ REJECT - Block the original decision                     ││
│  │   └── The content should not be delivered                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ○ MODIFY - Approve with conditions                         ││
│  │   └── Requires specifying modifications                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ○ ESCALATE FURTHER - Send to higher authority              ││
│  │   └── Beyond my authorization level                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Justification (required for REJECT/MODIFY):                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                             ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [ ] Apply this decision to similar pending escalations (4)    │
│                                                                 │
│                              [Cancel] [Submit Decision]         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Override UX

Overrides are exceptional interventions that bypass normal system behavior. The UX emphasizes the gravity of the action while enabling legitimate use cases.

#### Override Request Flow

```
Step 1: Initiate Override
┌─────────────────────────────────────────────────────────────────┐
│ REQUEST OVERRIDE                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⚠ Overrides bypass normal governance controls.                │
│    This action will be logged and audited.                     │
│                                                                 │
│  Decision to Override: dec_a1b2c3d4                             │
│  Current Status: BLOCKED (toxicity threshold)                   │
│                                                                 │
│  Override Type:                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ○ POLICY - Override specific policy rule                   ││
│  │ ○ RISK_ACCEPTANCE - Accept identified risk                 ││
│  │ ○ EMERGENCY - Time-critical bypass (requires justification)││
│  │ ○ TESTING - Development/testing purposes only              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│                                              [Cancel] [Next →] │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Step 2: Provide Justification
┌─────────────────────────────────────────────────────────────────┐
│ OVERRIDE JUSTIFICATION                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Why is this override necessary?                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ The content discusses historical violence in an            ││
│  │ educational context. The toxicity score is triggered       ││
│  │ by quoted historical text, not generated harmful content.  ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│  Minimum 50 characters required (142/50)                        │
│                                                                 │
│  Duration:                                                      │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ○ This decision only                                      │ │
│  │ ○ 1 hour   ○ 24 hours   ○ 7 days   ○ Custom...           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│                                        [← Back] [Submit Override]│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Step 3: Confirmation (for high-impact overrides)
┌─────────────────────────────────────────────────────────────────┐
│ ⚠ CONFIRM OVERRIDE                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  You are about to create an override that:                      │
│                                                                 │
│  • Bypasses: Content safety policy (toxicity threshold)        │
│  • Affects: 1 decision                                          │
│  • Duration: This decision only                                 │
│  • Audit: This action will be permanently logged                │
│                                                                 │
│  To confirm, type "OVERRIDE" below:                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│                                       [Cancel] [Confirm Override]│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Override Audit Trail

Every override is permanently recorded with full context:

```
┌─────────────────────────────────────────────────────────────────┐
│ OVERRIDE RECORD OVR-1847                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Created: 2026-01-04T12:45:23Z                                  │
│  Created By: alice@example.com                                  │
│  Status: ACTIVE                                                 │
│                                                                 │
│  Target Decision: dec_a1b2c3d4                                  │
│  Override Type: POLICY                                          │
│  Duration: Single decision                                      │
│                                                                 │
│  Justification:                                                 │
│  "The content discusses historical violence in an educational   │
│   context. The toxicity score is triggered by quoted historical │
│   text, not generated harmful content."                         │
│                                                                 │
│  Bypassed Controls:                                             │
│  └── Content safety policy: toxicity threshold (0.70)           │
│                                                                 │
│  Evidence:                                                      │
│  ├── Original decision context                                  │
│  ├── Risk assessment at time of override                        │
│  └── Reviewer acknowledgment                                    │
│                                                                 │
│  Audit Chain:                                                   │
│  └── Linked to: ESC-2847, dec_a1b2c3d4, risk_5678              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Audit UX

The audit interface serves compliance officers, auditors, and investigators who need to reconstruct decision histories.

#### Audit Export Wizard

```
┌─────────────────────────────────────────────────────────────────┐
│ CREATE AUDIT EXPORT                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1 of 3: Define Scope                                      │
│                                                                 │
│  Export Type:                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ○ Complete Audit Packet (all governance data)              ││
│  │ ○ Risk Assessments Only                                    ││
│  │ ○ Escalations Only                                         ││
│  │ ○ Overrides Only                                           ││
│  │ ○ Compliance Mapping Only                                  ││
│  │ ○ Custom Selection...                                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Date Range:                                                    │
│  ┌──────────────────┐  to  ┌──────────────────┐                │
│  │ 2026-01-01      │      │ 2026-01-04      │                │
│  └──────────────────┘      └──────────────────┘                │
│                                                                 │
│  [ ] Include deleted records                                    │
│                                                                 │
│                                              [Cancel] [Next →] │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Audit Verification

```
┌─────────────────────────────────────────────────────────────────┐
│ VERIFY AUDIT PACKET                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Packet: audit_export_2026-01-04_exp_abc123.zip                 │
│                                                                 │
│  Verification Results:                                          │
│                                                                 │
│  ✓ Manifest integrity verified                                  │
│  ✓ Root checksum matches (SHA-256)                              │
│  ✓ All artifact checksums verified (156/156)                    │
│  ✓ Evidence chain complete                                      │
│  ✓ No tampering detected                                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ✓ PACKET INTEGRITY VERIFIED                                ││
│  │   This audit packet has not been modified since generation.││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Packet Statistics:                                             │
│  ├── Decisions: 156                                             │
│  ├── Risk Assessments: 23                                       │
│  ├── Escalations: 8                                             │
│  ├── Overrides: 3                                               │
│  └── Evidence Artifacts: 42                                     │
│                                                                 │
│                                           [View Contents] [Close]│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Human Safety Considerations

### Cognitive Load Management

| Risk | Mitigation |
|------|------------|
| Alert fatigue | Intervention budgets, batching, priority routing |
| Decision fatigue | Progressive disclosure, recommended actions, batch approval |
| Information overload | Layered detail, summary-first views |
| Time pressure | SLA visibility, delegation options, async workflows |

### Error Prevention

| Risk | Mitigation |
|------|------------|
| Accidental approval | Confirmation for high-impact decisions |
| Misunderstanding context | Mandatory context display, similar case comparison |
| Overlooking critical items | Visual priority hierarchy, critical item highlighting |
| Inconsistent decisions | Decision history, pattern matching, policy references |

### Accountability Support

| Requirement | Implementation |
|-------------|----------------|
| Decision traceability | Every action linked to actor and timestamp |
| Justification capture | Required justification for consequential decisions |
| Audit trail access | Self-service access to personal decision history |
| Escalation paths | Clear routes for uncertain or high-stakes decisions |

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance

All governance interfaces MUST meet WCAG 2.1 AA standards:

- **Perceivable**: Color is not the only indicator of priority; text alternatives for all visual indicators
- **Operable**: Full keyboard navigation; no time limits that cannot be extended
- **Understandable**: Consistent navigation; error identification with suggestions
- **Robust**: Compatible with assistive technologies; valid HTML

### Additional Considerations

- **Screen reader optimization**: ARIA labels for all interactive elements
- **High contrast mode**: All interfaces functional in high contrast
- **Reduced motion**: Respect `prefers-reduced-motion` for animations
- **Focus management**: Logical focus order; visible focus indicators

---

## Dashboard Standards

### Information Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                     GOVERNANCE DASHBOARD                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRIMARY ZONE (Requires Immediate Attention)                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🔴 3 Critical Escalations    🟠 7 High Priority Items      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  SECONDARY ZONE (Status Overview)                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Risk Score Trend ▼   │ Escalation Rate   │ Override Count  ││
│  │ [Sparkline Graph]    │ [Sparkline Graph] │ 3 this week     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  TERTIARY ZONE (Detailed Metrics)                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ [Compliance Status] [Control Coverage] [Audit Readiness]   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Real-Time Updates

- Dashboard refreshes automatically (configurable interval, default 30s)
- New items appear with subtle animation (respects reduced motion preference)
- Count badges update without full page refresh
- Connection status indicator for real-time features

### Personalization

- Configurable widget arrangement
- Saved filter preferences
- Custom alert thresholds per user
- Role-based default views

---

## Implementation Guidelines

### For Developers

1. **Always show context**: Never ask for a decision without showing why it's needed
2. **Default to less intrusive**: Use passive notifications unless active response required
3. **Support batch operations**: Similar items should be resolvable together
4. **Preserve undo capability**: Where possible, decisions should be reversible
5. **Log everything**: Every user action in governance UI must be auditable

### For Designers

1. **Lead with the action**: Primary action should be immediately visible
2. **Use progressive disclosure**: Details available but not overwhelming
3. **Maintain consistency**: Same action, same appearance across all contexts
4. **Design for worst case**: Interface must work under high load conditions
5. **Test with real scenarios**: Validate with actual governance workflows

### For Product Managers

1. **Measure intervention rate**: Track how often humans are interrupted
2. **Monitor resolution time**: How long do decisions take?
3. **Track escalation patterns**: Are thresholds appropriately calibrated?
4. **Survey user satisfaction**: Is the system helping or hindering?
5. **Audit decision quality**: Are human decisions consistent and well-reasoned?
