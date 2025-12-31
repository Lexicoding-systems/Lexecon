# API Reference

Complete reference for Lexecon's REST API and Python SDK.

---

## REST API

Base URL: `http://localhost:8000` (default)

All endpoints return JSON responses.

---

## Authentication

Currently, Lexecon uses node-based authentication. Future versions will support:
- API keys
- OAuth 2.0
- mTLS

---

## Endpoints

### POST /decide

Request a governance decision for a proposed action.

**Request Body**:
```json
{
  "request_id": "string (optional)",
  "actor": "string (required)",
  "proposed_action": "string (required)",
  "tool": "string (required)",
  "user_intent": "string (optional)",
  "risk_level": "integer (1-5, optional)",
  "policy_mode": "string (optional, 'strict' or 'permissive')",
  "context": "object (optional)"
}
```

**Parameters**:
- `request_id`: Unique identifier for request (auto-generated if not provided)
- `actor`: Who is requesting the action (e.g., "model", "user")
- `proposed_action`: Human-readable description of action
- `tool`: Tool/function name to execute
- `user_intent`: Original user intent/prompt
- `risk_level`: Risk assessment (1=low, 5=critical)
- `policy_mode`: Override policy mode
- `context`: Additional context data

**Response** (200 OK):
```json
{
  "decision_id": "dec_abc123",
  "decision": "ALLOWED",
  "reason": "Action explicitly permitted by policy",
  "capability_token": "cap_xyz789...",
  "expires_at": "2024-01-15T10:30:00Z",
  "policy_version": "1.0.0",
  "signature": "ed25519:...",
  "chain_hash": "sha256:...",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

**Decision Values**:
- `ALLOWED`: Action is permitted
- `DENIED`: Action is forbidden
- `REQUIRES_REVIEW`: Needs human approval

**Response** (400 Bad Request):
```json
{
  "error": "Invalid request",
  "details": "Missing required field: actor"
}
```

**Response** (500 Internal Server Error):
```json
{
  "error": "Policy evaluation failed",
  "details": "..."
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "actor": "model",
    "proposed_action": "Search the web",
    "tool": "web_search",
    "user_intent": "Find AI governance papers",
    "risk_level": 1
  }'
```

---

### POST /verify

Verify a capability token.

**Request Body**:
```json
{
  "capability_token": "string (required)",
  "action": "string (optional)",
  "actor": "string (optional)"
}
```

**Response** (200 OK):
```json
{
  "valid": true,
  "token_id": "cap_xyz789",
  "decision_id": "dec_abc123",
  "action": "web_search",
  "actor": "model",
  "expires_at": "2024-01-15T10:30:00Z",
  "policy_version": "1.0.0"
}
```

**Response** (Invalid Token):
```json
{
  "valid": false,
  "reason": "Token expired"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "capability_token": "cap_xyz789..."
  }'
```

---

### GET /health

Health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "node_id": "my-governance-node",
  "policy_loaded": true,
  "ledger_entries": 42
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

---

### GET /ledger

Query the audit ledger.

**Query Parameters**:
- `limit`: Number of entries to return (default: 10, max: 100)
- `offset`: Pagination offset (default: 0)
- `decision_id`: Filter by decision ID
- `actor`: Filter by actor
- `start_time`: Filter by start timestamp (ISO 8601)
- `end_time`: Filter by end timestamp (ISO 8601)

**Response** (200 OK):
```json
{
  "total": 150,
  "limit": 10,
  "offset": 0,
  "entries": [
    {
      "entry_id": "ent_001",
      "timestamp": "2024-01-15T10:00:00Z",
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
  ]
}
```

**Example**:
```bash
# Get recent entries
curl http://localhost:8000/ledger?limit=10

# Filter by actor
curl http://localhost:8000/ledger?actor=model

# Filter by time range
curl "http://localhost:8000/ledger?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z"
```

---

### GET /policy

View loaded policy.

**Response** (200 OK):
```json
{
  "policy_id": "pol_001",
  "version": "1.0.0",
  "name": "Basic Safety Policy",
  "mode": "strict",
  "loaded_at": "2024-01-15T09:00:00Z",
  "terms": {
    "actions": [...],
    "actors": [...],
    "data_classes": [...]
  },
  "relations": {
    "permits": [...],
    "forbids": [...],
    "requires": [...]
  }
}
```

**Example**:
```bash
curl http://localhost:8000/policy
```

---

### GET /node/info

Get node information.

**Response** (200 OK):
```json
{
  "node_id": "my-governance-node",
  "public_key": "8f3a2c1d...",
  "created_at": "2024-01-15T08:00:00Z",
  "ledger_entries": 42,
  "policy_loaded": true,
  "version": "0.1.0"
}
```

**Example**:
```bash
curl http://localhost:8000/node/info
```

---

## Python SDK

Install with: `pip install lexecon`

### LexeconClient

Main client class for interacting with Lexecon.

```python
from lexecon import LexeconClient

# Initialize client
client = LexeconClient(base_url="http://localhost:8000")

# Or with configuration
client = LexeconClient(
    base_url="http://localhost:8000",
    timeout=30,
    verify_ssl=True
)
```

#### decide()

Request a governance decision.

```python
decision = client.decide(
    actor="model",
    action="search_web",
    tool="web_search",
    intent="Research AI governance",
    risk_level=1,
    context={"user_id": "user_123"}
)

print(f"Decision: {decision.decision}")
print(f"Reason: {decision.reason}")
print(f"Token: {decision.capability_token}")
```

**Parameters**:
- `actor` (str): Who is requesting
- `action` (str): What action to perform
- `tool` (str): Tool/function name
- `intent` (str, optional): User intent
- `risk_level` (int, optional): 1-5 risk level
- `context` (dict, optional): Additional context

**Returns**: `Decision` object with:
- `decision_id`: Unique ID
- `decision`: ALLOWED/DENIED/REQUIRES_REVIEW
- `reason`: Explanation
- `capability_token`: Authorization token (if allowed)
- `expires_at`: Token expiration
- `policy_version`: Policy version used
- `signature`: Cryptographic signature
- `chain_hash`: Ledger hash

#### verify()

Verify a capability token.

```python
result = client.verify(
    capability_token="cap_xyz789...",
    action="web_search",
    actor="model"
)

if result.valid:
    print("Token is valid")
else:
    print(f"Token invalid: {result.reason}")
```

**Parameters**:
- `capability_token` (str): Token to verify
- `action` (str, optional): Expected action
- `actor` (str, optional): Expected actor

**Returns**: `VerificationResult` with:
- `valid`: Boolean
- `reason`: Explanation if invalid
- `token_id`: Token ID
- `expires_at`: Expiration time

#### get_ledger()

Query the audit ledger.

```python
# Get recent entries
entries = client.get_ledger(limit=10)

# Filter by actor
entries = client.get_ledger(actor="model", limit=20)

# Filter by time range
from datetime import datetime, timedelta
start = datetime.now() - timedelta(days=1)
end = datetime.now()
entries = client.get_ledger(
    start_time=start,
    end_time=end
)

for entry in entries:
    print(f"{entry.timestamp}: {entry.action} -> {entry.decision}")
```

**Parameters**:
- `limit` (int, optional): Max entries (default: 10)
- `offset` (int, optional): Pagination offset
- `decision_id` (str, optional): Filter by decision ID
- `actor` (str, optional): Filter by actor
- `start_time` (datetime, optional): Start time
- `end_time` (datetime, optional): End time

**Returns**: List of `LedgerEntry` objects

#### get_policy()

Get loaded policy.

```python
policy = client.get_policy()

print(f"Policy: {policy.name}")
print(f"Version: {policy.version}")
print(f"Mode: {policy.mode}")
```

**Returns**: `Policy` object

#### health_check()

Check server health.

```python
health = client.health_check()

if health.status == "healthy":
    print("Server is healthy")
```

**Returns**: `HealthStatus` object

---

### Async Client

For async/await support:

```python
from lexecon import AsyncLexeconClient

async def make_decision():
    client = AsyncLexeconClient(base_url="http://localhost:8000")
    
    decision = await client.decide(
        actor="model",
        action="search_web",
        tool="web_search"
    )
    
    return decision

# Use in async context
import asyncio
decision = asyncio.run(make_decision())
```

---

## Response Models

### Decision

```python
class Decision:
    decision_id: str
    decision: str  # ALLOWED, DENIED, REQUIRES_REVIEW
    reason: str
    capability_token: Optional[str]
    expires_at: Optional[datetime]
    policy_version: str
    signature: str
    chain_hash: str
    timestamp: datetime
```

### LedgerEntry

```python
class LedgerEntry:
    entry_id: str
    timestamp: datetime
    event_type: str
    decision_id: str
    actor: str
    action: str
    decision: str
    policy_version: str
    prev_hash: str
    entry_hash: str
    signature: str
```

### Policy

```python
class Policy:
    policy_id: str
    version: str
    name: str
    mode: str
    loaded_at: datetime
    terms: Dict
    relations: Dict
```

---

## Error Handling

The SDK raises specific exceptions:

```python
from lexecon.exceptions import (
    LexeconError,
    DecisionError,
    VerificationError,
    PolicyError,
    ConnectionError
)

try:
    decision = client.decide(actor="model", action="test")
except DecisionError as e:
    print(f"Decision failed: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
except LexeconError as e:
    print(f"General error: {e}")
```

---

## Rate Limiting

API requests may be rate limited. The response includes headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

When rate limited, you'll receive a 429 status:

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Webhooks

Configure webhooks for specific events:

```python
# Coming in future version
client.configure_webhook(
    url="https://myapp.com/webhook",
    events=["decision.made", "policy.updated"]
)
```

---

## Examples

### Example 1: Simple Decision

```python
from lexecon import LexeconClient

client = LexeconClient()

decision = client.decide(
    actor="model",
    action="read_file",
    tool="file_reader",
    intent="Read configuration file"
)

if decision.decision == "ALLOWED":
    # Proceed with action
    result = execute_tool(decision.capability_token)
else:
    print(f"Denied: {decision.reason}")
```

### Example 2: Verify Before Execution

```python
def execute_with_token(token, action):
    # Verify token first
    verification = client.verify(
        capability_token=token,
        action=action
    )
    
    if not verification.valid:
        raise PermissionError(verification.reason)
    
    # Execute action
    return perform_action(action)
```

### Example 3: Audit Trail Query

```python
from datetime import datetime, timedelta

# Get all decisions from last hour
start_time = datetime.now() - timedelta(hours=1)
entries = client.get_ledger(
    start_time=start_time,
    limit=100
)

# Analyze decisions
allowed = sum(1 for e in entries if e.decision == "ALLOWED")
denied = sum(1 for e in entries if e.decision == "DENIED")

print(f"Allowed: {allowed}, Denied: {denied}")
```

---

## Next Steps

- **[[Policy Guide]]** - Learn to write policies
- **[[Examples]]** - More code examples
- **[[CLI Commands]]** - CLI reference
- **[[Security Best Practices]]** - Secure your deployment
