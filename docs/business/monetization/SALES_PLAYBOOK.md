# 📞 LEXECON SALES PLAYBOOK
## Enterprise B2B Sales Execution Guide

**Document Type:** Internal Sales Enablement  
**Target:** Founding Sales, Account Executives, SDRs  
**Use Case:** Closing $5K-500K/year enterprise deals  

---

## 📋 TABLE OF CONTENTS

1. [Sales Process Overview](#sales-process-overview)
2. [Tier 3: Enterprise Starter ($5-15K)](#tier-3-enterprise-starter)
3. [Tier 4: Enterprise Platform ($25-75K)](#tier-4-enterprise-platform)
4. [Tier 5: Enterprise Global ($150-500K)](#tier-5-enterprise-global)
5. [Objection Handling](#objection-handling)
6. [Demo Script](#demo-script)
7. [Discovery Questions](#discovery-questions)
8. [ROI Framework](#roi-framework)
9. [Competitive Intelligence](#competitive-intelligence)

---

## 🎯 SALES PROCESS OVERVIEW

### Universal Stages (All Tiers)

```
Lead → Qualified → Demo → POC → Proposal → Negotiation → Closed Won
  ↓         ↓         ↓      ↓        ↓           ↓           ↓
Touch  BANT    Tech Fit  Value   Pricing   Legal/Proc   Signed
```

**Stage Definitions:**

**Lead:** Any contact expressing interest  
**Qualified:** Meets BANT (Budget, Authority, Need, Timeline)  
**Demo:** Product demonstration (customized to their use case)  
**POC:** Proof of concept (paid or unpaid trial)  
**Proposal:** Formal pricing and scope  
**Negotiation:** Contract terms, security review  
**Closed Won:** Signed contract + first payment

**Conversion Rates:**
- Lead → Qualified: 30%
- Qualified → Demo: 60%
- Demo → POC: 40%
- POC → Proposal: 70%
- Proposal → Closed: 60%

**Overall:** Lead → Closed = 3% (enterprise standard)

---

## 💼 TIER 3: ENTERPRISE STARTER ($5-15K/year)

### Ideal Customer Profile

**Company:**
- Size: 200-2,000 employees
- Stage: Growth or mature
- Industry: Tech, AI, mid-size finance/healthcare
- Tech stack: Modern (cloud-native, API-driven)

**Buyer Persona:**
- **Primary:** CTO, VP Engineering, Head of AI
- **Age:** 35-50
- **Motivation:** Risk mitigation, compliance, efficiency
- **Pain:** "We're deploying AI but don't have governance"
- **Budget:** $5-50K/year (approved by them)
- **Urgency:** Medium (6-12 month timeline)

**Use Cases:**
- Internal AI tools (ChatGPT, copilots)
- Customer-facing AI features
- SOC 2 audit preparation
- EU AI Act compliance

### Sales Process (2-4 weeks)

**Day 1-2: Lead Qualification**

**Sources:**
- Inbound (website, open source users)
- LinkedIn outreach (SDR)
- Referrals
- Events

**Qualification Call (30 min):**

```
**Agenda:**
1. Introduction (5 min)
2. Current state (10 min)
3. Pain points (10 min)
4. Solution fit (5 min)
5. Next steps (5 min)

**Key Questions:**
- Walk me through your current AI deployment
- How many autonomous systems do you have?
- What's your current governance approach?
- Are you facing any compliance requirements (EU AI Act, SOC2)?
- What's your biggest governance fear?
- Who else needs to be involved in this decision?
- What's your budget range for governance tools?
- What's your timeline for implementation?

**Qualification Criteria:**
✓ 200+ employees
✓ Deploying AI systems (or planning to)
✓ Budget $5K+
✓ Timeline <6 months
✓ Technical buyer identified

**Next Step:** Schedule technical demo
```

**Day 3-5: Technical Demo (45 min)**

```
**Agenda:**
1. Problem recap (5 min) - show you listened
2. Lexecon overview (10 min) - architecture
3. Live demo (20 min) - THEIR use case
4. Q&A (10 min)
5. Next steps (5 min)

**Demo Flow:**
"Let me show you how Lexecon would work for YOUR [use case]..."

1. **Policy Definition:**
```python
# Show their policy in Lexecon
policy = PolicyEngine()
policy.add_rule("trading_limit", {"max_daily": 1000000})
policy.add_rule("human_approval", {"requires": "senior_trader"})
```

2. **Decision Flow:**
```python
# Show real-time decision
decision = governance.evaluate(
    actor="algo_trading_bot",
    action="place_order",
    amount=500000
)
# Result: APPROVED (in 8ms)
```

3. **Audit Trail:**
```python
# Show tamper-proof log
ledger = Ledger(tenant_id)
for decision in ledger.recent(limit=10):
    print(f"{decision.timestamp}: {decision.action} → {decision.outcome}")
```

4. **Compliance Report:**
```python
# Generate EU AI Act report
report = EUAIActReport(tenant_id, period="2024-Q1")
report.export("eu_ai_act_q1.pdf")
```

**Key Demo Tips:**
- Pre-load their scenario (ask ahead of time)
- Show both APPROVED and DENIED decisions
- Show the cryptographic signature verification
- Have compliance report pre-generated
- Keep it under 45 minutes

**Next Step:** Proposal + Security review
```

**Day 6-10: Security Review (Async)**

**Materials to Send:**
- Security whitepaper
- Architecture diagram
- Compliance mapping (relevant frameworks)
- Penetration test report (when you have it)
- SOC 2 Type II (when you have it)

**Common Questions:**
- "Where is data stored?" → AWS/Azure/GCP, customer choice
- "Is data encrypted?" → At rest (AES-256) + in transit (TLS 1.3)
- "Can we audit the code?" → Open source core, enterprise full audit
- "What happens if you go out of business?" → Source code escrow (Tier 4+)
- "Who has access to our data?" → Only named admins (logged)

**Next Step:** POC (if security approved)

**Day 11-20: POC (Optional, 1-2 weeks)**

**POC Structure:**
- **Duration:** 1 week (free) or 2 weeks ($5K)
- **Scope:** 1-2 systems, 1 policy set
- **Success Criteria:**
  - <10ms latency (p99)
  - 100% audit completeness
  - 50% reduction in compliance time
- **Cost:** Free (risk) vs $5K (commitment signal)

**POC Setup:**
```bash
# Provision isolated environment
export TENANT_ID="corp_xyz_poc"
export ENV="poc"
./scripts/provision_tenant.sh

# Customer integrates 1-2 systems
curl -X POST https://api.lexecon.com/v1/decisions \
  -H "X-API-Key: $POC_API_KEY" \
  -d '{"actor": "bot", "action": "trade", "params": {"amount": 100000}}'

# Daily check-ins (15 min)
# Weekly reviews (45 min)
```

**POC Success:**
- Customer confirms: "This solves our problem"
- Champion identified (internal advocate)
- Technical validation complete
- Budget confirmed

**Next Step:** Proposal

**Day 21-24: Proposal**

**Format:**
- Order Form (1 page)
- Pricing table (clear breakdown)
- Implementation timeline (1-2 weeks)
- Support terms (24hr response)
- SLA (99.5% uptime)

**Pricing Tactics:**
- **Anchor high:** Start with Tier 4 package ($50K)
- **Tier 3 floor:** Don't go below $5K (value preservation)
- **Discounts:** 15% for annual, 20% for 3-year
- **Urgency:** "Pricing increases next quarter"

**Example Proposal:**
```
Lexecon Enterprise Platform
Customer: Acme Corp
Term: 1 year
Start Date: [30 days from signature]

Platform Fee: $50,000/year
  - Includes: Dedicated infrastructure, SSO, 10 integrations
  - Support: Premium (4hr response)
  - Training: 10 employees
  - QBRs: Quarterly business reviews

Implementation: $10,000 one-time
  - Setup: Dedicated cluster
  - Integration: 3 systems
  - Training: 2 sessions

Total Year 1: $60,000

Payment Terms: Annual upfront
```

**Next Step:** Contract negotiation

**Day 25-35: Negotiation & Contract**

**Typical Negotiation Points:**

| Issue | Your Position | Concession |
|-------|---------------|------------|
| Price | $50K list | 15% max discount |
| Payment | Annual upfront | Quarterly (+5%) |
| Term | 1 year | 3 years (+10% discount) |
| SLA | 99.5% uptime | 99.9% (if they pay 20% more) |
| Support | Business hours | 24/7 (Enterprise tier only) |
| Integrations | 3 included | +$5K per additional |

**Contract Documents:**
- Order Form (pricing)
- MSA (Master Service Agreement)
- DPA (Data Processing Agreement)
- SLA Addendum
- Security Addendum

**Red Flags:**
- Unlimited liability (cap at 12 months fees)
- IP indemnification beyond your code (don't)
- Custom features without payment (don't)
- On-premise without services fee (don't)

**Legal Review:**
- Have lawyer review (cost: $500-1000)
- Don't sign without understanding
- Standard changes: OK
- Custom changes: Push back

**Time:** 1-2 weeks (typical)

**Closed Won:**
- Signed Order Form
- First payment received (annual upfront)
- Kickoff call scheduled
- Slack channel created

---

## 🏢 TIER 4: ENTERPRISE PLATFORM ($25-75K/year)

### Differences from Tier 3

**Longer Sales Cycle:** 4-8 weeks (vs 2-4 weeks)
**More Stakeholders:** 5-8 (vs 2-3)
**More Complex:** Custom integrations, compliance needs
**Higher Touch:** Dedicated CSM, premium support

### Additional Stakeholders

**Technical Buyer:** CTO, VP Engineering  
**Security Buyer:** CISO, Security Architect  
**Compliance Buyer:** Chief Compliance Officer, General Counsel  
**Economic Buyer:** CFO (final sign-off)

### Discovery (60 min)

**Expanded Questions:**

**Technical:**
- "Walk me through your architecture"
- "How many systems need governance?"
- "What's your current audit approach?"
- "Any custom integrations needed?"
- "Performance requirements? (latency, throughput)"

**Security:**
- "What's your security review process?"
- "Penetration testing requirements?"
- "Data residency requirements?"
- "On-premise or cloud?"
- "MFA requirements?"

**Compliance:**
- "Which regulations apply?"
- "Current audit frequency?"
- "Audit costs today?"
- "Findings in last audit?"
- "Compliance team size?"

**Economic:**
- "Current compliance spending?"
- "Budget allocation?"
- "CFO priorities this year?"
- "ROI requirements?"

### POC (Required for Tier 4)

**Duration:** 2-4 weeks  
**Cost:** $5K-15K (signals commitment)  
**Scope:** Broader (3-5 systems, 2-3 policies)

**POC Structure:**
```python
# Week 1: Integration
- Customer env setup
- Integrate 3 systems
- Write 2 policy sets
- Acceptance testing

# Week 2: Validation
- Run live traffic (5-10%)
- Measure latency
- Generate compliance report
- Train admin users

# Week 3: Expansion (if 4-week POC)
- Add 2 more systems
- Custom compliance mapping
- Stress testing

# Week 4: Evaluation
- Report to stakeholders
- ROI calculation
- Success criteria validation
- Go/No-Go decision
```

**Success Criteria:**
- Performance: <10ms latency (p99)
- Uptime: 99.5%+ during POC
- Adoption: 3+ systems integrated
- Stakeholder: 5+ users trained
- Compliance: Generate 1 report
- Security: Pass security review

**Deliverable:** POC Report (template provided)

---

## 🏭 TIER 5: ENTERPRISE GLOBAL ($150-500K/year)

### Full-Scale Enterprise Sales

**Sales Cycle:** 3-6 months  
**Team:** Full sales team (AE + SE + SC)  
**Process:** Formal procurement, RFP, legal review  
**Value:** Platform deal, strategic relationship

### Buying Committee (8-12 people)

**Executive Stakeholders:**
- CEO (strategic direction)
- CFO (financial approval)
- Chief Risk Officer (risk mitigation)

**Technical Stakeholders:**
- CTO (architecture)
- CISO (security)
- VP Engineering (implementation)
- VP AI/ML (use cases)

**Operational Stakeholders:**
- Chief Compliance Officer (regulatory)
- General Counsel (contract)
- Head of Procurement (vendor mgmt)
- VP Operations (ongoing mgmt)

**End Users:**
- Security Architects
- ML Engineers
- Compliance Analysts

### RFP Response (If Required)

**Typical RFP Sections:**

1. **Company Information** (10 pages)
   - Financial statements
   - Insurance certificates
   - References
   - Team bios

2. **Technical Requirements** (30 pages)
   - Architecture diagrams
   - Security documentation
   - Scalability proof
   - Integration capabilities

3. **Compliance** (20 pages)
   - Certifications (SOC 2, ISO)
   - Audit reports
   - Compliance mappings
   - Regulatory responses

4. **Commercial** (10 pages)
   - Pricing (redacted)
   - Contract terms
   - SLA commitments
   - Support model

**Response Strategy:**
- Use template (don't start from scratch)
- Answer YES to all *requirements*
- Address *nice-to-haves* selectively
- Submit 1 day before deadline (not early)

**Timeline:**
- RFP Issued: Day 0
- Questions Due: Day 7
- Response Due: Day 21
- Shortlist: Day 28
- Presentation: Day 35
- POC: Days 42-70
- Final Proposal: Day 77
- Negotiation: Days 78-105
- Award: Day 105

**Total:** 15 weeks (3.5 months)

### Executive Presentation (90 min)

**Audience:** CIO, CFO, CRO, Board  
**Focus:** Business value, not technical details

**Structure:**

**Part 1: Business Problem (15 min)**
- Regulatory risk: €20M fines (EU AI Act)
- Reputational risk: AI failures in headlines
- Operational risk: AI systems out of control
- Financial risk: $5M+/year manual compliance

**Part 2: Market Context (10 min)**
- Competitors deploying AI governance
- Regulatory trends (tightening)
- Industry standards emerging
- First-mover advantage

**Part 3: Solution (20 min)**
- Lexecon overview
- Business benefits (not technical)
- ROI: 300-500% payback
- Case study from similar company

**Part 4: Implementation (15 min)**
- Timeline: 3 months
- Resources: 2 FTEs (your team)
- Risk mitigation: Phased rollout
- Success metrics

**Part 5: Financials (20 min)**
- TCO analysis (3-year)
- Cost savings (compliance automation)
- Risk reduction (audit success)
- Competitive advantage

**Part 6: Q&A (10 min)**
- CFO questions (ROI, budget)
- CIO questions (integration, resources)
- CRO questions (risk, compliance)

### Contract Structure (Tier 5)

**Total Contract Value:** $300K-500K/year  
**Term:** 3 years (standard)  
**Payment:** Quarterly or annual

**Components:**

**Platform Fee:** 60% of contract
- Decision engine
- Ledger storage
- Policy management
- API access
- Dashboards

**Professional Services:** 25% of contract
- Implementation: $50K
- Integration: $25K
- Training: $15K
- Quarterly health checks: $10K

**Premium Support:** 15% of contract
- 24/7 support
- 4hr response SLA
- Named CSM
- Quarterly business reviews

**Example:** $500K/year contract
- Platform: $300K
- Services: $125K
- Support: $75K

**Payment Schedule:**
- Year 1: 40% upfront, 20% Q2, 20% Q3, 20% Q4
- Year 2-3: Annual upfront

**Key Terms:**
- **Uptime SLA:** 99.9% (with credits)
- **Support SLA:** 4hr response, 24hr resolution (P1)
- **Trainings:** 2 included per quarter
- **Custom Features:** 40 hrs/quarter included
- **Integrations:** Unlimited (within scope)

---

## 🤔 OBJECTION HANDLING

### Price Objections

**"Too expensive"** (Tier 3)

**Response:**
"I understand budget is tight. Let me ask:

1. What's your current compliance cost per year?
2. How many hours/week on manual audit prep?
3. What's the cost of a failed audit?

[Let them answer]

Our typical customer sees 300-500% ROI in first year. 

**Options:**
- Start with Tier 2 ($99/mo) to prove value
- Annual discount (save 15%)
- Start with 1 system (reduce scope)

Would either of those work?"

**"We don't have budget"**

**Response:**
"That's fair. When does your budget cycle reset?

[They answer: Usually Jan 1 or July 1]

Perfect. Let's do this:
1. Run a 30-day POC now (free)
2. Build business case with ROI
3. Get on budget for next cycle

By then you'll have data to justify the spend. Sound reasonable?"

---

### Technical Objections

**"We can build this in-house"**

**Response:**
"You're right, you could. Let me ask:

1. How many engineer-months would that take?
2. What's their fully-loaded cost?
3. Who maintains it long-term?
4. Will auditors trust a homegrown solution?

[Let them calculate: Typically 6-12 months, $200-500K cost]

Our enterprise customers tried that. They learned:
- Harder than expected (edge cases)
- Maintenance burden
- Auditor skepticism
- Diverts from core product

Could it make sense to focus your team on your core product and use Lexecon for governance?"

**"What about blockchain?"**

**Response:**
"Great question. We evaluated blockchain:

**Blockchain Cons:**
- Slow (10-60s per transaction)
- Expensive ($1-10 per transaction)
- Complex infrastructure
- Overkill for audit trails

**Lexecon Approach:**
- Hash-chained ledger (tamper-proof)
- Cryptographic signatures (non-repudiation)
- 10,000 decisions/second
- 10ms latency
- 99.9% cheaper

The auditability is the same. The performance is 1000x better.

Does that address your concern?"

---

### Procurement Objections

**"We need to get 3 quotes"**

**Response:**
"Totally understand. A few questions:

1. What are your evaluation criteria? (price, features, security)
2. What weight for each?
3. When do you need quotes by?

We're confident we'll score highest on:
- Features (universal protocol, not just AI)
- Security (cryptographic ledger)
- Compliance (6 frameworks mapped)
- Performance (10ms latency)

Will Lexecon be evaluated fairly on those criteria?"

**"Slower than blockchain"**

**Response:**
"Let me show you:

**Lexecon Performance:**
- Decision latency: 10ms (p99)
- Throughput: 10,000 decisions/sec
- Ledger writes: 100ms (async)

**Blockchain Performance:**
- Transaction time: 10-60 seconds
- Throughput: 10-100 transactions/sec
- Cost: $1-10 per transaction

We're 1000x faster and 99.9% cheaper.

The auditability is the same because we use cryptographic hash chaining.

Would you like to see the benchmarks?"

---

## 🎬 COMPETITIVE INTELLIGENCE

### AWS CloudTrail / Azure Monitor

**Weaknesses:**
- Cloud-specific (not universal)
- Not real-time (batch)
- No policy engine
- No compliance mapping
- No cryptographic proofs

**Our Edge:**
- Universal (multi-cloud, on-premise)
- Real-time (runtime gating)
- Policy engine (graph-based)
- Automated compliance (6 frameworks)
- Cryptographic audit trails

**Message:**
"CloudTrail is great for infrastructure logs. Lexecon is for AI/autonomous system governance. They complement each other."

### HumanLayer / Gopal

**Weaknesses:**
- AI-specific only (not universal)
- Less mature (smaller teams)
- Fewer compliance mappings
- No cryptographic ledger

**Our Edge:**
- Universal protocol (AI, finance, healthcare, automotive)
- Open source core (transparency)
- Enterprise security (Ed25519, MFA, OIDC)
- 6 compliance frameworks
- Standards positioning (NIST, IEEE)

**Message:**
"HumanLayer is great for AI agents. Lexecon is the universal governance protocol for any autonomous system—AI, trading, vehicles, IoT. We're building the standard."

### Traditional GRC Tools (ServiceNow, RSA Archer)

**Weaknesses:**
- Manual (not real-time)
- Not developer-friendly
- Expensive ($500K-2M/year)
- Slow implementation (1-2 years)
- Post-hoc analysis (not preventive)

**Our Edge:**
- Real-time (runtime gating)
- Developer-first (API, code, CLI)
- Affordable ($5K-500K/year)
- Fast deployment (1-4 weeks)
- Preventive (deny-by-default)

**Message:**
"Traditional GRC is compliance theater—checking boxes after the fact. Lexecon is real governance—preventing bad decisions in real time."

---

## 📞 DISCOVERY QUESTION BANK

### Qualification Questions (BANT)

**Budget:**
- "What's your budget range for governance tools this year?"
- "Who controls that budget?"
- "What's the approval process?"
- "Is there budget allocated, or do we need to create?"

**Authority:**
- "Who else needs to be involved in this decision?"
- "Who's the final approver?"
- "What's your role in the process?"
- "Have you bought similar tools before?"

**Need:**
- "How are you solving this today?"
- "What's working well?"
- "What's not working?"
- "How painful is this on a scale of 1-10?"

**Timeline:**
- "When do you need a solution in place?"
- "What's driving that timeline?"
- "What happens if you don't hit it?"
- "Ideal vs. acceptable timeline?"

### Problem Discovery

**Current State:**
- "Walk me through how [process] works today"
- "Who's involved in that process?"
- "How long does it take?"
- "How often do you do it?"

**Pain Points:**
- "What's the biggest frustration with current process?"
- "What happens when it breaks?"
- "How often does that happen?"
- "What's the business impact?"

**Desired State:**
- "What would ideal look like?"
- "If you could wave a wand, what changes?"
- "What's the measurable outcome?"
- "Who benefits most from that?"

### ROI Discovery

**Current Costs:**
- "How many hours per week on compliance?"
- "How many people?"
- "What's their fully-loaded cost?"
- "What about external audit costs?"

**Risk Costs:**
- "Have you had audit findings?"
- "What's the cost to remediate?"
- "Any near-misses or incidents?"
- "What's your worst-case scenario?"

**Benefits:**
- "What would you do with saved time?"
- "How would faster deployment help?"
- "What's the value of passing audits easily?"
- "How do you measure success?"

---

## 📊 ROI FRAMEWORK

### ROI Calculator Template

```python
# Inputs from customer
engineer_hours_per_week = 40
engineer_cost_per_hour = 150  # Fully loaded
compliance_breach_risk = 5000000  # $5M fine
audit_failure_probability = 0.3  # 30% chance
manual_reporting_hours = 80  # per quarter

# Lexecon benefits
lexecon_annual_cost = 50000
time_savings_factor = 0.6  # 60% time reduction
audit_improvement = 0.9  # 90% pass rate

# Calculation
time_savings_value = (manual_reporting_hours * 4 * engineer_cost_per_hour * time_savings_factor)
risk_reduction_value = (compliance_breach_risk * audit_failure_probability * (1 - audit_improvement))

annual_benefit = time_savings_value + risk_reduction_value
annual_roi = (annual_benefit - lexecon_annual_cost) / lexecon_annual_cost * 100

print(f"Annual Benefit: ${annual_benefit:,}")
print(f"Annual ROI: {annual_roi:.0f}%")
```

**Expected Output:**
- Annual Benefit: $180,000
- Annual ROI: 260%
- Payback: 3.4 months

**Use Cases:**

### Hedge Fund (MIFID II)
- **Current:** 2 compliance officers, $400K/year
- **With Lexecon:** 0.5 FTE, $100K/year
- **Savings:** $300K/year
- **Cost:** $50K/year
- **ROI:** 500%

### Hospital Network (HIPAA)
- **Current:** 3 FTEs for audit prep, $450K/year
- **With Lexecon:** 1 FTE, $150K/year
- **Savings:** $300K/year
- **Cost:** $60K/year (platform + services)
- **ROI:** 400%

### AI Startup (SOC 2)
- **Current:** Consultant, $80K/year
- **With Lexecon:** Automated, $15K/year (plus staff time)
- **Savings:** $65K/year
- **Cost:** $15K/year
- **ROI:** 333%

---

## ✅ NEXT ACTIONS

**For Founding Sales (You):**

**Today:**
- [ ] Review pitch deck (30 min)
- [ ] Customize demo for next call
- [ ] Follow up on 3 active deals

**This Week:**
- [ ] Run 5 demos
- [ ] Send 10 proposals
- [ ] Close 2 deals

**This Month:**
- [ ] Hit $100K ARR in new business
- [ ] Create 2 case studies
- [ ] Build pipeline of $500K

**For Sales Manager (Future Hire):**

**When Hired:**
- [ ] Review this playbook (2 hours)
- [ ] Shadow 5 demos
- [ ] Run 5 demos with feedback
- [ ] Build outbound sequence
- [ ] Start closing deals

---

## 📚 ADDITIONAL RESOURCES

- **SALES_PLAYBOOK.md** ← You're here
- **DEMO_ENVIRONMENT.md** - Setup & scripts
- **ROI_CALCULATOR.md** - Spreadsheet & formulas
- **COMPLIANCE_MAPPING.md** - Framework details
- **ICP_WORKSHEETS.md** - Customer profiles
- **OUTBOUND_SEQUENCES.md** - Email templates
- **PARTNERSHIP_FRAMEWORK.md** - Channel strategy
- **ENTERPRISE_CONTRACTS.md** - Legal templates
- **GTM_METRICS.md** - KPIs & dashboards
- **HIRING_PLAN.md** - When to hire

---

**Remember:** This playbook is a guide, not a script. Adapt to each customer. The best salespeople listen more than they talk.

**Now go close some deals.** 📞💰

**Target:** $150K ARR in 90 days. You got this. 💪