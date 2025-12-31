# Model Adapter Integration Guide

This guide explains how to integrate Lexecon governance with foundation models using the provided adapters.

## Overview

Lexecon adapters intercept tool calls from AI models and route them through the governance system before execution. This ensures all AI actions are policy-compliant and auditable.

## Architecture

```
User Request
    ↓
AI Model (OpenAI/Anthropic)
    ↓
Tool Call Proposed
    ↓
Governance Adapter ← → Lexecon API Server
    ↓                      ↓
Policy Evaluation      Ledger Entry
    ↓
Decision (Permit/Deny)
    ↓
Tool Execution (if permitted)
    ↓
Result + Capability Token
    ↓
AI Model (final response)
    ↓
User
```

## Quick Start

### 1. Start Governance Server

```bash
cd ~/Lexecon
python3 -m lexecon.cli.main server --port 8000
```

### 2. Load a Policy

```python
import requests
import json

# Load example policy
with open("examples/example_policy.json") as f:
    policy = json.load(f)

requests.post(
    "http://localhost:8000/policies/load",
    json={"policy": policy}
)
```

### 3. Create Adapter

#### OpenAI

```python
from model_governance_pack.adapters.openai_adapter import OpenAIGovernanceAdapter

adapter = OpenAIGovernanceAdapter(
    governance_url="http://localhost:8000",
    actor="model"
)
```

#### Anthropic

```python
from model_governance_pack.adapters.anthropic_adapter import AnthropicGovernanceAdapter

adapter = AnthropicGovernanceAdapter(
    governance_url="http://localhost:8000",
    actor="model"
)
```

### 4. Register Tools

```python
def search_web(query: str, max_results: int = 10):
    # Your tool implementation
    return {"results": [...]}

adapter.register_tool("search_web", search_web)
```

### 5. Intercept Tool Calls

#### Manual Interception

```python
result = adapter.intercept_tool_call(
    tool_name="search_web",
    tool_args={"query": "AI governance", "max_results": 5},
    user_intent="Research AI safety frameworks",
    risk_level=1
)

if result['governance_decision']['decision'] == 'permit':
    # Tool was executed
    print(result['content'])
else:
    # Tool was denied
    print(result['governance_decision']['reasoning'])
```

#### Automatic Integration (OpenAI)

```python
from openai import OpenAI

client = OpenAI()

response = adapter.create_governed_completion(
    client=client,
    messages=[...],
    tools=[...],
    user_intent="Research AI governance",
    model="gpt-4"
)
```

#### Automatic Integration (Anthropic)

```python
from anthropic import Anthropic

client = Anthropic()

response = adapter.create_governed_message(
    client=client,
    messages=[...],
    tools=[...],
    user_intent="Research AI governance",
    model="claude-3-sonnet-20240229"
)
```

## Adapter API Reference

### Base GovernanceAdapter

All adapters inherit from `GovernanceAdapter`:

#### Methods

**`check_health() -> bool`**
- Check if governance service is available

**`request_decision(tool_name, tool_args, user_intent, data_classes=None, risk_level=1) -> dict`**
- Request governance decision for a tool call
- Returns decision response with permit/deny and capability token

**`is_permitted(decision: dict) -> bool`**
- Check if decision permits the action

**`get_capability_token(decision: dict) -> Optional[dict]`**
- Extract capability token from decision

**`verify_token(token_id, action, tool) -> bool`**
- Verify a capability token is valid for the action

### OpenAIGovernanceAdapter

Specific to OpenAI models:

**`register_tool(name: str, function: Callable)`**
- Register a tool function

**`intercept_tool_call(tool_name, tool_args, user_intent="", risk_level=1, execute_if_permitted=True) -> dict`**
- Intercept and govern a tool call

**`process_tool_calls(tool_calls: list, user_intent="") -> list`**
- Process multiple tool calls from OpenAI response

**`create_governed_completion(client, messages, tools, user_intent="", **kwargs)`**
- Create a governed chat completion with automatic tool execution

### AnthropicGovernanceAdapter

Specific to Anthropic models:

**`register_tool(name: str, function: Callable)`**
- Register a tool function

**`intercept_tool_call(tool_name, tool_args, user_intent="", risk_level=1, execute_if_permitted=True) -> dict`**
- Intercept and govern a tool use

**`process_tool_uses(tool_uses: list, user_intent="") -> list`**
- Process multiple tool_use blocks from Claude response

**`create_governed_message(client, messages, tools, user_intent="", **kwargs)`**
- Create a governed message with automatic tool execution

## Verification

### Verify Decision Response

```python
from model_governance_pack.adapters.verification import GovernanceVerifier

verifier = GovernanceVerifier()

# Verify a decision against the ledger
result = verifier.verify_decision(decision_response)
print(f"Valid: {result['verified']}")
```

### Verify Capability Token

```python
token_result = verifier.verify_capability_token(capability_token)
print(f"Valid: {token_result['valid']}")
print(f"Time Remaining: {token_result['time_remaining']} seconds")
```

### Verify Ledger Integrity

```python
integrity = verifier.verify_ledger_integrity()
print(f"Chain Valid: {integrity['valid']}")
print(f"Entries Verified: {integrity['entries_verified']}")
```

### Get Audit Report

```python
report = verifier.get_audit_report()
print(f"Total Entries: {report['total_entries']}")
print(f"Event Types: {report['event_type_counts']}")
```

## System Prompts

Include governance instructions in your system prompts:

### Full Version

See `model_governance_pack/prompts/system_prompt.md`

### Concise Version

```
You operate under Lexecon governance. All tool calls require policy approval.
If approved, you receive a capability token. If denied, explain the denial
reason to the user and suggest alternatives.
```

## Response Handling

### Permitted Action

```json
{
  "decision": "permit",
  "reasoning": "Permitted by 1 rule(s), no conflicts",
  "capability_token": {
    "token_id": "tok_abc123",
    "scope": {"action": "search", "tool": "web_search"},
    "expiry": "2025-12-31T23:59:59"
  },
  "ledger_entry_hash": "3d10482a...",
  "policy_version_hash": "5a0fdb65..."
}
```

### Denied Action

```json
{
  "decision": "deny",
  "reasoning": "Denied by default (no explicit permission)",
  "capability_token": null,
  "ledger_entry_hash": "3d10482a...",
  "policy_version_hash": "5a0fdb65..."
}
```

## Error Handling

### Governance Service Unavailable

```python
if not adapter.check_health():
    # Fail-safe: deny by default
    print("Governance service unavailable - denying action")
```

### Tool Execution Failure

```python
try:
    result = adapter.intercept_tool_call(...)
    if result.get('is_error') or result.get('error'):
        print(f"Error: {result.get('content') or result.get('message')}")
except Exception as e:
    print(f"Execution failed: {str(e)}")
```

## Best Practices

1. **Always Check Health**: Verify governance service is available before starting
2. **Provide Context**: Include meaningful user intent in decision requests
3. **Verify Tokens**: Validate capability tokens before executing tools
4. **Handle Denials Gracefully**: Explain denials to users and suggest alternatives
5. **Audit Regularly**: Periodically verify ledger integrity
6. **Fail-Safe**: Default to deny if governance is unavailable
7. **Log Everything**: Maintain local logs of governance decisions
8. **Token Cleanup**: Remove expired tokens periodically

## Risk Levels

Use appropriate risk levels for different operations:

- **1 (Low)**: Read-only operations, searches, queries
- **2 (Medium)**: Data processing, transformations
- **3 (Moderate)**: File operations, API calls
- **4 (High)**: System modifications, privileged operations
- **5 (Critical)**: Irreversible actions, security-sensitive operations

## Example Workflows

### Complete OpenAI Integration

See `model_governance_pack/examples/openai_example.py`

### Complete Anthropic Integration

See `model_governance_pack/examples/anthropic_example.py`

## Troubleshooting

### "Governance service error"

- Ensure governance server is running: `curl http://localhost:8000/health`
- Check network connectivity
- Verify URL is correct in adapter initialization

### "Tool not registered"

- Ensure tool function is registered: `adapter.register_tool(name, func)`
- Check tool name matches exactly

### "Token has expired"

- Capability tokens expire after 5 minutes by default
- Request new decision for continued operation
- Check system clock synchronization

### "Action denied by governance"

- Verify policy is loaded: `curl http://localhost:8000/policies`
- Check policy rules permit the action
- Review policy mode (strict vs permissive)
- Ensure actor and action match policy terms

## Next Steps

- Review example policies in `examples/`
- Customize policies for your use case
- Implement custom tools
- Set up monitoring and alerting
- Configure backup governance servers for high availability
