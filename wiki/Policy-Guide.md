# Policy Guide

Learn how to write effective governance policies for AI systems using Lexecon.

---

## What is a Policy?

A policy defines **what actions are permitted or forbidden** for different actors (users, models, systems) in your AI governance framework.

Policies in Lexecon are:
- **Declarative**: Describe rules, not implementation
- **Versioned**: Each policy has a version for audit trail
- **Composable**: Policies can reference and extend others
- **Verifiable**: Hash-pinned and cryptographically signed

---

## Policy Structure

A Lexecon policy consists of:

1. **Metadata**: ID, version, name, description
2. **Mode**: strict (deny-by-default) or permissive (allow-by-default)
3. **Terms**: The vocabulary (actions, actors, data classes)
4. **Relations**: Rules connecting terms (permits, forbids, requires)
5. **Constraints**: Additional conditions and limits

### Basic Policy Template

```json
{
  "policy_id": "pol_001",
  "version": "1.0.0",
  "name": "My Policy",
  "description": "Description of what this policy does",
  "mode": "strict",
  "terms": {
    "actions": [],
    "actors": [],
    "data_classes": []
  },
  "relations": {
    "permits": [],
    "forbids": [],
    "requires": []
  },
  "constraints": {}
}
```

---

## Policy Modes

### Strict Mode (Recommended)

**Deny-by-default**: Only explicitly permitted actions are allowed.

```json
{
  "mode": "strict"
}
```

Use when:
- ✅ Security is critical
- ✅ You want explicit control
- ✅ Working with sensitive data
- ✅ Compliance requirements

### Permissive Mode

**Allow-by-default**: Only explicitly forbidden actions are denied.

```json
{
  "mode": "permissive"
}
```

Use when:
- ⚠️ Rapid prototyping
- ⚠️ Internal tools with trusted users
- ⚠️ Low-risk environments

---

## Terms: Building Your Vocabulary

### Actions

Actions represent things that can be done.

```json
{
  "terms": {
    "actions": [
      {
        "id": "read_file",
        "description": "Read contents of a file",
        "risk_level": 1
      },
      {
        "id": "write_file",
        "description": "Write or modify a file",
        "risk_level": 3
      },
      {
        "id": "execute_code",
        "description": "Execute arbitrary code",
        "risk_level": 5
      },
      {
        "id": "search_web",
        "description": "Search the internet",
        "risk_level": 2
      }
    ]
  }
}
```

**Action Properties**:
- `id`: Unique identifier (snake_case)
- `description`: Human-readable description
- `risk_level`: 1 (low) to 5 (critical)

### Actors

Actors represent who can perform actions.

```json
{
  "terms": {
    "actors": [
      {
        "id": "model",
        "description": "AI model agent",
        "trust_level": 1
      },
      {
        "id": "user",
        "description": "Human user",
        "trust_level": 3
      },
      {
        "id": "admin",
        "description": "System administrator",
        "trust_level": 5
      }
    ]
  }
}
```

**Actor Properties**:
- `id`: Unique identifier
- `description`: Description
- `trust_level`: 1 (low trust) to 5 (high trust)

### Data Classes

Data classes represent types of data being accessed.

```json
{
  "terms": {
    "data_classes": [
      {
        "id": "public_data",
        "description": "Publicly available information",
        "sensitivity": 1
      },
      {
        "id": "user_data",
        "description": "User-specific information",
        "sensitivity": 3
      },
      {
        "id": "pii",
        "description": "Personally identifiable information",
        "sensitivity": 5
      }
    ]
  }
}
```

**Data Class Properties**:
- `id`: Unique identifier
- `description`: Description
- `sensitivity`: 1 (public) to 5 (highly sensitive)

---

## Relations: Defining Rules

### Permits

Allow an actor to perform an action.

```json
{
  "relations": {
    "permits": [
      {
        "actor": "model",
        "action": "search_web",
        "conditions": []
      },
      {
        "actor": "user",
        "action": "read_file",
        "data_class": "public_data",
        "conditions": []
      }
    ]
  }
}
```

### Forbids

Explicitly deny an action (takes precedence over permits).

```json
{
  "relations": {
    "forbids": [
      {
        "actor": "model",
        "action": "execute_code",
        "reason": "Models cannot execute arbitrary code"
      },
      {
        "actor": "model",
        "action": "write_file",
        "data_class": "system_files",
        "reason": "System files are protected"
      }
    ]
  }
}
```

### Requires

Add conditions that must be met.

```json
{
  "relations": {
    "requires": [
      {
        "action": "access_pii",
        "conditions": [
          {
            "type": "time_window",
            "start": "09:00",
            "end": "17:00"
          },
          {
            "type": "approval",
            "approver": "admin"
          }
        ]
      }
    ]
  }
}
```

---

## Conditions

Add fine-grained control with conditions.

### Time Windows

Restrict actions to specific times.

```json
{
  "type": "time_window",
  "start": "09:00",
  "end": "17:00",
  "timezone": "UTC",
  "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
}
```

### Rate Limits

Limit how often an action can be performed.

```json
{
  "type": "rate_limit",
  "max_requests": 100,
  "window": "1h"
}
```

### Approval Required

Require human approval.

```json
{
  "type": "approval",
  "approver": "admin",
  "timeout": "5m"
}
```

### Context Checks

Check request context.

```json
{
  "type": "context_check",
  "field": "user_role",
  "operator": "equals",
  "value": "developer"
}
```

---

## Example Policies

### Example 1: Basic Safe AI Policy

```json
{
  "policy_id": "pol_safe_ai",
  "version": "1.0.0",
  "name": "Basic Safe AI Policy",
  "description": "Safe defaults for AI model interactions",
  "mode": "strict",
  "terms": {
    "actions": [
      {"id": "search_web", "description": "Search internet", "risk_level": 2},
      {"id": "read_file", "description": "Read files", "risk_level": 2},
      {"id": "write_file", "description": "Write files", "risk_level": 4},
      {"id": "execute_code", "description": "Execute code", "risk_level": 5}
    ],
    "actors": [
      {"id": "model", "description": "AI model", "trust_level": 1}
    ],
    "data_classes": [
      {"id": "public_data", "description": "Public info", "sensitivity": 1},
      {"id": "user_data", "description": "User data", "sensitivity": 3}
    ]
  },
  "relations": {
    "permits": [
      {
        "actor": "model",
        "action": "search_web",
        "data_class": "public_data"
      },
      {
        "actor": "model",
        "action": "read_file",
        "data_class": "public_data"
      }
    ],
    "forbids": [
      {
        "actor": "model",
        "action": "execute_code",
        "reason": "Code execution not allowed for models"
      },
      {
        "actor": "model",
        "action": "write_file",
        "data_class": "user_data",
        "reason": "Cannot modify user data"
      }
    ]
  }
}
```

### Example 2: Customer Support Bot

```json
{
  "policy_id": "pol_support_bot",
  "version": "1.0.0",
  "name": "Customer Support Bot Policy",
  "mode": "strict",
  "terms": {
    "actions": [
      {"id": "read_ticket", "risk_level": 2},
      {"id": "update_ticket", "risk_level": 3},
      {"id": "access_customer_data", "risk_level": 4},
      {"id": "send_email", "risk_level": 3}
    ],
    "actors": [
      {"id": "support_bot", "trust_level": 2}
    ]
  },
  "relations": {
    "permits": [
      {
        "actor": "support_bot",
        "action": "read_ticket"
      },
      {
        "actor": "support_bot",
        "action": "update_ticket",
        "conditions": [
          {
            "type": "rate_limit",
            "max_requests": 50,
            "window": "1h"
          }
        ]
      },
      {
        "actor": "support_bot",
        "action": "access_customer_data",
        "data_class": "contact_info",
        "conditions": [
          {
            "type": "time_window",
            "start": "00:00",
            "end": "23:59"
          }
        ]
      }
    ],
    "forbids": [
      {
        "actor": "support_bot",
        "action": "access_customer_data",
        "data_class": "payment_info",
        "reason": "Bots cannot access payment information"
      }
    ]
  }
}
```

### Example 3: Data Analysis Agent

```json
{
  "policy_id": "pol_data_analyst",
  "version": "1.0.0",
  "name": "Data Analysis Agent Policy",
  "mode": "strict",
  "terms": {
    "actions": [
      {"id": "read_database", "risk_level": 3},
      {"id": "run_query", "risk_level": 3},
      {"id": "export_data", "risk_level": 4}
    ],
    "actors": [
      {"id": "analyst_agent", "trust_level": 2}
    ],
    "data_classes": [
      {"id": "analytics_data", "sensitivity": 2},
      {"id": "raw_data", "sensitivity": 3},
      {"id": "pii", "sensitivity": 5}
    ]
  },
  "relations": {
    "permits": [
      {
        "actor": "analyst_agent",
        "action": "read_database",
        "data_class": "analytics_data"
      },
      {
        "actor": "analyst_agent",
        "action": "run_query",
        "data_class": "analytics_data",
        "conditions": [
          {
            "type": "rate_limit",
            "max_requests": 1000,
            "window": "1h"
          }
        ]
      }
    ],
    "forbids": [
      {
        "actor": "analyst_agent",
        "action": "read_database",
        "data_class": "pii",
        "reason": "PII requires special handling"
      },
      {
        "actor": "analyst_agent",
        "action": "export_data",
        "reason": "Data export requires human approval"
      }
    ],
    "requires": [
      {
        "action": "export_data",
        "conditions": [
          {
            "type": "approval",
            "approver": "admin"
          }
        ]
      }
    ]
  }
}
```

---

## Best Practices

### 1. Start Strict

Always use `"mode": "strict"` for production systems.

```json
{
  "mode": "strict"  // ✅ Deny by default
}
```

### 2. Be Explicit

Clearly document why actions are permitted or forbidden.

```json
{
  "forbids": [
    {
      "actor": "model",
      "action": "delete_data",
      "reason": "Data deletion requires human approval per policy #123"
    }
  ]
}
```

### 3. Layer Defenses

Use multiple conditions for high-risk actions.

```json
{
  "action": "access_pii",
  "conditions": [
    {"type": "time_window", "start": "09:00", "end": "17:00"},
    {"type": "rate_limit", "max_requests": 10, "window": "1h"},
    {"type": "approval", "approver": "admin"}
  ]
}
```

### 4. Version Policies

Increment versions when making changes.

```json
{
  "policy_id": "pol_001",
  "version": "1.1.0",  // Updated from 1.0.0
  "changelog": "Added rate limits to data access"
}
```

### 5. Test Policies

Test policies before deploying to production.

```bash
# Test with safe request
lexecon decide --policy examples/test_policy.json \
  --actor model --action search_web

# Test with forbidden request
lexecon decide --policy examples/test_policy.json \
  --actor model --action execute_code
```

### 6. Monitor and Adjust

Review audit logs to refine policies.

```bash
# Check what's being denied
lexecon ledger show --decision DENIED --limit 100

# Analyze patterns
lexecon analyze --policy pol_001 --timerange 7d
```

---

## Policy Loading

### Via CLI

```bash
# Load from file
lexecon policy load --file my_policy.json --node-id my-node

# Validate before loading
lexecon policy validate --file my_policy.json

# List loaded policies
lexecon policy list --node-id my-node
```

### Via API

```bash
curl -X POST http://localhost:8000/policy \
  -H "Content-Type: application/json" \
  -d @my_policy.json
```

### Via Python

```python
from lexecon import LexeconClient

client = LexeconClient()

with open("my_policy.json") as f:
    policy = json.load(f)

client.load_policy(policy)
```

---

## Policy Composition

Extend existing policies:

```json
{
  "policy_id": "pol_002",
  "version": "1.0.0",
  "extends": "pol_001",
  "relations": {
    "permits": [
      {
        "actor": "admin",
        "action": "execute_code"
      }
    ]
  }
}
```

---

## Troubleshooting

### Policy Not Loading

```bash
# Check syntax
lexecon policy validate --file my_policy.json

# Check logs
lexecon logs --node-id my-node
```

### Unexpected Denials

```bash
# Test specific decision
lexecon decide --actor model --action test --dry-run

# View policy
lexecon policy show --policy-id pol_001
```

### Performance Issues

- Cache compiled policies
- Simplify complex conditions
- Use indexed data classes

---

## Next Steps

- **[[Examples]]** - More policy examples
- **[[API Reference]]** - Load policies via API
- **[[Security Best Practices]]** - Harden policies
- **[[Compliance Mapping]]** - Map to regulations
