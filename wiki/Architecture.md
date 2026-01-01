# Architecture

This page provides a comprehensive overview of Lexecon's architecture, components, and design principles.

---

## Overview

Lexecon is designed as a **layered governance protocol** that sits between AI models and their tool execution environment. It provides:

- **Policy-based decision making** before actions execute
- **Cryptographic proof** of authorization
- **Tamper-evident audit trail** of all decisions
- **Model-agnostic integration** layer

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          AI Model                                │
│              (OpenAI, Anthropic, Open Source)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Tool Call Request
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Lexecon Protocol Stack                        │
├─────────────────────────────────────────────────────────────────┤
│  Model Integration Layer                                         │
│    • System Prompts & Instruction Templates                      │
│    • JSON Schema Definitions                                     │
│    • API Adapters (OpenAI, Anthropic, Generic)                   │
├─────────────────────────────────────────────────────────────────┤
│  Policy Engine (src/lexecon/policy/)                             │
│    • Lexicon: Terms (Actions, Data Classes, Actors)              │
│    • Relations: Permits, Forbids, Requires, Implies              │
│    • Constraints: Compile-time and Runtime Checks                │
│    • Evaluation: Deterministic Policy Resolution                 │
├─────────────────────────────────────────────────────────────────┤
│  Decision Service (src/lexecon/decision/)                        │
│    • Request Validation & Normalization                          │
│    • Policy Evaluation Pipeline                                  │
│    • Reason Trace Generation                                     │
│    • Capability Token Minting                                    │
├─────────────────────────────────────────────────────────────────┤
│  Capability System (src/lexecon/capability/)                     │
│    • Token Generation (Scoped, Time-Limited)                     │
│    • Token Verification & Validation                             │
│    • Policy Version Binding                                      │
├─────────────────────────────────────────────────────────────────┤
│  Cryptographic Ledger (src/lexecon/ledger/)                      │
│    • Event Recording with Hash Chains                            │
│    • Signature Generation & Verification                         │
│    • Audit Report Generation                                     │
│    • Integrity Verification                                      │
├─────────────────────────────────────────────────────────────────┤
│  Identity & Signing (src/lexecon/identity/)                      │
│    • Ed25519 Key Management                                      │
│    • Node Identity                                               │
│    • Key Storage & Retrieval                                     │
├─────────────────────────────────────────────────────────────────┤
│  API Layer (src/lexecon/api/)                                    │
│    • FastAPI Server                                              │
│    • REST Endpoints                                              │
│    • Request/Response Models                                     │
└─────────────────────────────────────────────────────────────────┘
                            │ Decision Response
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Tool Execution                              │
│              (Only with valid capability token)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Policy Engine

**Location**: `src/lexecon/policy/`

The policy engine evaluates whether a proposed action should be allowed based on loaded policies.

**Key Files**:
- `engine.py` - Main policy evaluation logic
- `terms.py` - Policy term definitions (actions, actors, data classes)
- `relations.py` - Policy relations (permits, forbids, requires)
- `loader.py` - Policy loading and validation

**Key Concepts**:
- **Lexicon**: Set of terms (nodes in policy graph)
  - Actions: What can be done (e.g., "read_file", "execute_query")
  - Actors: Who can do it (e.g., "model", "user", "admin")
  - Data Classes: What it applies to (e.g., "public_data", "pii")

- **Relations**: Edges in policy graph
  - `permits`: Actor is allowed to perform action
  - `forbids`: Actor is explicitly forbidden
  - `requires`: Action requires additional conditions
  - `implies`: Action implies other actions

**Evaluation Algorithm**:
1. Normalize request (map tool names to actions)
2. Check explicit forbids (deny takes precedence)
3. Check explicit permits
4. Apply policy mode (strict = deny-by-default, permissive = allow-by-default)
5. Evaluate conditions (time windows, data classes, etc.)
6. Generate decision with reasoning trace

---

### 2. Decision Service

**Location**: `src/lexecon/decision/`

Orchestrates the decision-making process for tool call requests.

**Key Files**:
- `service.py` - Main decision service implementation
- `models.py` - Pydantic models for requests/responses
- `validator.py` - Request validation logic

**Request Flow**:
```
Request → Validation → Policy Evaluation → Token Minting → Ledger Recording → Response
```

**Decision Types**:
- `ALLOWED` - Action is permitted, token issued
- `DENIED` - Action is forbidden
- `REQUIRES_REVIEW` - Needs human approval (high-risk actions)

**Decision Response**:
```python
{
    "decision_id": "dec_...",
    "decision": "ALLOWED",
    "reason": "Action explicitly permitted",
    "capability_token": "cap_...",
    "expires_at": "2026-01-15T10:30:00Z",
    "policy_version": "1.0.0",
    "signature": "ed25519:...",
    "chain_hash": "sha256:..."
}
```

---

### 3. Capability System

**Location**: `src/lexecon/capability/`

Issues and verifies cryptographic authorization tokens.

**Key Files**:
- `token.py` - Token generation and encoding
- `verifier.py` - Token verification logic
- `scopes.py` - Scope management

**Token Structure**:
```json
{
  "token_id": "cap_abc123",
  "decision_id": "dec_xyz789",
  "action": "search_web",
  "actor": "model",
  "issued_at": "2026-01-15T10:00:00Z",
  "expires_at": "2026-01-15T10:30:00Z",
  "policy_version": "1.0.0",
  "signature": "..."
}
```

**Token Properties**:
- **Scoped**: Limited to specific action/tool
- **Time-bound**: Has expiration timestamp
- **Version-locked**: Tied to specific policy version
- **Signed**: Ed25519 signature for authenticity
- **Non-transferable**: Bound to specific request context

**Verification Process**:
1. Decode token
2. Check expiration
3. Verify signature
4. Validate scope matches intended action
5. Check policy version hasn't changed

---

### 4. Cryptographic Ledger

**Location**: `src/lexecon/ledger/`

Maintains tamper-evident record of all decisions.

**Key Files**:
- `chain.py` - Hash chain implementation
- `events.py` - Event definitions
- `storage.py` - Persistence layer
- `verifier.py` - Integrity verification

**Ledger Entry**:
```json
{
  "entry_id": "ent_001",
  "timestamp": "2026-01-15T10:00:00Z",
  "event_type": "decision_made",
  "decision_id": "dec_xyz",
  "actor": "model",
  "action": "search_web",
  "decision": "ALLOWED",
  "policy_version": "1.0.0",
  "prev_hash": "sha256:...",
  "entry_hash": "sha256:...",
  "signature": "ed25519:..."
}
```

**Hash Chain**:
```
Entry[0] → Entry[1] → Entry[2] → Entry[3]
   ↓          ↓          ↓          ↓
 hash[0] ← hash[1] ← hash[2] ← hash[3]
```

Each entry contains hash of previous entry, making tampering detectable.

**Verification**:
- Check all signatures are valid
- Verify hash chain integrity
- Ensure no gaps in sequence
- Confirm timestamps are monotonic

---

### 5. Identity & Signing

**Location**: `src/lexecon/identity/`

Manages cryptographic identities for governance nodes.

**Key Files**:
- `keypair.py` - Ed25519 key generation
- `node.py` - Node identity management
- `storage.py` - Secure key storage

**Node Identity**:
- Each governance node has unique Ed25519 keypair
- Private key signs all decisions
- Public key enables verification
- Keys stored securely with proper permissions

**Signing Process**:
1. Serialize decision deterministically
2. Hash serialized data (SHA-256)
3. Sign hash with Ed25519 private key
4. Include signature in response

---

### 6. API Layer

**Location**: `src/lexecon/api/`

Provides HTTP interface for decision requests.

**Key Files**:
- `server.py` - FastAPI application
- `routes.py` - Endpoint definitions
- `middleware.py` - Request/response middleware

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/decide` | POST | Request governance decision |
| `/verify` | POST | Verify capability token |
| `/health` | GET | Health check |
| `/ledger` | GET | Query audit trail |
| `/policy` | GET | View loaded policy |
| `/node/info` | GET | Node information |

---

### 7. CLI Interface

**Location**: `src/lexecon/cli/`

Command-line interface for Lexecon operations.

**Key Files**:
- `main.py` - CLI entry point
- `commands/init.py` - Node initialization
- `commands/server.py` - Server management
- `commands/policy.py` - Policy operations
- `commands/decide.py` - Decision requests

**Command Structure**:
```
lexecon
├── init          # Initialize node
├── server        # Start server
├── policy        # Policy management
│   ├── load
│   ├── create
│   ├── list
│   └── show
├── decide        # Make decision
├── ledger        # Ledger operations
│   ├── show
│   ├── verify
│   └── export
└── node          # Node management
    └── info
```

---

## Data Flow

### Decision Request Flow

```
1. Client → POST /decide
   {actor, action, tool, intent}

2. API Layer → Decision Service
   Validate request structure

3. Decision Service → Policy Engine
   Evaluate against loaded policy

4. Policy Engine → Decision Service
   Return ALLOWED/DENIED + reasoning

5. Decision Service → Capability System
   Mint token (if allowed)

6. Decision Service → Ledger
   Record decision event

7. Ledger → Cryptography
   Sign and hash-chain entry

8. API Layer → Client
   Return decision + token
```

### Token Verification Flow

```
1. Client → POST /verify
   {capability_token}

2. Capability System → Verify
   - Decode token
   - Check expiration
   - Verify signature

3. Capability System → Policy Engine
   Ensure policy version matches

4. Response → Client
   {valid: true/false, reason}
```

---

## Design Principles

### 1. Deny-by-Default

Unless explicitly permitted by policy, actions are denied.

```python
if action in policy.forbids:
    return DENIED
elif action in policy.permits:
    return ALLOWED
else:
    # Default behavior based on policy mode
    if policy.mode == "strict":
        return DENIED
    else:
        return ALLOWED
```

### 2. Cryptographic Guarantees

Every decision is:
- **Signed** with Ed25519
- **Hash-chained** to previous decisions
- **Timestamped** with monotonic clock
- **Versioned** to specific policy

### 3. Separation of Concerns

- Policy defines WHAT is allowed
- Decision service determines IF allowed
- Capability system proves authorization
- Ledger records for audit
- Each layer is independent and testable

### 4. Injection Resistance

- Structured evaluation (no string interpolation)
- Schema-validated inputs
- No user-controlled code execution
- Policy tampering detection

### 5. Model Agnostic

- Works with any LLM/AI model
- Standard JSON request/response
- Adapters for specific model APIs
- No model-specific logic in core

---

## Scalability Considerations

### Horizontal Scaling

- **Stateless API**: Decision service is stateless
- **Shared Ledger**: Use distributed ledger backend
- **Policy Cache**: Cache compiled policies
- **Load Balancer**: Distribute requests across nodes

### Performance Optimizations

- **Policy Compilation**: Pre-compile policies to decision trees
- **Signature Batching**: Batch sign multiple decisions
- **Ledger Buffering**: Buffer writes to ledger
- **Token Caching**: Cache validated tokens

### High Availability

- **Multi-Node**: Run multiple governance nodes
- **Replication**: Replicate ledger across nodes
- **Consensus**: Use consensus for distributed decisions
- **Failover**: Automatic failover to backup nodes

---

## Security Model

### Threat Model

**Protections Against**:
- ✅ Prompt injection attacks
- ✅ Policy tampering
- ✅ Replay attacks
- ✅ Token forgery
- ✅ Audit trail tampering

**Out of Scope**:
- ❌ Physical access to server
- ❌ Compromised private keys
- ❌ Network layer attacks (use TLS)
- ❌ DoS attacks (use rate limiting)

### Key Security Features

1. **Cryptographic Signing**: Ed25519 signatures on all decisions
2. **Hash Chaining**: Tamper-evident ledger
3. **Token Expiration**: Time-limited authorization
4. **Policy Versioning**: Detect policy changes
5. **Deterministic Evaluation**: Same input → same output

---

## Extension Points

Lexecon is designed to be extensible:

1. **Custom Policy Evaluators**: Implement custom logic
2. **Custom Token Types**: Different authorization schemes
3. **Custom Ledger Backends**: Different storage systems
4. **Custom Adapters**: Support new AI models
5. **Custom Middleware**: Add logging, metrics, etc.

---

## Next Steps

- **[[Policy Guide]]** - Learn to write effective policies
- **[[API Reference]]** - Explore all endpoints
- **[[Security Best Practices]]** - Harden your deployment
- **[[Examples]]** - See architecture in action
