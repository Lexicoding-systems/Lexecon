# FAQ (Frequently Asked Questions)

Common questions about Lexecon and their answers.

---

## General Questions

### What is Lexecon?

Lexecon is a unified cryptographic governance system for AI safety, compliance, and auditability. It provides runtime gating for AI tool calls, cryptographic authorization tokens, and tamper-evident audit trails.

### Why do I need Lexecon?

If you're building AI systems that:
- Execute tool calls or actions
- Need compliance with regulations (GDPR, EU AI Act, SOC 2)
- Require audit trails
- Handle sensitive data
- Need to prevent unauthorized actions

Then Lexecon provides governance infrastructure to ensure safe, compliant operation.

### Is Lexecon free?

Yes, Lexecon is open source under the MIT License. You can use it freely for commercial and non-commercial purposes.

### What AI models does Lexecon support?

Lexecon is **model-agnostic**. It works with:
- OpenAI (GPT-3.5, GPT-4, etc.)
- Anthropic (Claude)
- Open-source models (LLaMA, Mistral, etc.)
- Any model that can make structured tool calls

### Can I use Lexecon in production?

Lexecon is currently in **Alpha** (v0.1.0). It's suitable for:
- ✅ Development and testing
- ✅ Internal tools
- ⚠️ Production (with caution and thorough testing)

We're working toward a stable 1.0 release.

---

## Installation & Setup

### How do I install Lexecon?

```bash
# From PyPI (when published)
pip install lexecon

# From source
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon
pip install -e .
```

See [[Installation]] for detailed instructions.

### What are the system requirements?

- Python 3.8 or higher
- 512MB+ RAM
- Linux, macOS, or Windows
- Internet connection (for dependencies)

### How do I get started quickly?

```bash
# 1. Initialize node
lexecon init --node-id my-node

# 2. Load policy
lexecon policy load --file examples/example_policy.json

# 3. Start server
lexecon server --node-id my-node

# 4. Make decision
lexecon decide --actor model --action search_web
```

See [[Getting Started]] for a complete tutorial.

---

## Policy Questions

### What is a policy?

A policy defines what actions are allowed or forbidden for different actors (users, models, systems). Policies are written in JSON and loaded into Lexecon.

### Do I need to write policies?

Yes, policies are required. However, we provide:
- Example policies in `examples/`
- Policy templates
- Policy generator tool (coming soon)

### What's the difference between strict and permissive mode?

- **Strict mode**: Deny-by-default (only explicitly allowed actions pass)
- **Permissive mode**: Allow-by-default (only explicitly forbidden actions fail)

We recommend **strict mode** for production.

### Can I update a policy without restarting?

Currently, policies require a server restart. Hot-reloading is planned for a future release.

### How do I test a policy?

```bash
# Validate syntax
lexecon policy validate --file my_policy.json

# Test with dry-run
lexecon decide --dry-run --actor model --action test
```

---

## Decision & Tokens

### What is a capability token?

A capability token is a cryptographically signed authorization proof that allows executing a specific action. It's:
- Time-limited (expires after period)
- Scoped (specific action only)
- Signed (Ed25519 signature)
- Non-transferable

### How long do tokens last?

Default: 30 minutes. Configurable per policy:

```json
{
  "token_ttl": "30m"
}
```

### Can I revoke a token?

Token revocation is planned for v0.2.0. Current workaround:
- Tokens auto-expire
- Update policy version (invalidates old tokens)
- Restart server

### What does "REQUIRES_REVIEW" mean?

High-risk actions can be configured to require human approval before execution. The decision is pending until approved.

### How do I handle denied decisions?

```python
decision = client.decide(actor="model", action="test")

if decision.decision == "DENIED":
    # Log the denial
    logger.warning(f"Action denied: {decision.reason}")
    
    # Inform user
    return f"I cannot perform that action: {decision.reason}"
```

---

## Security

### Is Lexecon secure?

Lexecon uses:
- Ed25519 cryptographic signatures
- SHA-256 hash chaining
- Tamper-evident ledger
- Structured evaluation (no code injection)

However, security depends on:
- Proper policy configuration
- Secure key storage
- Network security (use HTTPS)
- Regular updates

See [[Security Best Practices]] for hardening.

### How are private keys stored?

By default, keys are stored in `~/.lexecon/nodes/<node-id>/private_key` with 0600 permissions (owner read-only).

For production:
- Use hardware security modules (HSM)
- Use key management services (AWS KMS, Azure Key Vault)
- Encrypt at rest

### What if private keys are compromised?

1. Immediately rotate keys: `lexecon node rotate-key --node-id <id>`
2. Invalidate all existing tokens
3. Audit ledger for suspicious activity
4. Generate incident report: `lexecon ledger export`

### Can policies be tampered with?

Policies are hash-pinned. Any modification changes the hash, which:
- Invalidates existing capability tokens
- Is logged in the ledger
- Can be detected via integrity checks

### Does Lexecon prevent prompt injection?

Lexecon uses **structured evaluation** (not string interpolation), making it resistant to prompt injection. However:
- Policy logic itself must be sound
- User inputs are validated
- Context is checked

---

## Performance

### How fast is Lexecon?

Typical decision latency:
- Simple policy: <10ms
- Complex policy: 10-50ms
- With ledger write: 50-100ms

Performance depends on:
- Policy complexity
- Storage backend
- Network latency

### Can Lexecon scale horizontally?

Yes, the decision service is stateless. Scale by:
- Running multiple instances
- Using load balancer
- Sharing ledger backend

See [[Architecture]] for details.

### What's the bottleneck?

Usually ledger writes. Optimize by:
- Using faster storage (SSD, in-memory)
- Batching writes
- Async ledger commits

---

## Integration

### How do I integrate with OpenAI?

```python
from lexecon import LexeconClient
import openai

client = LexeconClient()

# Before tool call
decision = client.decide(
    actor="model",
    action="web_search",
    tool="web_search"
)

if decision.decision == "ALLOWED":
    # Call OpenAI with tool
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[...],
        tools=[...],
        tool_choice="auto"
    )
```

See [[Model Integration]] for complete examples.

### How do I integrate with Anthropic Claude?

Similar to OpenAI:

```python
from anthropic import Anthropic
from lexecon import LexeconClient

anthropic = Anthropic()
lexecon = LexeconClient()

# Get decision before tool use
decision = lexecon.decide(
    actor="model",
    action="search",
    tool="web_search"
)

if decision.decision == "ALLOWED":
    message = anthropic.messages.create(
        model="claude-3-opus-20240229",
        messages=[...],
        tools=[...]
    )
```

### Can I use Lexecon without an AI model?

Yes! Lexecon can govern any tool execution system, not just AI models. Use it for:
- API gateways
- Workflow engines
- Automation systems
- Service orchestration

---

## Troubleshooting

### Server won't start

**Check if port is in use:**
```bash
lsof -i :8000  # Check port 8000
```

**Solution:**
```bash
# Use different port
lexecon server --port 8080
```

### "Policy not loaded" error

**Cause:** No policy loaded into node.

**Solution:**
```bash
lexecon policy load --file examples/example_policy.json --node-id my-node
```

### Unexpected denials

**Debug:**
```bash
# View policy
lexecon policy show --policy-id pol_001

# Check decision with reason
lexecon decide --actor model --action test --verbose
```

### Token verification fails

**Possible causes:**
- Token expired
- Policy version changed
- Invalid signature
- Wrong node

**Check:**
```bash
lexecon verify --token <token> --verbose
```

### Ledger verification fails

**Cause:** Hash chain broken (tampering detected).

**Action:**
1. Do NOT use this node for decisions
2. Export ledger: `lexecon ledger export`
3. Investigate: Check for unauthorized access
4. Report incident
5. Restore from backup or create new node

See [[Troubleshooting]] for more issues.

---

## Development

### How do I contribute?

See [[Contributing]] for guidelines.

Quick start:
```bash
# Fork repo
git clone https://github.com/YOUR_USERNAME/Lexecon.git

# Create branch
git checkout -b feature/my-feature

# Make changes and test
make test

# Submit PR
```

### How do I run tests?

```bash
# All tests
pytest

# With coverage
pytest --cov=lexecon

# Specific test
pytest tests/test_policy.py
```

### How do I report bugs?

[Open an issue](https://github.com/Lexicoding-systems/Lexecon/issues) with:
- Description of bug
- Steps to reproduce
- Expected vs actual behavior
- System info (OS, Python version)
- Logs (if applicable)

---

## Compliance

### Is Lexecon GDPR compliant?

Lexecon provides tools for GDPR compliance:
- Audit trails for data access
- Purpose limitation via policies
- Data minimization enforcement
- Right to be forgotten (coming soon)

However, **compliance is a shared responsibility**. You must:
- Configure appropriate policies
- Implement data handling procedures
- Maintain audit logs
- Have legal review

### Does Lexecon help with EU AI Act?

Yes, Lexecon addresses several EU AI Act requirements:
- Risk management via policy controls
- Transparency via audit trails
- Human oversight via review workflows
- Record-keeping via ledger

See [[Compliance Mapping]] for details.

### What about SOC 2?

Lexecon supports SOC 2 Trust Service Criteria:
- **Security**: Cryptographic controls
- **Availability**: HA deployment options
- **Processing Integrity**: Policy enforcement
- **Confidentiality**: Access controls
- **Privacy**: Data governance

---

## Roadmap

### What's coming next?

**v0.2.0** (Q1 2026):
- Token revocation
- Hot policy reloading
- Web UI dashboard
- Enhanced monitoring

**v0.3.0** (Q2 2026):
- Multi-node consensus
- Policy marketplace
- Advanced analytics
- GraphQL API

**v1.0.0** (Q3 2026):
- Production-ready
- Performance optimizations
- Extended model support
- Enterprise features

See [GitHub Milestones](https://github.com/Lexicoding-systems/Lexecon/milestones) for details.

### Can I request features?

Yes! [Open a feature request](https://github.com/Lexicoding-systems/Lexecon/issues/new?template=feature_request.md) or vote on existing requests.

---

## Support

### Where can I get help?

- 📖 [Wiki](https://github.com/Lexicoding-systems/Lexecon/wiki) (you're here!)
- 💬 [Discussions](https://github.com/Lexicoding-systems/Lexecon/discussions)
- 🐛 [Issues](https://github.com/Lexicoding-systems/Lexecon/issues)
- 📧 Email: support@lexicoding.systems

### Is there a community?

Join our community:
- GitHub Discussions
- Discord (coming soon)
- Monthly community calls

### Can I get commercial support?

Enterprise support options coming soon. Contact: enterprise@lexicoding.systems

---

## Licensing

### What is the license?

[MIT License](https://github.com/Lexicoding-systems/Lexecon/blob/main/LICENSE) - very permissive.

You can:
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Sublicense

You must:
- Include license notice
- Include copyright notice

### Can I use Lexecon in proprietary software?

Yes, MIT license allows commercial use without requirement to open-source your code.

---

## More Questions?

Can't find your answer?
- Check [[Troubleshooting]]
- Search [GitHub Discussions](https://github.com/Lexicoding-systems/Lexecon/discussions)
- [Ask a question](https://github.com/Lexicoding-systems/Lexecon/discussions/new?category=q-a)
