# Lexecon Implementation Guide

A comprehensive guide for integrating Lexecon into your AI systems.

## Table of Contents

- [Overview](#overview)
- [When to Use Lexecon](#when-to-use-lexecon)
- [Architecture Patterns](#architecture-patterns)
- [Integration Strategies](#integration-strategies)
- [Step-by-Step Implementation](#step-by-step-implementation)
- [Policy Design](#policy-design)
- [Testing Strategies](#testing-strategies)
- [Production Deployment](#production-deployment)
- [Performance Optimization](#performance-optimization)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)
- [Real-World Examples](#real-world-examples)

---

## Overview

Lexecon provides cryptographic governance for AI systems by gating tool calls, enforcing policies, and maintaining tamper-evident audit trails. This guide walks you through implementing Lexecon in your application.

### What You'll Learn

- How to choose the right integration pattern
- How to implement governance in your code
- How to design effective policies
- How to deploy and monitor Lexecon in production
- How to optimize performance
- How to troubleshoot common issues

### Prerequisites

- Python 3.8+
- Basic understanding of AI systems and tool calling
- Familiarity with REST APIs
- Understanding of policy-based access control (helpful)

---

## When to Use Lexecon

### ✅ Good Use Cases

**Enterprise AI Assistants**
```
Problem: AI assistant needs access to company data but shouldn't exfiltrate
Solution: Lexecon gates data access, enforces read-only policies, logs all accesses
```

**Code Generation Tools**
```
Problem: AI code generator could write to arbitrary files or execute commands
Solution: Lexecon restricts file system access, blocks dangerous operations
```

**Customer Service Bots**
```
Problem: Bot needs customer data but must respect privacy regulations
Solution: Lexecon enforces data minimization, requires purpose specification
```

**Research & Analysis Agents**
```
Problem: Agent makes external API calls that could be expensive or dangerous
Solution: Lexecon controls which APIs can be called, enforces rate limits
```

### ❌ When NOT to Use Lexecon

- **Simple scripted bots** with no tool calling
- **Fully isolated systems** with no external access
- **Read-only applications** with no side effects
- **Ultra-low latency requirements** (< 1ms decision time)

---

## Architecture Patterns

### Pattern 1: Embedded Mode

**Use When**: Single application, low complexity, development/testing

```
┌─────────────────────────────────────┐
│        Your Application             │
│  ┌───────────────────────────────┐  │
│  │      AI Model (GPT-4)         │  │
│  └──────────┬────────────────────┘  │
│             │ tool call             │
│             ↓                        │
│  ┌───────────────────────────────┐  │
│  │   Lexecon (Embedded)          │  │
│  │   • PolicyEngine              │  │
│  │   • DecisionService           │  │
│  │   • Ledger                    │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Pros**:
- Simple setup
- No network latency
- Easy debugging

**Cons**:
- Can't share policies across applications
- No centralized audit trail
- Harder to update policies

**Code Example**:
```python
from lexecon import LexeconNode, PolicyEngine, DecisionService

# Initialize embedded node
node = LexeconNode(node_id="app-1")
policy = PolicyEngine(mode="strict")

# Load policy
policy.load_from_file("policy.json")

# Create decision service
decision_service = DecisionService(
    policy_engine=policy,
    ledger=node.ledger,
    identity=node.identity
)

# Use in your application
def call_tool_with_governance(tool_name, tool_args):
    # Request decision
    decision = decision_service.evaluate(
        actor="model",
        proposed_action=f"Execute {tool_name}",
        tool=tool_name,
        user_intent=get_user_intent(),
        risk_level=calculate_risk(tool_name)
    )

    if not decision.allowed:
        raise PermissionError(f"Denied: {decision.reason}")

    # Execute with capability token
    return execute_tool(tool_name, tool_args, decision.capability_token)
```

---

### Pattern 2: Client-Server Mode

**Use When**: Multiple applications, centralized governance, production

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Application 1  │  │   Application 2  │  │   Application 3  │
│   ┌──────────┐   │  │   ┌──────────┐   │  │   ┌──────────┐   │
│   │  Model   │   │  │   │  Model   │   │  │   │  Model   │   │
│   └────┬─────┘   │  │   └────┬─────┘   │  │   └────┬─────┘   │
└────────┼─────────┘  └────────┼─────────┘  └────────┼─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │ HTTP/HTTPS
                               ↓
                    ┌──────────────────────┐
                    │  Lexecon Server      │
                    │  ┌────────────────┐  │
                    │  │  API Layer     │  │
                    │  ├────────────────┤  │
                    │  │  Policy Engine │  │
                    │  ├────────────────┤  │
                    │  │  Ledger        │  │
                    │  └────────────────┘  │
                    └──────────────────────┘
```

**Pros**:
- Centralized policies
- Unified audit trail
- Easy to update policies
- Horizontal scaling

**Cons**:
- Network latency (5-20ms)
- Single point of failure (mitigate with HA)
- More complex deployment

**Code Example**:
```python
from lexecon import LexeconClient

# Initialize client
client = LexeconClient(
    base_url="https://governance.company.com",
    api_key=os.environ["LEXECON_API_KEY"]
)

def call_tool_with_governance(tool_name, tool_args):
    # Request decision from server
    decision = client.decide(
        actor="model",
        proposed_action=f"Execute {tool_name}",
        tool=tool_name,
        user_intent=get_user_intent(),
        risk_level=calculate_risk(tool_name)
    )

    if not decision.allowed:
        raise PermissionError(f"Denied: {decision.reason}")

    return execute_tool(tool_name, tool_args, decision.capability_token)
```

---

### Pattern 3: Sidecar Mode

**Use When**: Microservices, Kubernetes, need isolation

```
┌─────────────────────────────────────────────┐
│              Kubernetes Pod                  │
│  ┌───────────────┐      ┌────────────────┐  │
│  │  Application  │─────→│ Lexecon        │  │
│  │  Container    │      │ Sidecar        │  │
│  │               │←─────│ Container      │  │
│  └───────────────┘      └────────────────┘  │
│         │                       │            │
└─────────┼───────────────────────┼────────────┘
          │                       │
          │                       ↓
          │               ┌────────────────┐
          │               │ Central Ledger │
          └──────────────→│ (Optional)     │
                          └────────────────┘
```

**Pros**:
- Process isolation
- Easy to add to existing apps
- Kubernetes-native
- Independent scaling

**Cons**:
- More resource usage
- IPC or localhost network calls
- More complex troubleshooting

**Deployment**:
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-app
spec:
  template:
    spec:
      containers:
      # Main application
      - name: app
        image: your-app:latest
        env:
        - name: LEXECON_URL
          value: "http://localhost:8000"

      # Lexecon sidecar
      - name: lexecon
        image: lexecon/lexecon:latest
        ports:
        - containerPort: 8000
        env:
        - name: LEXECON_NODE_ID
          value: "app-sidecar"
        volumeMounts:
        - name: policy
          mountPath: /etc/lexecon/policy.json

      volumes:
      - name: policy
        configMap:
          name: lexecon-policy
```

---

## Integration Strategies

### Strategy 1: Wrapper Functions

**Best for**: Quick integration, minimal code changes

```python
# Before: Direct tool calls
def search_web(query):
    return requests.get(f"https://api.search.com?q={query}")

# After: Wrapped with governance
from lexecon import LexeconClient

lexecon = LexeconClient(base_url="http://localhost:8000")

def search_web(query, user_intent):
    # Request governance decision
    decision = lexecon.decide(
        actor="model",
        proposed_action="Execute web_search",
        tool="web_search",
        user_intent=user_intent,
        risk_level=1
    )

    if not decision.allowed:
        raise PermissionError(decision.reason)

    # Execute with token
    return requests.get(
        f"https://api.search.com?q={query}",
        headers={"X-Capability-Token": decision.capability_token.token_id}
    )
```

---

### Strategy 2: Decorator Pattern

**Best for**: Clean code, reusability

```python
from functools import wraps
from lexecon import LexeconClient

lexecon = LexeconClient(base_url="http://localhost:8000")

def governed(tool_name, risk_level=1):
    """Decorator to add governance to any function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, user_intent=None, **kwargs):
            # Request decision
            decision = lexecon.decide(
                actor="model",
                proposed_action=f"Execute {tool_name}",
                tool=tool_name,
                user_intent=user_intent or "Unknown",
                risk_level=risk_level
            )

            if not decision.allowed:
                raise PermissionError(decision.reason)

            # Call original function with token
            return func(*args, capability_token=decision.capability_token, **kwargs)
        return wrapper
    return decorator

# Usage
@governed("web_search", risk_level=1)
def search_web(query, capability_token=None):
    return requests.get(
        f"https://api.search.com?q={query}",
        headers={"X-Capability-Token": capability_token.token_id}
    )

# Call with governance
results = search_web("AI safety", user_intent="Research")
```

---

### Strategy 3: Middleware/Interceptor

**Best for**: Framework integration, consistent enforcement

```python
# FastAPI middleware example
from fastapi import FastAPI, Request
from lexecon import LexeconClient

app = FastAPI()
lexecon = LexeconClient(base_url="http://localhost:8000")

@app.middleware("http")
async def governance_middleware(request: Request, call_next):
    # Check if this is a tool call endpoint
    if request.url.path.startswith("/api/tools/"):
        tool_name = request.url.path.split("/")[-1]

        # Request governance decision
        decision = lexecon.decide(
            actor=request.headers.get("X-Actor", "unknown"),
            proposed_action=f"Execute {tool_name}",
            tool=tool_name,
            user_intent=request.headers.get("X-User-Intent", "Unknown"),
            risk_level=int(request.headers.get("X-Risk-Level", "3"))
        )

        if not decision.allowed:
            return JSONResponse(
                status_code=403,
                content={"error": "Governance denied", "reason": decision.reason}
            )

        # Add token to request context
        request.state.capability_token = decision.capability_token

    response = await call_next(request)
    return response

@app.post("/api/tools/web_search")
async def web_search(request: Request, query: str):
    token = request.state.capability_token
    # Execute with governance approval
    return {"results": perform_search(query, token)}
```

---

### Strategy 4: Agent Framework Integration

**Best for**: LangChain, AutoGPT, custom agent frameworks

```python
from langchain.agents import Tool, AgentExecutor
from langchain.chat_models import ChatOpenAI
from lexecon import LexeconClient

lexecon = LexeconClient(base_url="http://localhost:8000")

class GovernedTool(Tool):
    """LangChain tool with Lexecon governance."""

    def __init__(self, name, func, description, risk_level=1):
        super().__init__(name=name, func=self._governed_func, description=description)
        self._original_func = func
        self.risk_level = risk_level

    def _governed_func(self, *args, user_intent="", **kwargs):
        # Request governance decision
        decision = lexecon.decide(
            actor="model",
            proposed_action=f"Execute {self.name}",
            tool=self.name,
            user_intent=user_intent,
            risk_level=self.risk_level
        )

        if not decision.allowed:
            return f"Action denied: {decision.reason}"

        # Execute original function
        return self._original_func(*args, **kwargs)

# Create governed tools
tools = [
    GovernedTool(
        name="web_search",
        func=lambda q: search_api(q),
        description="Search the web",
        risk_level=1
    ),
    GovernedTool(
        name="file_write",
        func=lambda path, content: write_file(path, content),
        description="Write to file system",
        risk_level=4
    )
]

# Use in agent
agent = AgentExecutor.from_agent_and_tools(
    agent=ChatOpenAI(model="gpt-4"),
    tools=tools
)
```

---

## Step-by-Step Implementation

### Phase 1: Setup & Configuration

#### Step 1: Install Lexecon

```bash
# Install from PyPI
pip install lexecon

# Or from source
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon
pip install -e .
```

#### Step 2: Initialize Node

```bash
# Create governance node
lexecon init --node-id production-node

# This creates:
# ~/.lexecon/nodes/production-node/
#   ├── config.yaml        # Configuration
#   ├── keys/              # Cryptographic keys
#   │   ├── private_key.pem
#   │   └── public_key.pem
#   └── ledger.db         # Audit ledger
```

#### Step 3: Configure

```yaml
# ~/.lexecon/nodes/production-node/config.yaml
node_id: production-node
version: "0.1.0"

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

policy:
  default_mode: "strict"
  auto_load:
    - /etc/lexecon/policies/base_policy.json

capability:
  default_ttl: 300  # 5 minutes
  max_ttl: 3600    # 1 hour

ledger:
  storage: "file"
  path: "~/.lexecon/nodes/production-node/ledger.db"
  auto_verify: true

logging:
  level: "info"
  format: "json"
  output: "file"
  file_path: "/var/log/lexecon/lexecon.log"
```

---

### Phase 2: Policy Design

#### Step 4: Define Your Policy

```json
{
  "name": "AI Assistant Policy",
  "version": "1.0",
  "mode": "strict",
  "description": "Governance policy for internal AI assistant",

  "terms": [
    {
      "id": "action:read",
      "type": "action",
      "name": "read",
      "description": "Read data or information"
    },
    {
      "id": "action:write",
      "type": "action",
      "name": "write",
      "description": "Write or modify data"
    },
    {
      "id": "action:execute",
      "type": "action",
      "name": "execute",
      "description": "Execute code or commands"
    },
    {
      "id": "data:public",
      "type": "data_class",
      "name": "public",
      "description": "Publicly available data",
      "sensitivity": "low"
    },
    {
      "id": "data:internal",
      "type": "data_class",
      "name": "internal",
      "description": "Internal company data",
      "sensitivity": "medium"
    },
    {
      "id": "data:pii",
      "type": "data_class",
      "name": "pii",
      "description": "Personally identifiable information",
      "sensitivity": "high"
    },
    {
      "id": "actor:model",
      "type": "actor",
      "name": "model",
      "description": "AI model"
    },
    {
      "id": "actor:user",
      "type": "actor",
      "name": "user",
      "description": "Human user"
    }
  ],

  "relations": [
    {
      "type": "permits",
      "subject": "actor:model",
      "action": "action:read",
      "object": "data:public",
      "description": "Model can read public data"
    },
    {
      "type": "permits",
      "subject": "actor:model",
      "action": "action:read",
      "object": "data:internal",
      "conditions": ["user_approved"],
      "description": "Model can read internal data with user approval"
    },
    {
      "type": "forbids",
      "subject": "actor:model",
      "action": "action:write",
      "object": "data:pii",
      "description": "Model cannot write PII"
    },
    {
      "type": "forbids",
      "subject": "actor:model",
      "action": "action:execute",
      "object": "*",
      "description": "Model cannot execute code"
    }
  ],

  "constraints": [
    {
      "name": "high_risk_requires_approval",
      "condition": "risk_level >= 4",
      "action": "require_human_confirmation",
      "description": "High-risk actions need human approval"
    },
    {
      "name": "rate_limit_searches",
      "condition": "tool == 'web_search'",
      "action": "rate_limit",
      "parameters": {
        "max_calls": 10,
        "window_seconds": 60
      }
    }
  ]
}
```

#### Step 5: Load Policy

```bash
# Validate policy
lexecon policy validate --file policy.json

# Load policy
lexecon policy load --file policy.json

# Verify policy is loaded
lexecon policy list
```

---

### Phase 3: Integration

#### Step 6: Start Lexecon Server

```bash
# Start server
lexecon server --node-id production-node

# Or with systemd
sudo systemctl start lexecon

# Or with Docker
docker run -d \
  -p 8000:8000 \
  -v ~/.lexecon:/data/.lexecon \
  lexecon/lexecon:latest
```

#### Step 7: Integrate in Your Application

```python
# app.py
from lexecon import LexeconClient
from openai import OpenAI

# Initialize clients
openai_client = OpenAI()
lexecon_client = LexeconClient(base_url="http://localhost:8000")

def run_ai_assistant(user_message, user_intent):
    """Run AI assistant with governance."""

    # Get model response with tool calls
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}],
        tools=get_available_tools()
    )

    # If model wants to call a tool
    if response.choices[0].finish_reason == "tool_calls":
        for tool_call in response.choices[0].message.tool_calls:
            # Request governance decision
            decision = lexecon_client.decide(
                actor="model",
                proposed_action=f"Execute {tool_call.function.name}",
                tool=tool_call.function.name,
                user_intent=user_intent,
                risk_level=calculate_risk(tool_call.function.name)
            )

            if decision.allowed:
                # Execute tool with capability token
                result = execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments),
                    decision.capability_token
                )
                # Continue conversation with result...
            else:
                # Handle denial
                return f"Action denied: {decision.reason}"

    return response.choices[0].message.content
```

---

### Phase 4: Testing

#### Step 8: Write Tests

```python
# test_governance.py
import pytest
from lexecon import LexeconClient

@pytest.fixture
def lexecon():
    return LexeconClient(base_url="http://localhost:8000")

def test_allows_permitted_actions(lexecon):
    """Test that permitted actions are allowed."""
    decision = lexecon.decide(
        actor="model",
        proposed_action="Execute web_search",
        tool="web_search",
        user_intent="Research",
        risk_level=1
    )
    assert decision.allowed is True
    assert decision.capability_token is not None

def test_denies_forbidden_actions(lexecon):
    """Test that forbidden actions are denied."""
    decision = lexecon.decide(
        actor="model",
        proposed_action="Execute system_command",
        tool="execute",
        user_intent="Run command",
        risk_level=5
    )
    assert decision.allowed is False
    assert "forbidden" in decision.reason.lower()

def test_high_risk_requires_confirmation(lexecon):
    """Test that high-risk actions require confirmation."""
    decision = lexecon.decide(
        actor="model",
        proposed_action="Write to database",
        tool="database_write",
        user_intent="Update records",
        risk_level=4
    )
    # Should be denied or require confirmation
    assert decision.allowed is False or "confirmation" in decision.reason.lower()
```

#### Step 9: Run Integration Tests

```bash
# Start test server
lexecon server --node-id test-node --port 8001 &

# Run tests
pytest tests/test_governance.py

# Check coverage
pytest --cov=app --cov-report=html
```

---

### Phase 5: Deployment

#### Step 10: Deploy to Production

See [Production Deployment](#production-deployment) section below.

---

## Policy Design

### Policy Design Principles

#### 1. Start with Deny-by-Default

```json
{
  "mode": "strict",
  "description": "Deny all actions unless explicitly permitted"
}
```

**Why**: Safest default - you explicitly allow what's needed

#### 2. Use Risk-Based Classification

```python
def calculate_risk(tool_name):
    """Calculate risk level for a tool."""
    risk_levels = {
        "web_search": 1,       # Low risk - read-only
        "read_file": 2,        # Medium-low - local read
        "write_file": 4,       # High - can modify system
        "execute_code": 5,     # Critical - full control
        "delete_database": 5   # Critical - destructive
    }
    return risk_levels.get(tool_name, 3)  # Default to medium
```

#### 3. Group by Data Sensitivity

```json
{
  "terms": [
    {"id": "data:public", "sensitivity": "low"},
    {"id": "data:internal", "sensitivity": "medium"},
    {"id": "data:confidential", "sensitivity": "high"},
    {"id": "data:pii", "sensitivity": "critical"}
  ]
}
```

#### 4. Use Purpose Limitation

```json
{
  "relations": [
    {
      "type": "permits",
      "subject": "actor:model",
      "action": "action:read",
      "object": "data:customer",
      "conditions": ["purpose=support"],
      "description": "Can read customer data for support purposes only"
    }
  ]
}
```

---

### Common Policy Patterns

#### Pattern: Read-Only Access

```json
{
  "name": "Read-Only Policy",
  "relations": [
    {
      "type": "permits",
      "subject": "actor:model",
      "action": "action:read",
      "object": "*"
    },
    {
      "type": "forbids",
      "subject": "actor:model",
      "action": "action:write",
      "object": "*"
    },
    {
      "type": "forbids",
      "subject": "actor:model",
      "action": "action:delete",
      "object": "*"
    }
  ]
}
```

#### Pattern: Tiered Access

```json
{
  "name": "Tiered Access Policy",
  "relations": [
    {
      "type": "permits",
      "subject": "actor:basic_model",
      "action": "*",
      "object": "data:public"
    },
    {
      "type": "permits",
      "subject": "actor:advanced_model",
      "action": "*",
      "object": "data:internal"
    },
    {
      "type": "permits",
      "subject": "actor:admin_model",
      "action": "*",
      "object": "*",
      "conditions": ["audit_logged"]
    }
  ]
}
```

#### Pattern: Time-Based Access

```json
{
  "constraints": [
    {
      "name": "business_hours_only",
      "condition": "time.hour >= 9 and time.hour <= 17",
      "action": "allow",
      "else_action": "deny"
    }
  ]
}
```

#### Pattern: Rate Limiting

```json
{
  "constraints": [
    {
      "name": "api_rate_limit",
      "condition": "tool == 'external_api'",
      "action": "rate_limit",
      "parameters": {
        "max_calls": 100,
        "window_seconds": 3600,
        "per": "user"
      }
    }
  ]
}
```

---

## Testing Strategies

### Unit Testing

```python
def test_policy_engine_strict_mode():
    """Test policy engine in strict mode."""
    from lexecon.policy import PolicyEngine

    engine = PolicyEngine(mode="strict")

    # Should deny unknown actions
    decision = engine.evaluate(
        actor="model",
        action="unknown_action",
        data_classes=[]
    )
    assert decision.allowed is False

def test_capability_token_expiry():
    """Test that tokens expire."""
    from lexecon.capability import create_token
    from datetime import datetime, timedelta
    import time

    token = create_token(ttl=1)  # 1 second TTL
    time.sleep(2)

    assert verify_token(token) is False
```

### Integration Testing

```python
def test_end_to_end_governance_flow():
    """Test complete flow from decision to execution."""
    client = LexeconClient(base_url="http://localhost:8000")

    # 1. Request decision
    decision = client.decide(
        actor="model",
        proposed_action="Execute web_search",
        tool="web_search",
        user_intent="Research",
        risk_level=1
    )
    assert decision.allowed is True

    # 2. Verify token is valid
    assert client.verify_token(decision.capability_token) is True

    # 3. Execute tool with token
    result = execute_tool_with_token(
        "web_search",
        {"query": "test"},
        decision.capability_token
    )
    assert result is not None

    # 4. Verify ledger entry
    ledger_entry = client.get_ledger_entry(decision.ledger_entry_hash)
    assert ledger_entry.decision_hash == decision.decision_hash
```

### Load Testing

```python
# locustfile.py
from locust import HttpUser, task, between

class GovernanceUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def make_decision(self):
        self.client.post("/decide", json={
            "request_id": f"req_{uuid.uuid4()}",
            "actor": "model",
            "proposed_action": "Execute web_search",
            "tool": "web_search",
            "user_intent": "Research",
            "risk_level": 1,
            "policy_mode": "strict"
        })
```

```bash
# Run load test
locust -f locustfile.py --host http://localhost:8000
```

---

## Production Deployment

### Deployment Checklist

- [ ] **Security**
  - [ ] Keys stored in KMS (not filesystem)
  - [ ] TLS enabled for all communication
  - [ ] Firewall rules configured
  - [ ] Service account (non-root) configured
  - [ ] Secrets managed via vault/environment

- [ ] **High Availability**
  - [ ] Multiple instances (min 2)
  - [ ] Load balancer configured
  - [ ] Health checks enabled
  - [ ] Auto-scaling configured

- [ ] **Monitoring**
  - [ ] Metrics collection (Prometheus)
  - [ ] Log aggregation (ELK/Datadog)
  - [ ] Alerting configured
  - [ ] Dashboard created

- [ ] **Backup & Recovery**
  - [ ] Ledger backup scheduled
  - [ ] Policy backup scheduled
  - [ ] Recovery procedure documented
  - [ ] DR plan tested

- [ ] **Testing**
  - [ ] Integration tests passing
  - [ ] Load tests completed
  - [ ] Failure scenarios tested
  - [ ] Rollback procedure tested

### Production Configuration

```yaml
# production-config.yaml
node_id: production-1
version: "0.1.0"

server:
  host: "0.0.0.0"
  port: 8000
  workers: 8
  tls:
    enabled: true
    cert_file: /etc/lexecon/tls/cert.pem
    key_file: /etc/lexecon/tls/key.pem

policy:
  default_mode: "strict"
  auto_load:
    - /etc/lexecon/policies/production_policy.json
  cache_evaluations: true
  cache_ttl: 60

capability:
  default_ttl: 300
  max_ttl: 3600
  kms_provider: "aws"
  kms_key_id: "arn:aws:kms:us-east-1:123456789:key/abc-def"

ledger:
  storage: "postgresql"
  connection_string: "postgresql://user:pass@db:5432/lexecon"
  auto_verify: true
  integrity_check_interval: 3600

logging:
  level: "info"
  format: "json"
  output: "file"
  file_path: "/var/log/lexecon/lexecon.log"
  rotate: true
  max_size_mb: 100
  max_files: 10

monitoring:
  enabled: true
  prometheus_port: 9090
  alert_on_denied_high_risk: true
  alert_on_policy_changes: true
  alert_on_ledger_failures: true
```

---

## Performance Optimization

### 1. Policy Caching

```yaml
policy:
  cache_evaluations: true
  cache_ttl: 60  # seconds
  cache_size: 1000  # max entries
```

**Impact**: Reduces decision latency from 10-20ms to 1-2ms for repeated requests

### 2. Connection Pooling

```python
from lexecon import LexeconClient

# Use connection pooling
client = LexeconClient(
    base_url="http://localhost:8000",
    pool_size=20,
    pool_maxsize=50
)
```

### 3. Batch Decisions

```python
# Instead of individual decisions
decisions = []
for tool in tools:
    decision = client.decide(...)
    decisions.append(decision)

# Use batch API
decisions = client.decide_batch([
    {"actor": "model", "tool": "search", ...},
    {"actor": "model", "tool": "read", ...},
    {"actor": "model", "tool": "write", ...}
])
```

### 4. Async Operations

```python
import asyncio
from lexecon import AsyncLexeconClient

async def make_governed_call():
    client = AsyncLexeconClient(base_url="http://localhost:8000")

    # Non-blocking decision request
    decision = await client.decide_async(
        actor="model",
        tool="web_search",
        ...
    )

    if decision.allowed:
        result = await execute_tool_async(...)
        return result
```

### 5. Horizontal Scaling

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lexecon
spec:
  replicas: 5  # Multiple instances
  template:
    spec:
      containers:
      - name: lexecon
        image: lexecon/lexecon:latest
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: lexecon-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: lexecon
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Monitoring & Observability

### Metrics to Monitor

```python
# Key metrics
from prometheus_client import Counter, Histogram, Gauge

# Decision metrics
decision_requests_total = Counter(
    'lexecon_decision_requests_total',
    'Total decision requests'
)
decision_requests_allowed = Counter(
    'lexecon_decision_requests_allowed',
    'Allowed decisions'
)
decision_requests_denied = Counter(
    'lexecon_decision_requests_denied',
    'Denied decisions'
)
decision_latency = Histogram(
    'lexecon_decision_latency_seconds',
    'Decision latency'
)

# Ledger metrics
ledger_entries_total = Counter(
    'lexecon_ledger_entries_total',
    'Total ledger entries'
)
ledger_verification_failures = Counter(
    'lexecon_ledger_verification_failures',
    'Ledger verification failures'
)

# System metrics
active_tokens = Gauge(
    'lexecon_active_tokens',
    'Number of active capability tokens'
)
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Lexecon Governance",
    "panels": [
      {
        "title": "Decision Rate",
        "targets": [
          {
            "expr": "rate(lexecon_decision_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Allow/Deny Ratio",
        "targets": [
          {
            "expr": "lexecon_decision_requests_allowed / lexecon_decision_requests_total"
          }
        ]
      },
      {
        "title": "Decision Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, lexecon_decision_latency_seconds)"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules

```yaml
# prometheus-alerts.yaml
groups:
- name: lexecon
  rules:
  - alert: HighDenialRate
    expr: rate(lexecon_decision_requests_denied[5m]) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High denial rate detected"

  - alert: LedgerVerificationFailure
    expr: lexecon_ledger_verification_failures > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Ledger verification failed"

  - alert: HighLatency
    expr: histogram_quantile(0.95, lexecon_decision_latency_seconds) > 0.1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Decision latency above 100ms"
```

---

## Troubleshooting

### Common Issues

#### Issue: High Latency

**Symptoms**: Decision requests taking > 50ms

**Diagnosis**:
```bash
# Check metrics
curl http://localhost:9090/metrics | grep latency

# Check logs
tail -f /var/log/lexecon/lexecon.log | grep "latency"
```

**Solutions**:
1. Enable policy caching
2. Add connection pooling
3. Scale horizontally
4. Optimize policy complexity

#### Issue: Denied Decisions

**Symptoms**: Legitimate actions being denied

**Diagnosis**:
```bash
# Check recent denials
lexecon ledger show --last 100 | grep "allowed: false"

# Check policy
lexecon policy show --name production_policy
```

**Solutions**:
1. Review policy relations
2. Check policy mode (strict vs permissive)
3. Verify actor/action/data_class mapping
4. Check constraints and conditions

#### Issue: Ledger Verification Failures

**Symptoms**: `lexecon ledger verify` fails

**Diagnosis**:
```bash
# Run verification with details
lexecon ledger verify --verbose

# Check for corruption
lexecon ledger check-integrity
```

**Solutions**:
1. Restore from backup
2. Check for concurrent writes
3. Verify filesystem integrity
4. Check for tampering attempts

---

## Real-World Examples

### Example 1: Enterprise Customer Support Bot

```python
# support_bot.py
from lexecon import LexeconClient
from openai import OpenAI

lexecon = LexeconClient(base_url="https://governance.company.com")
openai = OpenAI()

def handle_support_request(user_message, customer_id):
    """Handle customer support request with governance."""

    # Determine user intent
    intent = classify_intent(user_message)

    # Get AI response
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a support assistant."},
            {"role": "user", "content": user_message}
        ],
        tools=[
            {"name": "get_customer_info", ...},
            {"name": "get_order_history", ...},
            {"name": "process_refund", ...}
        ]
    )

    # Process tool calls with governance
    if response.choices[0].finish_reason == "tool_calls":
        for tool_call in response.choices[0].message.tool_calls:
            # Calculate risk based on tool
            risk_level = {
                "get_customer_info": 2,
                "get_order_history": 2,
                "process_refund": 4
            }[tool_call.function.name]

            # Request governance decision
            decision = lexecon.decide(
                actor="support_bot",
                proposed_action=f"Execute {tool_call.function.name}",
                tool=tool_call.function.name,
                user_intent=intent,
                risk_level=risk_level,
                context={
                    "customer_id": customer_id,
                    "agent": "support_bot_v1"
                }
            )

            if decision.allowed:
                # Execute with token
                result = execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments),
                    decision.capability_token
                )
                # Log success
                logger.info(f"Executed {tool_call.function.name}", extra={
                    "decision_hash": decision.decision_hash,
                    "customer_id": customer_id
                })
            else:
                # Escalate to human
                logger.warning(f"Denied: {decision.reason}")
                return escalate_to_human(user_message, decision.reason)

    return response.choices[0].message.content
```

### Example 2: Code Generation Tool

```python
# code_generator.py
from lexecon import LexeconClient

lexecon = LexeconClient(base_url="http://localhost:8000")

def generate_code_with_governance(prompt, user_intent):
    """Generate code with file system governance."""

    # Generate code with AI
    generated_code = generate_code(prompt)

    # Parse file operations
    operations = parse_file_operations(generated_code)

    # Request governance for each operation
    for op in operations:
        decision = lexecon.decide(
            actor="code_generator",
            proposed_action=f"{op['type']} file {op['path']}",
            tool=f"file_{op['type']}",
            user_intent=user_intent,
            risk_level=calculate_file_risk(op['path']),
            context={
                "path": op['path'],
                "operation": op['type']
            }
        )

        if not decision.allowed:
            # Remove denied operations from code
            generated_code = remove_operation(generated_code, op)
            # Notify user
            print(f"⚠️  Removed {op['type']} to {op['path']}: {decision.reason}")

    return generated_code

def calculate_file_risk(path):
    """Calculate risk level for file operations."""
    # System files are high risk
    if path.startswith(('/etc/', '/sys/', '/proc/')):
        return 5
    # Home directory is medium risk
    elif path.startswith('/home/'):
        return 3
    # Project directory is low risk
    else:
        return 1
```

### Example 3: Research Assistant

```python
# research_assistant.py
from lexecon import LexeconClient
from anthropic import Anthropic

lexecon = LexeconClient(base_url="http://localhost:8000")
anthropic = Anthropic()

def research_with_governance(query, max_iterations=5):
    """Research assistant with governed tool use."""

    messages = [{"role": "user", "content": query}]

    for i in range(max_iterations):
        # Get Claude's response
        response = anthropic.messages.create(
            model="claude-opus-4",
            messages=messages,
            tools=[
                {"name": "web_search", ...},
                {"name": "read_paper", ...},
                {"name": "analyze_data", ...}
            ]
        )

        # Process tool uses
        if response.stop_reason == "tool_use":
            tool_results = []

            for tool_use in response.content:
                if tool_use.type == "tool_use":
                    # Request governance
                    decision = lexecon.decide(
                        actor="research_assistant",
                        proposed_action=f"Execute {tool_use.name}",
                        tool=tool_use.name,
                        user_intent="Research query",
                        risk_level=1,  # Research is typically low risk
                        context={"iteration": i}
                    )

                    if decision.allowed:
                        # Execute tool
                        result = execute_research_tool(
                            tool_use.name,
                            tool_use.input,
                            decision.capability_token
                        )
                        tool_results.append({
                            "tool_use_id": tool_use.id,
                            "content": result
                        })
                    else:
                        # Return error to model
                        tool_results.append({
                            "tool_use_id": tool_use.id,
                            "content": f"Access denied: {decision.reason}",
                            "is_error": True
                        })

            # Continue conversation with results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            # Final response
            return response.content[0].text

    return "Research completed"
```

---

## Next Steps

Now that you've implemented Lexecon:

1. **Monitor in Production**: Watch metrics, set up alerts
2. **Iterate on Policies**: Refine based on real usage
3. **Optimize Performance**: Profile and optimize hot paths
4. **Security Audit**: Review security posture regularly
5. **Scale**: Add nodes as traffic grows

## Additional Resources

- [Protocol Specification](PROTOCOL_SPEC.md) - Technical details
- [Adapter Guide](ADAPTER_GUIDE.md) - Model integrations
- [API Reference](../README.md#api-endpoints) - Complete API docs
- [Security Policy](../SECURITY.md) - Security best practices

---

**Questions or Issues?**
- GitHub Issues: https://github.com/Lexicoding-systems/Lexecon/issues
- GitHub Discussions: https://github.com/Lexicoding-systems/Lexecon/discussions
- Email: support@lexicoding.systems

**Happy Building!** 🚀
