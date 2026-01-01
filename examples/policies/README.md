# Lexecon Policy Templates

This directory contains production-ready policy templates for common compliance scenarios and enterprise use cases.

## Available Templates

### 1. GDPR Compliance Policy (`gdpr_compliance_policy.json`)

**Use Case**: EU-based applications processing personal data

**Key Features**:
- Article-level GDPR compliance mapping
- Special category data protection (Article 9)
- Purpose limitation and data minimization
- Right to erasure support
- Automated decision-making controls (Article 22)
- EU AI Act high-risk system handling

**Mode**: `strict` (deny-by-default)

**Best For**: SaaS platforms, consumer applications, HR systems

---

### 2. HIPAA Healthcare Policy (`hipaa_healthcare_policy.json`)

**Use Case**: Healthcare applications handling Protected Health Information (PHI)

**Key Features**:
- PHI access controls per HIPAA Privacy Rule
- Transmission security (HIPAA Security Rule 164.312(e))
- Audit trail requirements
- Minimum necessary standard enforcement
- Emergency access provisions
- Breach notification triggers
- Psychotherapy notes special protection

**Mode**: `paranoid` (maximum security)

**Best For**: EHR systems, telemedicine, medical AI assistants

---

### 3. Financial Services Policy (`financial_services_policy.json`)

**Use Case**: Financial institutions and fintech applications

**Key Features**:
- PCI-DSS cardholder data protection
- SOX financial record controls
- GLBA non-public information safeguards
- Trading oversight and circuit breakers
- Fair lending compliance (ECOA)
- Model explainability for adverse actions
- Suspicious activity reporting (SAR) triggers

**Mode**: `strict`

**Best For**: Banking, trading platforms, credit scoring, payment processing

---

### 4. Enterprise General Policy (`enterprise_general_policy.json`)

**Use Case**: General-purpose enterprise AI deployments

**Key Features**:
- Tool action governance (web search, file access, code execution)
- Confidential data protection
- External communication controls
- Rate limiting and abuse prevention
- Sensitive data detection
- Working hours enhanced security

**Mode**: `strict`

**Best For**: Internal AI assistants, productivity tools, development copilots

---

## Usage

### Loading a Policy

```bash
# Via CLI
lexecon policy load --file examples/policies/gdpr_compliance_policy.json

# Verify loaded
lexecon policy list
```

### Via Python

```python
from lexecon import LexeconClient
import json

client = LexeconClient(base_url="http://localhost:8000")

# Load policy
with open("examples/policies/gdpr_compliance_policy.json") as f:
    policy = json.load(f)

client.load_policy(policy)
```

### Testing a Policy

```bash
# Test a decision against the policy
lexecon decide \
  --actor ai_model \
  --action "Process user data for marketing" \
  --tool process \
  --data-class personal_data \
  --intent "Marketing campaign" \
  --risk-level 3
```

---

## Customization

These templates are starting points. Customize them for your specific needs:

### 1. Adjust Sensitivity Levels

```json
{
  "id": "data:internal_docs",
  "sensitivity": "medium",  // Change to "high" for more restrictive
  "requires_authorization": true
}
```

### 2. Add Custom Actions

```json
{
  "id": "action:send_slack_message",
  "type": "action",
  "name": "send_slack_message",
  "description": "Post message to Slack channel"
}
```

### 3. Add Organization-Specific Data Classes

```json
{
  "id": "data:proprietary_algorithms",
  "type": "data_class",
  "name": "proprietary_algorithms",
  "description": "Company trade secrets",
  "sensitivity": "critical"
}
```

### 4. Modify Risk Thresholds

```json
{
  "name": "high_risk_actions",
  "condition": "risk_level >= 3",  // Lower from 4 to 3 for stricter control
  "action": "require_human_confirmation"
}
```

---

## Policy Modes

### `strict` (Recommended)
- Deny by default
- Only explicitly permitted actions allowed
- Best for production environments

### `permissive`
- Allow by default
- Only explicitly forbidden actions blocked
- Best for development/testing

### `paranoid`
- Strict mode + additional safeguards
- High-risk actions require human confirmation
- Best for regulated industries (healthcare, finance)

---

## Compliance Mapping

### GDPR Articles Covered

| Article | Requirement | Implementation |
|---------|-------------|----------------|
| Art. 5(1)(b) | Purpose limitation | `purpose_limitation` constraint |
| Art. 5(1)(c) | Data minimization | `data_minimization` constraint |
| Art. 5(1)(e) | Storage limitation | `storage_limitation` constraint |
| Art. 6 | Lawfulness | `valid_legal_basis` requirement |
| Art. 9 | Special categories | `special_category_data` forbids |
| Art. 17 | Right to erasure | `delete` action permits |
| Art. 22 | Automated decisions | `automated_decision_making` constraint |

### HIPAA Rules Covered

| Rule | Requirement | Implementation |
|------|-------------|----------------|
| Privacy Rule 164.502(b) | Minimum necessary | `minimum_necessary` constraint |
| Privacy Rule 164.524 | Right of access | Patient `view_phi` permits |
| Security Rule 164.312(b) | Audit controls | `access_logged` requirement |
| Security Rule 164.312(e) | Transmission security | `tls_1_2_or_higher` requirement |
| Breach Rule 164.400 | Breach notification | `breach_notification` constraint |

### PCI-DSS Requirements Covered

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| Req. 3.1 | Data retention | `pci_data_retention` constraint |
| Req. 7 | Restrict access | `business_need_documented` requirement |
| Req. 10 | Track access | Audit logging enabled |

---

## Testing Your Policy

### Unit Tests

```python
import pytest
from lexecon import PolicyEngine
import json

def test_gdpr_forbids_special_category_processing():
    """Test that AI cannot process special category data."""
    with open("examples/policies/gdpr_compliance_policy.json") as f:
        policy = json.load(f)
    
    engine = PolicyEngine(policy)
    
    decision = engine.evaluate(
        actor="ai_model",
        action="process",
        data_classes=["special_category_data"],
        risk_level=3
    )
    
    assert decision.allowed is False
    assert "Article 9" in decision.reason
```

### Integration Tests

```bash
# Test decision flow
pytest tests/integration/test_policy_gdpr.py -v
```

---

## Best Practices

1. **Start Strict**: Begin with `strict` mode and relax as needed
2. **Document Justifications**: Include legal/regulatory references
3. **Version Control**: Track policy changes in git
4. **Regular Reviews**: Review policies every 90-180 days
5. **Test Thoroughly**: Write tests for critical policy rules
6. **Audit Logs**: Enable comprehensive audit logging
7. **Stakeholder Review**: Have legal/compliance review policies

---

## Resources

- [GDPR Full Text](https://gdpr-info.eu/)
- [HIPAA Privacy Rule](https://www.hhs.gov/hipaa/for-professionals/privacy/index.html)
- [PCI-DSS Standards](https://www.pcisecuritystandards.org/)
- [SOC 2 Trust Principles](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report.html)
- [EU AI Act](https://artificialintelligenceact.eu/)

---

## Support

For questions or custom policy development:
- **Email**: jacobporter@lexicoding.tech
- **Issues**: https://github.com/Lexicoding-systems/Lexecon/issues
- **Discussions**: https://github.com/Lexicoding-systems/Lexecon/discussions