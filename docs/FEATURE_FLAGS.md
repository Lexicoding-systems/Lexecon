# Feature Flags (Phase 5.4)

**Enterprise-grade feature flag management with LaunchDarkly integration**

## Overview

Lexecon supports feature flags for:
- **Gradual rollouts**: Deploy features to subset of users
- **A/B testing**: Test different implementations
- **Kill switches**: Quickly disable problematic features
- **Environment-specific config**: Different settings per environment
- **Compliance toggles**: Enable GDPR/HIPAA modes per customer

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Feature Flag System                    │
└─────────────────────────────────────────────────────────┘

Production:
  LaunchDarkly SDK ──► LaunchDarkly Cloud ──► Dashboard
       │                                         │
       ├─► User targeting                        │
       ├─► Percentage rollouts                   │
       └─► Real-time updates                     │
                                                  │
                                       Control flags in UI

Development:
  Environment Variables ──► FEATURE_FLAG_* ──► .env file
       │
       ├─► FEATURE_FLAG_NEW_DECISION_ENGINE=true
       ├─► FEATURE_FLAG_MFA_REQUIRED=false
       └─► FEATURE_FLAG_RATE_LIMIT_PER_USER=100
```

## Quick Start

### 1. Install LaunchDarkly SDK (Optional)

```bash
# For production with LaunchDarkly
pip install lexecon[features]

# Or install manually
pip install launchdarkly-server-sdk
```

### 2. Configure Environment

**For local development (environment variables):**

```bash
# .env
FEATURE_FLAGS_MODE=env
FEATURE_FLAG_NEW_DECISION_ENGINE=false
FEATURE_FLAG_MFA_REQUIRED=false
FEATURE_FLAG_RATE_LIMIT_PER_USER=100
```

**For production (LaunchDarkly):**

```bash
# .env
FEATURE_FLAGS_MODE=launchdarkly
LAUNCHDARKLY_SDK_KEY=sdk-xxxxx-xxxxx-xxxxx
```

### 3. Use in Code

```python
from lexecon.features import get_feature_flags, FeatureFlag

flags = get_feature_flags()

# Boolean flags
if flags.is_enabled(FeatureFlag.NEW_DECISION_ENGINE, user_id="user:alice"):
    result = new_decision_engine()
else:
    result = legacy_decision_engine()

# Numeric flags
rate_limit = flags.get_number(FeatureFlag.RATE_LIMIT_PER_USER, default=100)

# String flags
api_version = flags.get_string("api_version", default="v1")

# JSON flags
config = flags.get_json("experimental_config", default={"enabled": false})
```

## Available Feature Flags

### Security & Authentication

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `mfa_required` | bool | `false` | Require MFA for all users |
| `mfa_enrollment_mandatory` | bool | `false` | Force MFA enrollment on login |
| `password_expiration_enabled` | bool | `true` | Enable password expiration |
| `session_timeout_strict` | bool | `true` | Strict session timeout enforcement |

### Rate Limiting

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `rate_limiting_strict` | bool | `true` | Enable strict rate limiting |
| `rate_limit_per_user` | number | `100` | Requests per minute per user |
| `rate_limit_global` | number | `10000` | Global requests per minute |

### Decision Engine

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `new_decision_engine` | bool | `false` | Use new optimized decision engine |
| `decision_caching_enabled` | bool | `true` | Enable decision result caching |
| `decision_async_evaluation` | bool | `false` | Async decision evaluation |
| `decision_batch_processing` | bool | `false` | Batch decision processing |

### Ledger & Audit

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `ledger_compression_enabled` | bool | `true` | Compress ledger entries |
| `ledger_encryption_enabled` | bool | `true` | Encrypt ledger at rest |
| `audit_log_retention_days` | number | `90` | Audit log retention period |

### API Features

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `api_versioning_enabled` | bool | `true` | Enable API versioning |
| `api_deprecation_warnings` | bool | `true` | Show deprecation warnings |
| `graphql_enabled` | bool | `false` | Enable GraphQL API |
| `webhooks_enabled` | bool | `false` | Enable webhook notifications |

### Observability

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `metrics_detailed` | bool | `true` | Detailed Prometheus metrics |
| `tracing_enabled` | bool | `false` | Enable distributed tracing |
| `performance_profiling` | bool | `false` | Enable performance profiling |

### Compliance

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `gdpr_mode_enabled` | bool | `false` | Enable GDPR compliance features |
| `hipaa_mode_enabled` | bool | `false` | Enable HIPAA compliance features |
| `data_residency_enforcement` | bool | `false` | Enforce data residency rules |

### Experimental

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `experimental_features` | bool | `false` | Enable experimental features |
| `beta_features` | bool | `false` | Enable beta features |

## Usage Patterns

### 1. Feature Rollout

```python
# Gradually roll out new decision engine
flags = get_feature_flags()

if flags.is_enabled(
    FeatureFlag.NEW_DECISION_ENGINE,
    user_id=user.id,
    user_attributes={
        "email": user.email,
        "plan": user.plan,
        "signup_date": user.created_at.isoformat(),
    }
):
    # User gets new engine (LaunchDarkly can target by plan, date, etc.)
    return new_decision_engine.evaluate(request)
else:
    # User gets stable engine
    return legacy_decision_engine.evaluate(request)
```

### 2. Kill Switch

```python
# Quickly disable problematic feature
flags = get_feature_flags()

if flags.is_enabled(FeatureFlag.WEBHOOKS_ENABLED):
    try:
        send_webhook(event)
    except Exception as e:
        logger.error(f"Webhook failed: {e}")
        # Admin can disable webhooks instantly in LaunchDarkly dashboard
```

### 3. Dynamic Configuration

```python
# Configure rate limiter from feature flags
flags = get_feature_flags()

rate_limiter.configure(
    per_user=flags.get_number(FeatureFlag.RATE_LIMIT_PER_USER, default=100),
    global_limit=flags.get_number(FeatureFlag.RATE_LIMIT_GLOBAL, default=10000),
)
```

### 4. Compliance Modes

```python
# Enable compliance features per customer
flags = get_feature_flags()

if flags.is_enabled(FeatureFlag.GDPR_MODE_ENABLED, user_id=customer_id):
    # Add GDPR-specific headers, logging, data handling
    response.headers["X-GDPR-Compliant"] = "true"
    log_gdpr_access(user_id, resource_id)
    enforce_right_to_erasure()

if flags.is_enabled(FeatureFlag.HIPAA_MODE_ENABLED, user_id=customer_id):
    # Enable HIPAA audit logging, encryption
    enable_hipaa_audit_log()
    enforce_phi_encryption()
```

### 5. A/B Testing

```python
# Test different UI variations
flags = get_feature_flags()

ui_variant = flags.get_string(
    "ui_variant",
    user_id=user.id,
    default="control"
)

if ui_variant == "variant_a":
    return render_template("dashboard_v2.html")
elif ui_variant == "variant_b":
    return render_template("dashboard_v3.html")
else:
    return render_template("dashboard.html")
```

## LaunchDarkly Setup

### 1. Create LaunchDarkly Account

1. Sign up at https://launchdarkly.com/
2. Create project: "Lexecon"
3. Create environments: "staging", "production"

### 2. Get SDK Keys

```bash
# LaunchDarkly Dashboard → Account Settings → Projects → Lexecon

# Staging SDK Key
sdk-staging-xxxxx-xxxxx-xxxxx

# Production SDK Key
sdk-production-xxxxx-xxxxx-xxxxx
```

### 3. Configure in Kubernetes

```yaml
# infrastructure/helm/templates/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: lexecon-secrets
type: Opaque
stringData:
  launchdarkly-sdk-key: {{ .Values.secrets.launchdarklySDKKey }}
```

```yaml
# infrastructure/helm/values.yaml
secrets:
  launchdarklySDKKey: "sdk-production-xxxxx"

env:
  - name: LAUNCHDARKLY_SDK_KEY
    valueFrom:
      secretKeyRef:
        name: lexecon-secrets
        key: launchdarkly-sdk-key
  - name: FEATURE_FLAGS_MODE
    value: "launchdarkly"
```

### 4. Create Flags in Dashboard

```bash
# LaunchDarkly Dashboard → Feature Flags → Create Flag

Name: New Decision Engine
Key: new_decision_engine
Type: Boolean
Default: false (staging), false (production)

# Add targeting rules
IF user.plan = "enterprise"
  THEN serve true
IF user.email ends with "@beta-testers.com"
  THEN serve true
ELSE
  Percentage rollout: 10% true, 90% false
```

### 5. Monitor Flag Usage

LaunchDarkly provides:
- Real-time flag evaluation metrics
- User targeting analytics
- Flag change audit log
- Impact analysis

## Environment Variable Fallback

For local development without LaunchDarkly:

```bash
# .env
FEATURE_FLAGS_MODE=env
FEATURE_FLAG_NEW_DECISION_ENGINE=false
FEATURE_FLAG_MFA_REQUIRED=false
FEATURE_FLAG_RATE_LIMIT_PER_USER=100
FEATURE_FLAG_RATE_LIMIT_GLOBAL=10000
FEATURE_FLAG_DECISION_CACHING_ENABLED=true
```

Boolean values: `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off`
Numeric values: `100`, `1000.5`
JSON values: `{"key": "value"}`

## Testing

```python
# tests/test_features.py
def test_feature_flag_enabled(monkeypatch):
    monkeypatch.setenv("FEATURE_FLAG_NEW_DECISION_ENGINE", "true")

    flags = FeatureFlagService()
    assert flags.is_enabled("new_decision_engine") is True

def test_feature_flag_targeting():
    flags = FeatureFlagService()

    # Beta users get feature
    assert flags.is_enabled(
        "beta_feature",
        user_id="user:alice",
        user_attributes={"plan": "beta"}
    ) is True

    # Regular users don't
    assert flags.is_enabled(
        "beta_feature",
        user_id="user:bob",
        user_attributes={"plan": "free"}
    ) is False
```

## Best Practices

### 1. Use Typed Flag Access

```python
# Good: Type-safe with enum
if flags.is_enabled(FeatureFlag.NEW_DECISION_ENGINE):
    pass

# Bad: String typos not caught at compile time
if flags.is_enabled("new_desicion_engine"):  # Typo!
    pass
```

### 2. Provide Sensible Defaults

```python
# Good: Default works if flag system fails
rate_limit = flags.get_number(FeatureFlag.RATE_LIMIT_PER_USER, default=100)

# Bad: Default could break system
rate_limit = flags.get_number(FeatureFlag.RATE_LIMIT_PER_USER, default=0)
```

### 3. Use User Targeting

```python
# Good: Target by user attributes
flags.is_enabled(
    "feature",
    user_id=user.id,
    user_attributes={"plan": user.plan, "region": user.region}
)

# Limited: Can't target specific users
flags.is_enabled("feature")
```

### 4. Clean Up Old Flags

```python
# Remove flags after 100% rollout
# Flag: new_decision_engine → 100% enabled for 30 days
# Action: Delete flag, remove conditional code, new engine becomes default
```

### 5. Document Flag Purpose

```python
# Good: Clear purpose documented
FeatureFlag.MFA_REQUIRED = "mfa_required"  # Require MFA for all users

# Bad: Unclear purpose
FeatureFlag.FLAG_123 = "flag_123"  # What does this do?
```

## Cost

**LaunchDarkly Pricing:**
- **Starter**: Free (up to 1,000 MAU)
- **Pro**: $8/MAU (minimum $60/month)
- **Enterprise**: Custom pricing

**Environment Variable Mode:**
- Free (no external service)

**Recommendation for Lexecon:**
- **Staging**: Environment variables (free)
- **Production**: LaunchDarkly Starter (free < 1,000 MAU)
- **Scale**: LaunchDarkly Pro when you exceed 1,000 MAU

## Security

1. **SDK keys are secrets** - Store in Kubernetes Secrets, never in code
2. **Read-only SDK keys** - Use server-side SDK keys (read-only)
3. **Audit flag changes** - LaunchDarkly logs all flag modifications
4. **Principle of least privilege** - Limit who can modify production flags

## Troubleshooting

### LaunchDarkly Not Connecting

```python
# Check SDK initialization
flags = FeatureFlagService()
if flags.client is None:
    print("LaunchDarkly failed to initialize, using env fallback")
```

### Flag Not Updating

- LaunchDarkly updates flags in real-time (< 1 second)
- Check flag targeting rules in dashboard
- Verify user attributes match targeting criteria

### Environment Variables Not Working

```bash
# Check env var format
echo $FEATURE_FLAG_NEW_DECISION_ENGINE  # Should be: true/false

# Check service mode
echo $FEATURE_FLAGS_MODE  # Should be: env
```

## Next Steps

- **Phase 6**: Monitoring & Observability (Prometheus, Grafana, APM)
- **Phase 7**: Compliance (SOC 2, GDPR documentation)
- **Phase 8**: Optimization (performance tuning, cost reduction)

## References

- LaunchDarkly Documentation: https://docs.launchdarkly.com/
- LaunchDarkly Python SDK: https://docs.launchdarkly.com/sdk/server-side/python
- Feature Flag Best Practices: https://martinfowler.com/articles/feature-toggles.html
