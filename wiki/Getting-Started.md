# Getting Started

This guide will walk you through setting up Lexecon and making your first governance decision.

---

## Overview

By the end of this guide, you will:
1. Initialize a governance node with cryptographic identity
2. Load a policy that defines allowed/forbidden actions
3. Start the API server
4. Make governance decisions via CLI and API
5. Verify audit trail integrity

**Time to complete**: ~15 minutes

---

## Step 1: Initialize a Governance Node

Every Lexecon deployment starts with a governance node - a cryptographic identity with its own keypair and ledger.

```bash
# Create a new governance node
lexecon init --node-id my-governance-node

# Output:
# ✓ Created node directory: ~/.lexecon/nodes/my-governance-node/
# ✓ Generated Ed25519 keypair
# ✓ Initialized ledger
# ✓ Created default configuration
# 
# Node ID: my-governance-node
# Public Key: 8f3a2c1d...
```

This creates:
- **Keypair**: Ed25519 private/public keys for signing decisions
- **Ledger**: Empty hash-chained audit log
- **Config**: Default settings for policy evaluation

### View Node Info

```bash
lexecon node info --node-id my-governance-node
```

---

## Step 2: Create or Load a Policy

Policies define what actions are permitted or forbidden.

### Option A: Load Example Policy

```bash
# Load a pre-made example policy
lexecon policy load --file examples/example_policy.json --node-id my-governance-node
```

### Option B: Create a Simple Policy

```bash
# Create a basic policy via CLI
lexecon policy create \
  --name "Basic Safety Policy" \
  --mode strict \
  --allow "model:read:public_data" \
  --forbid "model:write:system_files" \
  --forbid "model:execute:shell_commands" \
  --node-id my-governance-node
```

### Option C: Write Policy JSON

Create `my_policy.json`:
```json
{
  "policy_id": "pol_001",
  "version": "1.0.0",
  "mode": "strict",
  "terms": {
    "actions": [
      {
        "id": "read_public_data",
        "description": "Read publicly available information"
      },
      {
        "id": "search_web",
        "description": "Search the web"
      }
    ],
    "actors": [
      {
        "id": "model",
        "description": "AI model agent"
      }
    ]
  },
  "relations": {
    "permits": [
      {
        "actor": "model",
        "action": "read_public_data",
        "conditions": []
      }
    ],
    "forbids": [
      {
        "actor": "model",
        "action": "write_system_files",
        "reason": "System files are protected"
      }
    ]
  }
}
```

Load it:
```bash
lexecon policy load --file my_policy.json --node-id my-governance-node
```

### Verify Policy

```bash
# List loaded policies
lexecon policy list --node-id my-governance-node

# View policy details
lexecon policy show --policy-id pol_001 --node-id my-governance-node
```

---

## Step 3: Start the API Server

Start the Lexecon decision service:

```bash
# Start on default port 8000
lexecon server --node-id my-governance-node

# Or specify custom host and port
lexecon server --node-id my-governance-node --host 0.0.0.0 --port 8080
```

The server provides:
- `POST /decide` - Make governance decisions
- `GET /health` - Health check
- `GET /ledger` - Audit trail access
- `POST /verify` - Verify capability tokens

Keep this terminal open or run in background:
```bash
# Run in background
lexecon server --node-id my-governance-node &

# Or use screen/tmux for persistent sessions
```

---

## Step 4: Make Your First Decision

Now let's request a governance decision for a proposed action.

### Via CLI

```bash
# Request permission to search the web
lexecon decide \
  --actor model \
  --action "search_web" \
  --tool web_search \
  --intent "Research AI governance best practices" \
  --risk-level 1 \
  --node-id my-governance-node
```

**Response:**
```json
{
  "decision_id": "dec_abc123",
  "decision": "ALLOWED",
  "reason": "Action 'search_web' is explicitly permitted for actor 'model'",
  "capability_token": "cap_xyz789...",
  "expires_at": "2026-01-15T10:30:00Z",
  "policy_version": "1.0.0",
  "signature": "ed25519:...",
  "chain_hash": "sha256:..."
}
```

### Via API

```bash
curl -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_001",
    "actor": "model",
    "proposed_action": "search_web",
    "tool": "web_search",
    "user_intent": "Research AI governance",
    "risk_level": 1
  }'
```

### Via Python SDK

```python
from lexecon import LexeconClient

# Initialize client
client = LexeconClient(base_url="http://localhost:8000")

# Request decision
decision = client.decide(
    actor="model",
    action="search_web",
    tool="web_search",
    intent="Research AI governance",
    risk_level=1
)

print(f"Decision: {decision.decision}")
print(f"Reason: {decision.reason}")
print(f"Token: {decision.capability_token}")
```

---

## Step 5: Understanding the Response

A decision response contains:

| Field | Description |
|-------|-------------|
| `decision_id` | Unique identifier for this decision |
| `decision` | `ALLOWED`, `DENIED`, or `REQUIRES_REVIEW` |
| `reason` | Human-readable explanation |
| `capability_token` | Cryptographic proof of authorization (if allowed) |
| `expires_at` | Token expiration timestamp |
| `policy_version` | Policy version used for decision |
| `signature` | Ed25519 signature over decision |
| `chain_hash` | Hash linking to previous ledger entry |

### Using the Capability Token

If the action is allowed, use the capability token to prove authorization:

```python
# Include token in subsequent API calls
result = execute_action(
    action="search_web",
    capability_token=decision.capability_token
)
```

The token:
- ✅ Cryptographically proves authorization
- ✅ Is scoped to specific action
- ✅ Has expiration timestamp
- ✅ Is bound to policy version

---

## Step 6: Verify Audit Trail

All decisions are recorded in the cryptographic ledger.

### View Ledger

```bash
# View recent entries
lexecon ledger show --node-id my-governance-node --limit 10

# View specific decision
lexecon ledger show --decision-id dec_abc123 --node-id my-governance-node
```

### Verify Integrity

```bash
# Verify hash chain integrity
lexecon ledger verify --node-id my-governance-node

# Output:
# ✓ Verified 15 entries
# ✓ Hash chain intact
# ✓ All signatures valid
# ✓ No tampering detected
```

### Export Audit Report

```bash
# Export for compliance/audit
lexecon ledger export \
  --format json \
  --output audit_report.json \
  --node-id my-governance-node
```

---

## Common Patterns

### Pattern 1: Deny-by-Default

```bash
# Create strict policy that denies everything by default
lexecon policy create \
  --name "Strict Policy" \
  --mode strict \
  --default deny \
  --allow "model:read:public_data"
```

### Pattern 2: Require Review for High-Risk

```python
# High-risk actions go to review queue
decision = client.decide(
    actor="model",
    action="delete_database",
    risk_level=4  # 1-5 scale
)

if decision.decision == "REQUIRES_REVIEW":
    print("Action requires human approval")
```

### Pattern 3: Conditional Permissions

```json
{
  "permits": [
    {
      "actor": "model",
      "action": "access_user_data",
      "conditions": [
        {"type": "time_window", "start": "09:00", "end": "17:00"},
        {"type": "data_class", "value": "non_sensitive"}
      ]
    }
  ]
}
```

---

## Next Steps

Now that you have the basics:

1. **Explore Examples**: Check out `examples/` directory for more use cases
2. **Learn Policies**: Read the [[Policy Guide]] for advanced policy authoring
3. **Model Integration**: See [[Model Integration]] for connecting AI models
4. **API Reference**: Browse [[API Reference]] for complete endpoint documentation
5. **Security**: Review [[Security Best Practices]] for production deployment

---

## Quick Reference

```bash
# Initialize node
lexecon init --node-id <name>

# Load policy
lexecon policy load --file <path> --node-id <name>

# Start server
lexecon server --node-id <name>

# Make decision
lexecon decide --actor <actor> --action <action> --node-id <name>

# Verify ledger
lexecon ledger verify --node-id <name>

# Get help
lexecon --help
lexecon <command> --help
```

---

## Troubleshooting

**Server won't start:**
- Check if port 8000 is already in use
- Verify node was initialized: `lexecon node info --node-id <name>`

**Decision denied unexpectedly:**
- Check policy: `lexecon policy show --policy-id <id>`
- Review logs: `lexecon logs --node-id <name>`

**Can't find lexecon command:**
- Ensure it's installed: `pip list | grep lexecon`
- Check PATH: `which lexecon`

For more help, see [[Troubleshooting]] or [[FAQ]].
