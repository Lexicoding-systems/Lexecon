# Security Policy

Lexecon is a cryptographic governance system designed with security as a core principle. We take the security of Lexecon and the systems that depend on it very seriously.

## Table of Contents

- [Supported Versions](#supported-versions)
- [Reporting a Vulnerability](#reporting-a-vulnerability)
- [Security Features](#security-features)
- [Threat Model](#threat-model)
- [Security Best Practices](#security-best-practices)
- [Cryptographic Standards](#cryptographic-standards)
- [Known Security Considerations](#known-security-considerations)
- [Security Audit History](#security-audit-history)
- [Security Updates](#security-updates)
- [Security Hall of Fame](#security-hall-of-fame)

---

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          | Support End Date |
| ------- | ------------------ | ---------------- |
| 0.1.x   | :white_check_mark: | TBD              |
| < 0.1.0 | :x:                | N/A              |

**Note**: As Lexecon is currently in alpha (v0.1.x), we recommend thorough security testing before production use.

### Version Support Policy

- **Current Version**: Always receives security updates
- **Previous Major Version**: Receives critical security updates for 6 months after new major release
- **Older Versions**: No longer supported, users should upgrade

---

## Reporting a Vulnerability

**DO NOT** open public issues for security vulnerabilities.

### Reporting Process

1. **Email Security Team**
   - Email: security@lexicoding.systems
   - PGP Key: [Available here](https://lexicoding.systems/pgp-key.txt)
   - Subject: "[SECURITY] Brief description"

2. **Include in Your Report**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)
   - Your contact information

3. **What to Expect**
   - **< 48 hours**: Initial response acknowledging receipt
   - **< 7 days**: Preliminary assessment and severity classification
   - **< 30 days**: Fix developed and tested (for critical issues)
   - **Coordinated disclosure**: We'll work with you on disclosure timing

### Report Template

```markdown
## Vulnerability Description
Brief description of the vulnerability

## Affected Components
- Component: [e.g., Policy Engine, Ledger, API]
- Version: [e.g., 0.1.0]

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Proof of Concept
Code or commands demonstrating the vulnerability

## Impact Assessment
- Confidentiality: [None/Low/Medium/High/Critical]
- Integrity: [None/Low/Medium/High/Critical]
- Availability: [None/Low/Medium/High/Critical]

## Suggested Mitigation
Your suggestions for fixing the vulnerability

## Additional Context
Any other relevant information
```

### Severity Classification

We use the following severity levels:

| Severity | Response Time | Description |
|----------|--------------|-------------|
| **Critical** | 24 hours | Remote code execution, authentication bypass |
| **High** | 48 hours | Privilege escalation, data leakage |
| **Medium** | 7 days | DoS, information disclosure |
| **Low** | 30 days | Minor issues with limited impact |

### Responsible Disclosure

We request:
- **90 days** for non-critical vulnerabilities
- **Immediate coordination** for actively exploited vulnerabilities
- **Credit** will be given in release notes (if desired)

---

## Security Features

Lexecon implements multiple layers of security:

### Cryptographic Security

#### Ed25519 Signatures
- All decisions are signed using Ed25519 (256-bit security)
- Signatures are verified before trust
- Key rotation supported

#### Hash Chaining
- Ledger entries are cryptographically linked
- Any tampering is immediately detectable
- Uses SHA-256 for hashing

#### Capability Tokens
- Time-limited authorization tokens
- Scope-restricted permissions
- Cryptographically signed
- Cannot be forged without private key

### System Security

#### Deny-by-Default
- Unknown actions are rejected by default in strict mode
- Explicit permissions required
- Fail-safe behavior on errors

#### Input Validation
- All inputs are validated and sanitized
- Type checking with Pydantic models
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)

#### Rate Limiting
- API endpoints are rate-limited
- Prevents brute-force attacks
- Configurable limits per endpoint

#### Audit Trail
- All decisions recorded in tamper-evident ledger
- Full traceability of actions
- Integrity verification available

---

## Threat Model

### Assets Protected

1. **Cryptographic Keys**: Ed25519 signing keys for nodes
2. **Policy Definitions**: Governance policies
3. **Audit Ledger**: Historical decision records
4. **Capability Tokens**: Authorization tokens
5. **Decision Integrity**: Correctness of governance decisions

### Threat Actors

#### External Attackers
- **Goal**: Bypass governance, exfiltrate data, disrupt service
- **Capabilities**: Network access, crafted requests
- **Mitigations**: Input validation, rate limiting, authentication

#### Malicious Models
- **Goal**: Bypass policy restrictions, escalate privileges
- **Capabilities**: Crafted tool call requests, prompt injection
- **Mitigations**: Structured evaluation, policy enforcement, ledger

#### Insider Threats
- **Goal**: Manipulate policies, tamper with ledger
- **Mitigations**: Policy versioning, hash chaining, audit trails

### Attack Vectors

#### 1. Policy Bypass
**Attack**: Craft requests to circumvent policy restrictions
**Mitigations**:
- Strict input validation
- Structured policy evaluation
- Deny-by-default mode
- Comprehensive testing

#### 2. Prompt Injection
**Attack**: Inject malicious instructions to manipulate model behavior
**Mitigations**:
- Structured decision requests (JSON)
- Separate evaluation context
- Policy-based rather than prompt-based control

#### 3. Token Forgery
**Attack**: Create fake capability tokens
**Mitigations**:
- Cryptographic signatures (Ed25519)
- Token verification on every use
- Time-limited tokens
- Policy version binding

#### 4. Ledger Tampering
**Attack**: Modify historical records
**Mitigations**:
- Hash chaining
- Cryptographic signatures
- Periodic integrity verification
- Immutable append-only structure

#### 5. Denial of Service
**Attack**: Overwhelm system with requests
**Mitigations**:
- Rate limiting
- Request timeouts
- Resource limits
- Monitoring and alerting

#### 6. Key Compromise
**Attack**: Steal or leak signing keys
**Mitigations**:
- Filesystem permissions
- Key rotation support
- KMS integration (recommended for production)
- Separate keys per node

---

## Security Best Practices

### For Deployment

#### Key Management

**Development**:
```bash
# Keys stored in node directory with restricted permissions
chmod 600 ~/.lexecon/nodes/*/keys/private_key.pem
```

**Production**:
```bash
# Use a Key Management Service (KMS)
# Examples: AWS KMS, Azure Key Vault, HashiCorp Vault
export LEXECON_KMS_PROVIDER=aws
export LEXECON_KMS_KEY_ID=arn:aws:kms:...
```

**Key Rotation**:
```bash
# Rotate keys periodically (every 90 days recommended)
lexecon identity rotate-key --node-id production-node
```

#### Network Security

**Always use TLS for API communication**:
```yaml
# config.yaml
server:
  tls:
    enabled: true
    cert_file: /path/to/cert.pem
    key_file: /path/to/key.pem
```

**Restrict network access**:
```bash
# Use firewall rules
iptables -A INPUT -p tcp --dport 8000 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

#### Access Control

**Restrict file system access**:
```bash
# Node directories should be owned by service user
chown -R lexecon:lexecon ~/.lexecon/
chmod 700 ~/.lexecon/nodes/
```

**Use dedicated service accounts**:
```bash
# Don't run as root
sudo -u lexecon lexecon server --node-id prod
```

#### Monitoring

**Set up security monitoring**:
```yaml
# config.yaml
monitoring:
  alert_on_denied_high_risk: true
  alert_on_policy_changes: true
  alert_on_ledger_verification_failures: true
```

**Monitor logs for suspicious activity**:
```bash
# Watch for repeated denials
tail -f /var/log/lexecon/decisions.log | grep "allowed: false"

# Alert on policy modifications
tail -f /var/log/lexecon/audit.log | grep "policy_loaded"
```

### For Development

#### Secure Coding Practices

**Input Validation**:
```python
# Always validate and sanitize inputs
from pydantic import BaseModel, validator

class DecisionRequest(BaseModel):
    actor: str
    risk_level: int

    @validator('risk_level')
    def validate_risk_level(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Risk level must be between 1 and 5')
        return v
```

**Avoid Secrets in Code**:
```python
# Bad
api_key = "sk-1234567890abcdef"

# Good
import os
api_key = os.environ.get('API_KEY')
if not api_key:
    raise ValueError("API_KEY environment variable not set")
```

**Use Parameterized Queries**:
```python
# Bad (SQL injection risk)
cursor.execute(f"SELECT * FROM ledger WHERE id = '{entry_id}'")

# Good
cursor.execute("SELECT * FROM ledger WHERE id = ?", (entry_id,))
```

#### Dependency Security

**Regular updates**:
```bash
# Check for vulnerable dependencies
pip install safety
safety check

# Update dependencies
pip install --upgrade -r requirements.txt
```

**Pin dependencies**:
```txt
# requirements.txt - use specific versions
cryptography==42.0.5
fastapi==0.109.2
pydantic==2.5.3
```

---

## Cryptographic Standards

### Algorithms Used

| Purpose | Algorithm | Key Size | Standard |
|---------|-----------|----------|----------|
| Signing | Ed25519 | 256-bit | RFC 8032 |
| Hashing | SHA-256 | 256-bit | FIPS 180-4 |
| JSON Canonicalization | RFC 8785 | N/A | RFC 8785 |

### Why Ed25519?

- **Fast**: Faster than RSA and ECDSA
- **Small keys**: 32-byte public keys
- **Deterministic**: No need for random number generation during signing
- **Widely supported**: Available in cryptography.io
- **Secure**: Resistant to timing attacks

### Cryptographic Guarantees

1. **Signature Integrity**: Cannot forge signatures without private key
2. **Hash Collision Resistance**: SHA-256 provides 128-bit collision resistance
3. **Deterministic Serialization**: Same data always produces same hash
4. **Non-repudiation**: Signatures prove origin

---

## Known Security Considerations

### Current Limitations

#### 1. Local Key Storage (v0.1.x)
- **Issue**: Keys stored on filesystem by default
- **Risk**: Keys could be compromised if system is breached
- **Mitigation**: Use KMS in production (planned for v0.3.0)
- **Workaround**: Restrict filesystem permissions, use disk encryption

#### 2. No Built-in Rate Limiting (v0.1.x)
- **Issue**: API doesn't have built-in rate limiting
- **Risk**: DoS attacks possible
- **Mitigation**: Use reverse proxy (nginx, API gateway)
- **Planned**: Built-in rate limiting in v0.2.0

#### 3. Single-Node Architecture (v0.1.x)
- **Issue**: No distributed consensus
- **Risk**: Single point of failure
- **Mitigation**: High availability setup, regular backups
- **Planned**: Multi-node federation in v0.3.0

### Security Assumptions

Lexecon's security model assumes:

1. **Trusted Execution Environment**: Node runs in secure environment
2. **Secure Transport**: TLS used for all network communication
3. **Key Security**: Private keys are kept secure
4. **System Security**: Underlying OS is secure and patched
5. **Network Security**: Network is protected by firewall

**If these assumptions don't hold, security guarantees may not apply.**

---

## Security Audit History

### Professional Audits

| Date | Auditor | Scope | Report |
|------|---------|-------|--------|
| TBD | TBD | Full security audit planned | Pending |

### Internal Reviews

- **2025-12**: Initial security design review
- Ongoing code reviews with security focus

### Bounty Program

We plan to launch a bug bounty program once we reach v1.0.0.

---

## Security Updates

### Update Notifications

Subscribe to security updates:
- GitHub: Watch repository → Custom → Security alerts
- Email: security-announce@lexicoding.systems
- RSS: https://lexicoding.systems/security.xml

### Applying Updates

```bash
# Check current version
lexecon --version

# Update to latest version
pip install --upgrade lexecon

# Verify update
lexecon --version

# Test in staging first
lexecon doctor --check-all
```

### Security Release Process

1. Security fix developed in private repository
2. Fix tested thoroughly
3. Advisory drafted
4. Release published
5. Advisory published
6. Notification sent to subscribers

---

## Security Hall of Fame

We recognize security researchers who help make Lexecon more secure:

| Researcher | Vulnerability | Severity | Date |
|------------|--------------|----------|------|
| TBD | TBD | TBD | TBD |

**Want to be listed?** Report a valid security vulnerability!

---

## Contact

### Security Team

- **Email**: security@lexicoding.systems
- **PGP Key**: [https://lexicoding.systems/pgp-key.txt](https://lexicoding.systems/pgp-key.txt)
- **Response Time**: < 48 hours

### General Security Questions

For non-sensitive security questions:
- GitHub Discussions: https://github.com/Lexicoding-systems/Lexecon/discussions
- Documentation: https://lexecon.readthedocs.io/security

---

## Compliance

### Standards and Frameworks

Lexecon is designed to help with:
- **GDPR**: Article 25 (Privacy by Design)
- **EU AI Act**: Annex IV (Technical Documentation)
- **SOC 2**: CC6.1 (Logical and Physical Access Controls)
- **NIST Cybersecurity Framework**: Identify, Protect, Detect

### Certifications (Planned)

- SOC 2 Type II (planned for v1.0.0)
- ISO 27001 (under consideration)

---

## Resources

### Security Documentation

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cryptographic Standards](https://csrc.nist.gov/)

### Security Tools

```bash
# Dependency scanning
pip install safety
safety check

# Static analysis
pip install bandit
bandit -r src/

# Secret scanning
pip install detect-secrets
detect-secrets scan

# License compliance
pip install pip-licenses
pip-licenses
```

---

## Acknowledgments

We thank the security research community for their valuable contributions to making Lexecon more secure.

**Report security issues responsibly. We appreciate your efforts to keep Lexecon and its users safe.**

---

*Last Updated: 2025-12-31*
