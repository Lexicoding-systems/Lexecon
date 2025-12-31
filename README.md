# Lexecon - Lexical Governance Protocol

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A unified cryptographic governance system for AI safety, compliance, and auditability**

[Documentation](https://lexecon.readthedocs.io) | [Quick Start](#quick-start) | [API Reference](#api-reference) | [Contributing](#contributing)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
  - [CLI Commands](#cli-commands)
  - [API Endpoints](#api-endpoints)
  - [Python SDK](#python-sdk)
- [Policy System](#policy-system)
- [Model Integration](#model-integration)
- [System Invariants](#system-invariants)
- [Compliance & Standards](#compliance--standards)
- [Development](#development)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

---

## Overview

Lexecon provides a complete governance framework for AI systems by combining lexicoding-forward policy models with runtime gating and tamper-evident ledgers. It ensures that AI systems operate within defined boundaries, with every action being cryptographically auditable.

### What Makes Lexecon Different?

- **Deny-by-Default**: Safe defaults with explicit permission requirements
- **Cryptographic Guarantees**: Every decision is signed, hashed, and chain-linked
- **Runtime Enforcement**: Policies are enforced at execution time, not just checked
- **Model-Agnostic**: Works with any foundation model (OpenAI, Anthropic, open-source)
- **Compliance-Ready**: Built-in mapping to GDPR, EU AI Act, SOC 2

---

## Problem Statement

Modern AI systems face critical challenges:

1. **Uncontrolled Tool Usage**: Models can execute arbitrary tool calls without oversight
2. **Audit Gaps**: No tamper-proof record of what actions were taken and why
3. **Compliance Burden**: Manual mapping of AI behavior to regulatory requirements
4. **Policy Drift**: Policies become outdated or inconsistent with actual behavior
5. **Prompt Injection**: Adversarial inputs can bypass intent-based controls

**Lexecon solves these problems** by providing:
- Pre-execution gating for all tool calls
- Cryptographic audit trail with hash chaining
- Declarative policies that compile to executable constraints
- Injection-resistant evaluation framework

---

## Key Features

### 🔐 Lexicoding-Forward Policies
- Policy as lexicon (terms/nodes) + relations (edges)
- Compiles into executable constraints
- Version-controlled and hash-pinned

### ⚡ Runtime Gating
- Every tool call must pass through decision service
- Capability tokens for approved actions
- Expiry and scope enforcement

### 🔗 Cryptographic Auditability
- Ed25519 signatures on all decisions
- Hash-chained ledger entries
- Deterministic serialization
- Verification tooling included

### 🛡️ Capability Enforcement
- "Allowed" means cryptographically authorized
- Ephemeral tokens with limited scope
- Policy version binding

### 🤖 Model Integration Pack
- System prompts for governance-aware models
- JSON schemas for requests/responses
- Adapters for OpenAI and Anthropic APIs
- Example transcripts and test cases

### 🔴 Anti-Tamper Posture
- Injection resistance via structured evaluation
- Policy tamper detection
- Red team harness included

---

## Architecture

```
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
```

### Component Breakdown

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Policy Engine** | Evaluate governance rules | `policy/engine.py`, `policy/terms.py`, `policy/relations.py` |
| **Decision Service** | Gate tool calls and generate decisions | `decision/service.py`, `decision/models.py` |
| **Capability System** | Issue and verify authorization tokens | `capability/token.py`, `capability/verifier.py` |
| **Ledger** | Maintain tamper-proof audit log | `ledger/chain.py`, `ledger/events.py` |
| **Identity** | Manage cryptographic identities | `identity/keypair.py`, `identity/node.py` |
| **API** | HTTP interface for decision requests | `api/server.py`, `api/routes.py` |
| **CLI** | Command-line tooling | `cli/main.py`, `cli/commands/` |

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Method 1: Install from PyPI (Recommended)

```bash
pip install lexecon
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Method 3: Using Poetry

```bash
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon
poetry install
```

### Method 4: Using Docker

```bash
docker pull lexecon/lexecon:latest
docker run -p 8000:8000 lexecon/lexecon:latest
```

### Verify Installation

```bash
lexecon --version
lexecon doctor
```

---

## Quick Start

### 1. Initialize a Governance Node

```bash
# Create a new node with cryptographic identity
lexecon init --node-id my-governance-node

# This creates:
# - ~/.lexecon/nodes/my-governance-node/
# - Ed25519 keypair
# - Empty ledger
# - Default configuration
```

### 2. Load a Policy

```bash
# Load an example policy
lexecon policy load --file examples/example_policy.json

# Or create a simple policy programmatically
lexecon policy create \
  --name "Basic Safety Policy" \
  --mode strict \
  --allow "model:read:public_data" \
  --forbid "model:write:system_files"
```

### 3. Start the API Server

```bash
# Start server on default port 8000
lexecon server --node-id my-governance-node

# Or specify custom port and host
lexecon server --node-id my-governance-node --host 0.0.0.0 --port 8080
```

### 4. Make a Governance Decision

#### Via CLI:

```bash
# Make a decision about a proposed tool call
lexecon decide \
  --actor model \
  --action "Execute web_search" \
  --tool web_search \
  --intent "Research AI governance" \
  --risk-level 1

# Or from JSON file
lexecon decide --json examples/safe_request.json
```

#### Via API:

```bash
curl -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_001",
    "actor": "model",
    "proposed_action": "Execute web_search",
    "tool": "web_search",
    "user_intent": "Research AI governance",
    "risk_level": 1,
    "policy_mode": "strict"
  }'
```

#### Via Python SDK:

```python
from lexecon import LexeconClient

client = LexeconClient(base_url="http://localhost:8000")

decision = client.decide(
    actor="model",
    proposed_action="Execute web_search",
    tool="web_search",
    user_intent="Research AI governance",
    risk_level=1
)

if decision.allowed:
    print(f"Action approved! Token: {decision.capability_token}")
    # Execute the tool call with the capability token
else:
    print(f"Action denied: {decision.reason}")
```

### 5. Verify the Ledger

```bash
# Check ledger integrity
lexecon ledger verify

# Generate audit report
lexecon ledger report --format json --output audit_report.json

# View recent decisions
lexecon ledger show --last 10
```

---

## Usage Guide

### CLI Commands

#### Node Management

```bash
# Initialize new node
lexecon init --node-id <node_id>

# List all nodes
lexecon node list

# Show node details
lexecon node show --node-id <node_id>

# Delete node
lexecon node delete --node-id <node_id>

# Export node configuration
lexecon node export --node-id <node_id> --output node_config.json
```

#### Policy Management

```bash
# Load policy from file
lexecon policy load --file <policy_file.json>

# List loaded policies
lexecon policy list

# Show policy details
lexecon policy show --name <policy_name>

# Validate policy syntax
lexecon policy validate --file <policy_file.json>

# Export policy
lexecon policy export --name <policy_name> --output policy.json

# Remove policy
lexecon policy remove --name <policy_name>
```

#### Decision Making

```bash
# Make decision from JSON file
lexecon decide --json <request_file.json>

# Make decision with CLI arguments
lexecon decide \
  --actor <actor> \
  --action <action_description> \
  --tool <tool_name> \
  --intent <user_intent> \
  --risk-level <1-5>

# Verify a decision response
lexecon decide verify --response <response_file.json>
```

#### Ledger Operations

```bash
# Verify ledger integrity
lexecon ledger verify

# Show ledger entries
lexecon ledger show [--last N] [--filter <filter>]

# Generate audit report
lexecon ledger report \
  --format <json|html|pdf> \
  --output <output_file> \
  --from <start_date> \
  --to <end_date>

# Export ledger
lexecon ledger export --output ledger_backup.json
```

#### Server Operations

```bash
# Start API server
lexecon server \
  --node-id <node_id> \
  --host <host> \
  --port <port> \
  --workers <num_workers>

# Check server health
lexecon server health --url http://localhost:8000
```

---

### API Endpoints

#### Health & Status

**GET /health**
```bash
curl http://localhost:8000/health
```
Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "node_id": "my-governance-node"
}
```

**GET /status**
```bash
curl http://localhost:8000/status
```
Response:
```json
{
  "node_id": "my-governance-node",
  "policies_loaded": 3,
  "ledger_entries": 142,
  "uptime_seconds": 3600,
  "active_tokens": 5
}
```

#### Policy Management

**GET /policies**
```bash
curl http://localhost:8000/policies
```
Response:
```json
{
  "policies": [
    {
      "name": "Basic Safety Policy",
      "version": "1.0",
      "hash": "abc123...",
      "mode": "strict",
      "loaded_at": "2025-12-31T10:00:00Z"
    }
  ]
}
```

**POST /policies/load**
```bash
curl -X POST http://localhost:8000/policies/load \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Custom Policy",
    "policy_data": {...}
  }'
```

#### Decision Making

**POST /decide**
```bash
curl -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_123",
    "actor": "model",
    "proposed_action": "Execute web_search",
    "tool": "web_search",
    "user_intent": "Research AI governance",
    "data_classes": [],
    "risk_level": 1,
    "requested_output_type": "tool_action",
    "policy_mode": "strict"
  }'
```

Response (Approved):
```json
{
  "request_id": "req_123",
  "allowed": true,
  "reason": "Action permitted by policy: web_search is allowed for research",
  "capability_token": {
    "token_id": "tok_abc123",
    "scope": {
      "action": "search",
      "tool": "web_search"
    },
    "expiry": "2025-12-31T11:30:00Z",
    "policy_version_hash": "def456...",
    "signature": "sig_789..."
  },
  "policy_version_hash": "def456...",
  "decision_hash": "hash_xyz...",
  "ledger_entry_hash": "ledger_123...",
  "timestamp": "2025-12-31T11:00:00Z",
  "signature": "node_sig_456..."
}
```

Response (Denied):
```json
{
  "request_id": "req_124",
  "allowed": false,
  "reason": "Action forbidden by policy: write:system_files requires admin role",
  "reason_trace": [
    "Evaluated rule: forbid(model, write, system_files)",
    "No overriding permit found",
    "Risk level 4 exceeds threshold for automatic approval"
  ],
  "policy_version_hash": "def456...",
  "decision_hash": "hash_abc...",
  "ledger_entry_hash": "ledger_124...",
  "timestamp": "2025-12-31T11:01:00Z",
  "signature": "node_sig_789..."
}
```

**POST /decide/verify**
```bash
curl -X POST http://localhost:8000/decide/verify \
  -H "Content-Type: application/json" \
  -d '{
    "decision_response": {...},
    "original_request": {...}
  }'
```

#### Ledger Operations

**GET /ledger/verify**
```bash
curl http://localhost:8000/ledger/verify
```
Response:
```json
{
  "valid": true,
  "entries_checked": 142,
  "chain_intact": true,
  "signatures_valid": 142
}
```

**GET /ledger/report**
```bash
curl http://localhost:8000/ledger/report?format=json&from=2025-12-01&to=2025-12-31
```

---

### Python SDK

#### Installation

```python
pip install lexecon
```

#### Basic Usage

```python
from lexecon import LexeconClient, DecisionRequest

# Initialize client
client = LexeconClient(
    base_url="http://localhost:8000",
    node_id="my-governance-node"
)

# Create a decision request
request = DecisionRequest(
    request_id="req_sdk_001",
    actor="model",
    proposed_action="Execute web_search",
    tool="web_search",
    user_intent="Research AI governance best practices",
    risk_level=1,
    policy_mode="strict"
)

# Make decision
decision = client.decide(request)

if decision.allowed:
    print(f"✓ Action approved")
    print(f"  Token: {decision.capability_token.token_id}")
    print(f"  Expires: {decision.capability_token.expiry}")

    # Verify the token before using
    is_valid = client.verify_token(decision.capability_token)
    if is_valid:
        # Execute the tool call
        result = execute_tool(tool="web_search", token=decision.capability_token)
else:
    print(f"✗ Action denied")
    print(f"  Reason: {decision.reason}")
    print(f"  Trace: {decision.reason_trace}")
```

#### Advanced Usage

```python
from lexecon import LexeconNode, PolicyEngine, DecisionService
from lexecon.policy import PolicyTerm, PolicyRelation

# Create a local node (no server)
node = LexeconNode(node_id="embedded-node")

# Define policy programmatically
policy_engine = PolicyEngine()

# Define terms
web_search = PolicyTerm.create_action("web_search", "Web Search Tool")
file_write = PolicyTerm.create_action("file_write", "File Write Operation")
model_actor = PolicyTerm.create_actor("model", "AI Model")
admin_actor = PolicyTerm.create_actor("admin", "Administrator")

# Define relations
policy_engine.add_relation(
    PolicyRelation.permits(actor=model_actor, action=web_search)
)
policy_engine.add_relation(
    PolicyRelation.forbids(actor=model_actor, action=file_write)
)
policy_engine.add_relation(
    PolicyRelation.permits(actor=admin_actor, action=file_write)
)

# Create decision service
decision_service = DecisionService(
    policy_engine=policy_engine,
    ledger=node.ledger,
    identity=node.identity
)

# Evaluate decision
decision = decision_service.evaluate(
    actor="model",
    proposed_action="Execute web_search",
    tool="web_search",
    user_intent="Research",
    risk_level=1
)

print(f"Decision: {'ALLOW' if decision.allowed else 'DENY'}")
print(f"Reason: {decision.reason}")
```

---

## Policy System

### Policy Structure

Policies in Lexecon are built from three primitives:

1. **Terms** (Nodes): Actions, Data Classes, Actors, Resources
2. **Relations** (Edges): Permits, Forbids, Requires, Implies
3. **Constraints**: Additional conditions and guards

### Example Policy

```json
{
  "name": "Standard AI Safety Policy",
  "version": "1.0",
  "mode": "strict",
  "terms": [
    {
      "id": "action:read",
      "type": "action",
      "name": "read",
      "description": "Read data"
    },
    {
      "id": "action:write",
      "type": "action",
      "name": "write",
      "description": "Write data"
    },
    {
      "id": "data:pii",
      "type": "data_class",
      "name": "pii",
      "description": "Personally Identifiable Information",
      "sensitivity": "high"
    },
    {
      "id": "actor:model",
      "type": "actor",
      "name": "model",
      "description": "AI Model"
    },
    {
      "id": "actor:user",
      "type": "actor",
      "name": "user",
      "description": "Human User"
    }
  ],
  "relations": [
    {
      "type": "permits",
      "subject": "actor:model",
      "action": "action:read",
      "object": "data:public"
    },
    {
      "type": "forbids",
      "subject": "actor:model",
      "action": "action:write",
      "object": "data:pii"
    },
    {
      "type": "requires",
      "action": "action:write",
      "condition": "user_approval"
    }
  ],
  "constraints": [
    {
      "name": "high_risk_requires_confirmation",
      "condition": "risk_level >= 4",
      "action": "require_human_confirmation"
    }
  ]
}
```

### Policy Modes

#### Permissive Mode
```python
# Allow unless explicitly forbidden
policy = Policy(name="Permissive", mode="permissive")
# Actions are allowed by default
# Only explicitly forbidden actions are blocked
```

#### Strict Mode (Recommended)
```python
# Deny unless explicitly permitted
policy = Policy(name="Strict", mode="strict")
# Actions are denied by default
# Only explicitly permitted actions are allowed
```

#### Paranoid Mode
```python
# Deny high-risk actions unless human confirms
policy = Policy(name="Paranoid", mode="paranoid")
# All risk level >= 3 actions require human confirmation
# Provides extra safety for production systems
```

### Policy Evaluation Process

```
1. Normalize Request
   ↓
2. Load Active Policy (by version hash)
   ↓
3. Extract Actor, Action, Data Classes
   ↓
4. Check Explicit Forbids (immediate deny if matched)
   ↓
5. Check Explicit Permits (allow if matched and no forbid)
   ↓
6. Apply Policy Mode Default
   - Permissive → Allow
   - Strict → Deny
   - Paranoid → Require confirmation if risk >= 3
   ↓
7. Evaluate Constraints
   ↓
8. Generate Reason Trace
   ↓
9. Mint Capability Token (if allowed)
   ↓
10. Record to Ledger
    ↓
11. Sign and Return Decision
```

---

## Model Integration

### System Prompt Template

Lexecon provides system prompts to make foundation models governance-aware:

```
You are an AI assistant integrated with Lexecon governance protocol.

CRITICAL: Before executing ANY tool call, you must:
1. Send a decision request to the governance endpoint
2. Wait for approval and capability token
3. Include the capability token in the tool call
4. Handle denials gracefully by explaining to the user

Decision Request Format:
{
  "request_id": "<unique_id>",
  "actor": "model",
  "proposed_action": "<description>",
  "tool": "<tool_name>",
  "user_intent": "<user's goal>",
  "risk_level": <1-5>,
  "policy_mode": "strict"
}

Never attempt to bypass governance checks.
Never execute tools without valid capability tokens.
Always explain governance decisions to the user.
```

### OpenAI Integration

```python
from openai import OpenAI
from lexecon import LexeconClient

client = OpenAI()
lexecon = LexeconClient(base_url="http://localhost:8000")

def governed_tool_call(tool_name, tool_args, user_intent):
    # Request governance decision
    decision = lexecon.decide(
        actor="model",
        proposed_action=f"Execute {tool_name}",
        tool=tool_name,
        user_intent=user_intent,
        risk_level=2
    )

    if not decision.allowed:
        return {
            "error": "Governance denied",
            "reason": decision.reason
        }

    # Execute with capability token
    result = execute_tool(
        name=tool_name,
        arguments=tool_args,
        capability_token=decision.capability_token
    )

    return result

# Use in OpenAI function calling
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Search for AI governance papers"}],
    functions=[{
        "name": "web_search",
        "description": "Search the web (governance-gated)",
        "parameters": {...}
    }],
    function_call="auto"
)

if response.choices[0].message.function_call:
    tool_result = governed_tool_call(
        tool_name=response.choices[0].message.function_call.name,
        tool_args=response.choices[0].message.function_call.arguments,
        user_intent="Research AI governance"
    )
```

### Anthropic Integration

```python
from anthropic import Anthropic
from lexecon import LexeconClient

client = Anthropic()
lexecon = LexeconClient(base_url="http://localhost:8000")

# System prompt includes governance instructions
system_prompt = """
You are Claude, integrated with Lexecon governance.
Before using tools, request approval from governance endpoint.
"""

response = client.messages.create(
    model="claude-opus-4",
    system=system_prompt,
    messages=[{"role": "user", "content": "Search for AI safety research"}],
    tools=[{
        "name": "web_search",
        "description": "Search the web",
        "input_schema": {...}
    }]
)

# Intercept tool use and gate with Lexecon
if response.stop_reason == "tool_use":
    for tool_use in response.content:
        if tool_use.type == "tool_use":
            # Request governance decision
            decision = lexecon.decide(
                actor="model",
                proposed_action=f"Execute {tool_use.name}",
                tool=tool_use.name,
                user_intent="Research AI safety",
                risk_level=1
            )

            if decision.allowed:
                # Execute tool with token
                result = execute_tool(
                    tool_use.name,
                    tool_use.input,
                    decision.capability_token
                )
            else:
                # Return denial to model
                result = {"error": decision.reason}
```

---

## System Invariants

Lexecon enforces these core guarantees:

| Invariant | Description | Verification |
|-----------|-------------|--------------|
| **Deterministic Evaluation** | Same policy + same request = same decision | `pytest tests/test_determinism.py` |
| **Policy Version Pinning** | Every decision references exact policy hash | Check `decision.policy_version_hash` |
| **Ledger Immutability** | Events are hash-chained and tamper-evident | `lexecon ledger verify` |
| **Proof Linkage** | Decisions link to ledger entries | Check `decision.ledger_entry_hash` |
| **Deny-by-Default** | Unknown actions fail safely | Policy mode tests |
| **Tool Gating** | No tool execution without decision + token | Runtime enforcement |
| **Canonical Serialization** | Hashing uses stable JSON | Uses `sort_keys=True` |

---

## Compliance & Standards

### GDPR Compliance

| GDPR Requirement | Lexecon Feature |
|------------------|-----------------|
| **Data Minimization** | Policy enforces data class access limits |
| **Purpose Limitation** | `user_intent` field captures purpose |
| **Consent Management** | Policies can require explicit user approval |
| **Right to Audit** | Cryptographic ledger provides full audit trail |
| **Data Protection Impact Assessment** | Risk levels and decision traces |

### EU AI Act Compliance

| EU AI Act Requirement | Lexecon Feature |
|-----------------------|-----------------|
| **Risk Assessment** | 5-level risk classification system |
| **Human Oversight** | Paranoid mode requires human confirmation |
| **Transparency** | Decision reasoning traces |
| **Audit Trail** | Immutable ledger with signatures |
| **Robustness** | Injection resistance and fail-safe defaults |

### SOC 2 Compliance

| SOC 2 Control | Lexecon Feature |
|---------------|-----------------|
| **Access Controls** | Actor-based permissions in policies |
| **Audit Logging** | Tamper-proof ledger |
| **Change Management** | Policy versioning and hash pinning |
| **Monitoring** | Real-time decision logging |

---

## Development

### Development Setup

```bash
# Clone repository
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linters
make lint

# Format code
make format
```

### Development Commands (Makefile)

```bash
# Install dev dependencies
make install-dev

# Run tests with coverage
make test

# Run linters (flake8, mypy)
make lint

# Format code (black, isort)
make format

# Type checking
make typecheck

# Build package
make build

# Clean build artifacts
make clean

# Run development server
make dev-server
```

### Project Structure

```
Lexecon/
├── src/
│   └── lexecon/
│       ├── __init__.py              # Package initialization
│       ├── api/                     # FastAPI server
│       │   ├── server.py           # Main server setup
│       │   ├── routes.py           # API endpoints
│       │   └── models.py           # Request/response models
│       ├── capability/              # Capability token system
│       │   ├── token.py            # Token generation
│       │   └── verifier.py         # Token verification
│       ├── cli/                     # Command-line interface
│       │   ├── main.py             # CLI entry point
│       │   └── commands/           # Command implementations
│       ├── decision/                # Decision service
│       │   ├── service.py          # Core decision logic
│       │   └── models.py           # Decision models
│       ├── identity/                # Identity management
│       │   ├── keypair.py          # Ed25519 key management
│       │   └── node.py             # Node identity
│       ├── ledger/                  # Audit ledger
│       │   ├── chain.py            # Hash chain implementation
│       │   └── events.py           # Event types
│       └── policy/                  # Policy engine
│           ├── engine.py           # Policy evaluation
│           ├── terms.py            # Policy terms
│           └── relations.py        # Policy relations
├── tests/                           # Test suite
│   ├── test_policy.py
│   ├── test_decision.py
│   ├── test_ledger.py
│   ├── test_api.py
│   └── test_cli.py
├── docs/                            # Documentation
│   ├── PROTOCOL_SPEC.md
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── ADAPTER_GUIDE.md
│   └── LEGACY_UNIFICATION_MAP.md
├── examples/                        # Example files
│   ├── example_policy.json
│   ├── safe_request.json
│   └── risky_request.json
├── model_governance_pack/           # Model integration
│   ├── README.md
│   ├── prompts/                    # System prompts
│   ├── schemas/                    # JSON schemas
│   ├── adapters/                   # API adapters
│   └── examples/                   # Example transcripts
├── pyproject.toml                   # Project configuration
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
├── Makefile                         # Development commands
├── .flake8                         # Linter configuration
├── LICENSE                         # MIT license
├── CONTRIBUTING.md                 # Contribution guidelines
├── SECURITY.md                     # Security policy
└── README.md                       # This file
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lexecon --cov-report=html

# Run specific test file
pytest tests/test_policy.py

# Run specific test
pytest tests/test_policy.py::test_strict_mode_deny_by_default

# Run tests in parallel
pytest -n auto
```

### Test Categories

```bash
# Unit tests (fast)
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# Security tests
pytest tests/security/
```

### Writing Tests

```python
import pytest
from lexecon import PolicyEngine, DecisionService

def test_deny_by_default_in_strict_mode():
    """Test that strict mode denies unknown actions"""
    engine = PolicyEngine(mode="strict")

    decision = engine.evaluate(
        actor="model",
        action="unknown_action",
        data_classes=[]
    )

    assert decision.allowed is False
    assert "not explicitly permitted" in decision.reason

def test_capability_token_expiry():
    """Test that expired tokens are rejected"""
    from datetime import datetime, timedelta

    # Create expired token
    token = create_token(expiry=datetime.now() - timedelta(hours=1))

    # Verification should fail
    assert verify_token(token) is False
```

---

## Configuration

### Node Configuration

Configuration file location: `~/.lexecon/nodes/<node_id>/config.yaml`

```yaml
# Node Configuration
node_id: my-governance-node
version: "0.1.0"

# Server Settings
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  log_level: "info"

# Policy Settings
policy:
  default_mode: "strict"  # strict | permissive | paranoid
  auto_load: []           # Policies to load on startup
  cache_evaluations: true

# Capability Token Settings
capability:
  default_ttl: 300        # 5 minutes in seconds
  max_ttl: 3600          # 1 hour
  allow_refresh: false

# Ledger Settings
ledger:
  storage: "file"         # file | database
  path: "~/.lexecon/nodes/my-governance-node/ledger.db"
  auto_verify: true
  integrity_check_interval: 3600

# Identity Settings
identity:
  key_algorithm: "ed25519"
  key_path: "~/.lexecon/nodes/my-governance-node/keys/"

# Logging
logging:
  level: "info"           # debug | info | warning | error
  format: "json"          # json | text
  output: "stdout"        # stdout | file
  file_path: "~/.lexecon/nodes/my-governance-node/logs/lexecon.log"
```

### Environment Variables

```bash
# Node configuration
export LEXECON_NODE_ID=my-governance-node
export LEXECON_CONFIG_PATH=~/.lexecon/config.yaml

# Server settings
export LEXECON_HOST=0.0.0.0
export LEXECON_PORT=8000

# Policy settings
export LEXECON_POLICY_MODE=strict

# Logging
export LEXECON_LOG_LEVEL=info
export LEXECON_LOG_FORMAT=json
```

---

## Deployment

### Production Deployment with Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY pyproject.toml .

# Install application
RUN pip install -e .

# Create data directory
RUN mkdir -p /data/.lexecon

# Expose port
EXPOSE 8000

# Set environment variables
ENV LEXECON_NODE_ID=production-node
ENV LEXECON_HOST=0.0.0.0
ENV LEXECON_PORT=8000

# Run server
CMD ["lexecon", "server", "--node-id", "production-node"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  lexecon:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - lexecon-data:/data/.lexecon
    environment:
      - LEXECON_NODE_ID=production-node
      - LEXECON_POLICY_MODE=strict
      - LEXECON_LOG_LEVEL=info
    restart: unless-stopped

volumes:
  lexecon-data:
```

### Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lexecon
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lexecon
  template:
    metadata:
      labels:
        app: lexecon
    spec:
      containers:
      - name: lexecon
        image: lexecon/lexecon:latest
        ports:
        - containerPort: 8000
        env:
        - name: LEXECON_NODE_ID
          value: "k8s-node"
        - name: LEXECON_POLICY_MODE
          value: "strict"
        volumeMounts:
        - name: lexecon-storage
          mountPath: /data/.lexecon
      volumes:
      - name: lexecon-storage
        persistentVolumeClaim:
          claimName: lexecon-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: lexecon-service
spec:
  selector:
    app: lexecon
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Monitoring & Observability

```python
# Prometheus metrics endpoint
from prometheus_client import Counter, Histogram

decision_requests = Counter('lexecon_decision_requests_total', 'Total decision requests')
decision_latency = Histogram('lexecon_decision_latency_seconds', 'Decision latency')
decisions_allowed = Counter('lexecon_decisions_allowed_total', 'Allowed decisions')
decisions_denied = Counter('lexecon_decisions_denied_total', 'Denied decisions')

# Add to FastAPI app
from prometheus_client import make_asgi_app

app.mount("/metrics", make_asgi_app())
```

---

## Troubleshooting

### Common Issues

#### Issue: "Node not found"
```bash
# Check if node exists
lexecon node list

# If missing, initialize it
lexecon init --node-id my-node
```

#### Issue: "Policy evaluation failed"
```bash
# Validate policy syntax
lexecon policy validate --file policy.json

# Check loaded policies
lexecon policy list

# Reload policy
lexecon policy load --file policy.json --force
```

#### Issue: "Ledger verification failed"
```bash
# Check ledger integrity
lexecon ledger verify

# If corrupted, restore from backup
lexecon ledger restore --backup ledger_backup.json
```

#### Issue: "Port already in use"
```bash
# Check what's using the port
lsof -i :8000

# Start on different port
lexecon server --port 8001
```

### Debug Mode

```bash
# Enable debug logging
export LEXECON_LOG_LEVEL=debug
lexecon server --node-id my-node

# Or via CLI flag
lexecon server --node-id my-node --log-level debug
```

### Health Checks

```bash
# Check system health
lexecon doctor

# Check specific components
lexecon doctor --check policy
lexecon doctor --check ledger
lexecon doctor --check identity
```

---

## FAQ

### General Questions

**Q: What makes Lexecon different from traditional policy engines?**
A: Lexecon combines policy evaluation with cryptographic guarantees, runtime gating, and tamper-evident logging specifically designed for AI systems.

**Q: Can I use Lexecon with any AI model?**
A: Yes, Lexecon is model-agnostic. We provide adapters for OpenAI and Anthropic, and you can integrate any model.

**Q: Does Lexecon add significant latency?**
A: Typical decision latency is 5-20ms. For high-throughput systems, we recommend caching and batch evaluation.

**Q: Is Lexecon production-ready?**
A: Lexecon is currently in alpha (v0.1.0). We recommend thorough testing before production use.

### Security Questions

**Q: How are keys managed?**
A: Keys are stored in the node directory with filesystem permissions. For production, integrate with a key management service (KMS).

**Q: Can the ledger be tampered with?**
A: The ledger uses hash chaining and signatures. Any tampering will be detected by `lexecon ledger verify`.

**Q: What happens if the governance server is down?**
A: Fail-safe mode: deny all actions (configurable to allow based on cached policies).

### Integration Questions

**Q: How do I integrate with my existing auth system?**
A: Use the actor field to pass authenticated user/service identities. Policies can reference these actors.

**Q: Can I run Lexecon without a server?**
A: Yes, use the embedded mode with `LexeconNode` class for in-process evaluation.

**Q: How do I migrate from another governance system?**
A: See `docs/LEGACY_UNIFICATION_MAP.md` for migration guides from common systems.

---

## Roadmap

### v0.2.0 (Q1 2026)
- [ ] PostgreSQL ledger backend
- [ ] GraphQL API
- [ ] Policy templates library
- [ ] Web-based policy editor
- [ ] Enhanced monitoring dashboard

### v0.3.0 (Q2 2026)
- [ ] Multi-node federation
- [ ] Distributed ledger consensus
- [ ] Policy conflict detection
- [ ] Advanced risk scoring
- [ ] Integration with cloud KMS

### v1.0.0 (Q3 2026)
- [ ] Production hardening
- [ ] Formal security audit
- [ ] Enterprise features
- [ ] SaaS offering
- [ ] Comprehensive compliance reports

### Future
- [ ] Zero-knowledge proofs for private decisions
- [ ] On-chain ledger option (blockchain)
- [ ] Machine learning for policy recommendation
- [ ] Federated learning for risk models

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start for Contributors

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/Lexecon.git
cd Lexecon

# Create feature branch
git checkout -b feature/amazing-feature

# Install dev dependencies
make install-dev

# Make changes and test
make test
make lint

# Commit (follows conventional commits)
git commit -m "feat: add amazing feature"

# Push and create PR
git push origin feature/amazing-feature
```

### Contribution Areas

- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🧪 Test coverage
- 🎨 UI/UX improvements
- 🌐 Translations
- 🔧 DevOps and tooling

### Code of Conduct

We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

---

## Security

### Reporting Vulnerabilities

**Do not open public issues for security vulnerabilities.**

Email: security@lexicoding.systems

We will respond within 48 hours and work with you to address the issue.

### Security Best Practices

1. **Key Management**: Use KMS in production, never commit keys
2. **Network Security**: Use TLS for all API communication
3. **Access Control**: Limit access to node directories and configuration
4. **Monitoring**: Set up alerts for denied high-risk actions
5. **Updates**: Keep Lexecon and dependencies up to date

See [SECURITY.md](SECURITY.md) for detailed security policy.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Lexicoding Systems

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

- **Cryptography**: Uses [cryptography.io](https://cryptography.io/) for Ed25519 signatures
- **Web Framework**: Built on [FastAPI](https://fastapi.tiangolo.com/)
- **CLI Framework**: Uses [Click](https://click.palletsprojects.com/)
- **Inspiration**: Informed by work in capability-based security, zero-trust architecture, and AI safety research

---

## Support & Community

- **Documentation**: https://lexecon.readthedocs.io
- **GitHub Issues**: https://github.com/Lexicoding-systems/Lexecon/issues
- **GitHub Discussions**: https://github.com/Lexicoding-systems/Lexecon/discussions
- **Email**: contact@lexicoding.systems
- **Twitter**: [@LexicodingSys](https://twitter.com/LexicodingSys)

---

<div align="center">

**Built with ❤️ by Lexicoding Systems**

[⬆ Back to Top](#lexecon---lexical-governance-protocol)

</div>
