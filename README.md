# Lexecon - Lexical Governance Protocol

A unified cryptographic governance system for AI safety, compliance, and auditability. Lexecon combines lexicoding-forward policy models with runtime gating and tamper-evident ledgers.

## Overview

Lexecon provides a complete governance framework for AI systems with the following key features:

- **Lexicoding-Forward Policies**: Policy as lexicon + relations, compiled into executable constraints
- **Runtime Gating**: Every tool call and high-impact model action must be decision-gated
- **Cryptographic Auditability**: Signatures, hash chaining, deterministic serialization, verification tooling
- **Capability Enforcement**: "Allowed" means enforceable authorization, not just permission
- **Model Integration Pack**: System prompt + JSON schemas + adapters for foundation model integration
- **Anti-Tamper Posture**: Injection resistance, policy tamper resistance, red team harness

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Lexecon Protocol Stack                    │
├─────────────────────────────────────────────────────────────┤
│  Model Integration Layer (System Prompts + Adapters)        │
├─────────────────────────────────────────────────────────────┤
│  Policy Engine (Lexicon + Relations + Constraints)          │
├─────────────────────────────────────────────────────────────┤
│  Decision Service (Evaluation + Reason Trace)               │
├─────────────────────────────────────────────────────────────┤
│  Capability System (Token Minting + Verification)           │
├─────────────────────────────────────────────────────────────┤
│  Cryptographic Ledger (Hash Chain + Signatures)             │
├─────────────────────────────────────────────────────────────┤
│  Identity & Signing (Ed25519 + Key Management)              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/lexecon/lexecon.git
cd lexecon

# Install dependencies
pip install -e .

# Or install from PyPI
pip install lexecon
```

### Initialize a Node

```bash
lexecon init --node-id my-node
```

### Start the API Server

```bash
lexecon server --node-id my-node --port 8000
```

### Make a Governance Decision

```bash
lexecon decide --json examples/safe_request.json
```

## API Endpoints

- `GET /health` - Health check
- `GET /status` - System status
- `GET /policies` - List loaded policies
- `POST /policies/load` - Load policy bundle
- `POST /decide` - Make governance decision
- `POST /decide/verify` - Verify decision response
- `GET /ledger/verify` - Verify ledger integrity
- `GET /ledger/report` - Generate audit report

## Model Integration

See the [Model Governance Pack](model_governance_pack/) for:

- System prompt template
- JSON schemas for requests/responses
- Adapters for OpenAI and Anthropic tool calling
- Example decision requests and model transcripts

## Core Concepts

### Policy Terms

Policies are built from terms (nodes) and relations (edges):

```python
# Define terms
read_action = PolicyTerm.create_action("read", "Read Data")
pii_data = PolicyTerm.create_data_class("pii", "Personally Identifiable Information")

# Define relations
PolicyRelation.permits("actor:user", "read:own_data")
PolicyRelation.forbids("actor:model", "write:system_files")
```

### Decision Requests

All tool calls must be routed through governance:

```json
{
  "request_id": "uuid",
  "actor": "model",
  "proposed_action": "Execute web_search",
  "tool": "web_search",
  "data_classes": [],
  "user_intent": "Research AI governance",
  "risk_level": 1,
  "requested_output_type": "tool_action",
  "policy_mode": "strict"
}
```

### Capability Tokens

Approved actions receive ephemeral capability tokens:

```json
{
  "token_id": "tok_123",
  "scope": {"action": "search", "tool": "web_search"},
  "expiry": "2025-01-15T11:30:00Z",
  "policy_version_hash": "abc123...",
  "signature": "sig_456..."
}
```

## System Invariants

Lexecon enforces these core invariants:

1. **Deterministic Evaluation**: Same policy + same request = same decision
2. **Policy Version Pinning**: Every decision references exact policy version hash
3. **Ledger Immutability**: Events are hash chained and signature verified
4. **Proof Linkage**: Decision responses contain verifiable ledger entry hash
5. **Deny-by-Default**: Fail-safe defaults exist and are testable
6. **Tool Gating**: No tool action without recorded decision and capability token
7. **Canonical Serialization**: Hashing and signing uses stable JSON form

## Policy Modes

- **permissive**: Allow unless explicitly forbidden
- **strict**: Deny unless explicitly permitted (default)
- **paranoid**: Deny high risk unless human confirmation provided

## Compliance Mapping

- **GDPR**: Data minimization, purpose limitation, consent management
- **EU AI Act**: Risk assessment, human oversight, transparency
- **SOC 2**: Audit trails, access controls, change management

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
black src/
flake8 src/

```
## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security policy and vulnerability reporting.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Documentation

- [Protocol Specification](docs/PROTOCOL_SPEC.md)
- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)
- [Legacy Unification Map](docs/LEGACY_UNIFICATION_MAP.md)
- [Model Governance Pack](model_governance_pack/)

## Support

- Documentation: https://lexecon.readthedocs.io
- Issues: https://github.com/lexecon/lexecon/issues
- Discussions: https://github.com/lexecon/lexecon/discussions