# Monitoring & Observability (Phase 6)

**Enterprise-grade monitoring with Prometheus, Grafana, OpenTelemetry, and comprehensive alerting**

## Overview

Lexecon's monitoring stack provides complete observability across:
- **Metrics**: Prometheus for time-series metrics
- **Dashboards**: Grafana for visualization
- **Tracing**: OpenTelemetry + Jaeger for distributed tracing
- **Alerting**: Prometheus Alertmanager for proactive monitoring
- **Health Checks**: Kubernetes-native liveness, readiness, startup probes

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                           │
└──────────────────────────────────────────────────────────────┘

Lexecon Pods
     │
     ├─► /metrics endpoint ──► Prometheus ──► Grafana
     │                             │              (Visualization)
     │                             │
     │                             └──► Alertmanager ──► Slack/PagerDuty
     │
     ├─► OpenTelemetry ──► Jaeger
     │   (Distributed Tracing)     (Trace Visualization)
     │
     └─► /health endpoints ──► Kubernetes
         (liveness, readiness)    (Auto-healing)
```

## Quick Start

### 1. Enable Monitoring in Kubernetes

```bash
# Deploy Prometheus
kubectl apply -f infrastructure/kubernetes/prometheus/

# Deploy Grafana
kubectl apply -f infrastructure/kubernetes/grafana/

# Deploy Jaeger (optional, for tracing)
kubectl apply -f infrastructure/kubernetes/jaeger/
```

### 2. Configure Environment Variables

```bash
# Enable detailed metrics
FEATURE_FLAG_METRICS_DETAILED=true

# Enable distributed tracing
TRACING_ENABLED=true
JAEGER_ENDPOINT=jaeger:6831
OTEL_SAMPLE_RATE=0.1  # Sample 10% of requests

# Service name
SERVICE_NAME=lexecon
```

### 3. Access Dashboards

```bash
# Port forward Grafana
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Access: http://localhost:3000
# Default credentials: admin/admin

# Port forward Jaeger UI
kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring

# Access: http://localhost:16686
```

## Available Metrics

### HTTP & API Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lexecon_http_requests_total` | Counter | Total HTTP requests by method, endpoint, status |
| `lexecon_http_request_duration_seconds` | Histogram | HTTP request duration |
| `lexecon_api_latency_summary` | Summary | API latency summary statistics |
| `lexecon_api_response_size_bytes` | Histogram | API response size distribution |
| `lexecon_concurrent_requests` | Gauge | Current concurrent requests |

### Decision Engine Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lexecon_decisions_total` | Counter | Total decisions by allowed/denied, actor, risk level |
| `lexecon_decision_evaluation_duration_seconds` | Histogram | Decision evaluation latency |
| `lexecon_decisions_denied_total` | Counter | Total denied decisions by reason, actor |

### Error & Exception Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lexecon_errors_total` | Counter | Total errors by type, severity, component |
| `lexecon_exceptions_total` | Counter | Total exceptions by class, endpoint |
| `lexecon_error_recovery_total` | Counter | Successful error recoveries |

### Cache Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lexecon_cache_hits_total` | Counter | Cache hits by cache name |
| `lexecon_cache_misses_total` | Counter | Cache misses by cache name |
| `lexecon_cache_evictions_total` | Counter | Cache evictions by cache name, reason |
| `lexecon_cache_size_bytes` | Gauge | Current cache size |
| `lexecon_cache_items` | Gauge | Number of cached items |

### Authentication & Security Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lexecon_auth_attempts_total` | Counter | Authentication attempts by method, result |
| `lexecon_auth_failures_total` | Counter | Authentication failures by method, reason |
| `lexecon_mfa_challenges_total` | Counter | MFA challenges issued |
| `lexecon_mfa_verifications_total` | Counter | MFA verifications by result |
| `lexecon_active_sessions` | Gauge | Number of active user sessions |
| `lexecon_rate_limit_hits_total` | Counter | Rate limit hits (blocked requests) |

### Database Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lexecon_db_connections_active` | Gauge | Active database connections |
| `lexecon_db_connections_idle` | Gauge | Idle database connections |
| `lexecon_db_query_duration_seconds` | Histogram | Database query duration |
| `lexecon_db_errors_total` | Counter | Database errors by type |
| `lexecon_db_transaction_duration_seconds` | Histogram | Transaction duration |

### Business & Compliance Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lexecon_compliance_violations_total` | Counter | Compliance violations by type, severity |
| `lexecon_audit_log_entries_total` | Counter | Audit log entries by event type |
| `lexecon_risk_assessments_total` | Counter | Risk assessments by level |
| `lexecon_ledger_entries_total` | Counter | Total ledger entries |
| `lexecon_ledger_integrity_checks_total` | Counter | Ledger integrity checks by result |

### Feature Flag Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lexecon_feature_flag_evaluations_total` | Counter | Feature flag evaluations by flag, result |
| `lexecon_feature_flag_errors_total` | Counter | Feature flag errors by flag, type |

## Grafana Dashboards

### Main Dashboard (`lexecon-dashboard.json`)

**Panels:**
1. **HTTP Request Rate**: Real-time request throughput
2. **API Latency (p95)**: 95th percentile response time
3. **Decision Rate**: Governance decisions per second
4. **Cache Hit Rate**: Cache effectiveness
5. **Error Rate by Type**: Error distribution
6. **Active Sessions**: Current user sessions
7. **Active DB Connections**: Database connection pool usage
8. **Active Policies**: Number of loaded policies
9. **Uptime**: Service uptime

**Refresh**: Auto-refresh every 5 seconds

### Custom Dashboards

Create custom dashboards for specific use cases:

```bash
# Import dashboard via Grafana UI
# Dashboards → Import → Upload JSON file
# File: infrastructure/grafana/lexecon-dashboard.json
```

## Alerting Rules

### Critical Alerts (PagerDuty/Slack)

| Alert | Condition | Duration | Description |
|-------|-----------|----------|-------------|
| `LexeconServiceDown` | `up == 0` | 1m | Service is completely down |
| `LexeconCriticalErrorRate` | `rate(errors{severity="critical"}) > 1` | 2m | Critical errors occurring |
| `LexeconDatabaseErrors` | `rate(db_errors) > 5` | 2m | High database error rate |
| `LexeconComplianceViolations` | `rate(compliance_violations) > 1` | 2m | Compliance violations detected |
| `LexeconLedgerVerificationFailure` | `rate(ledger_integrity_checks{result="failure"}) > 0` | 1m | Ledger integrity compromised |

### Warning Alerts (Slack)

| Alert | Condition | Duration | Description |
|-------|-----------|----------|-------------|
| `LexeconHighErrorRate` | `rate(errors_total) > 10` | 5m | Elevated error rate |
| `LexeconHighLatency` | `p95 latency > 1s` | 5m | API latency degraded |
| `LexeconVeryHighLatency` | `p95 latency > 5s` | 2m | API latency severely degraded |
| `LexeconSlowDecisions` | `p95 decision latency > 0.5s` | 5m | Decision engine slow |
| `LexeconDatabaseConnectionsHigh` | `active_connections > 80` | 5m | Database connection pool saturated |
| `LexeconLowCacheHitRate` | `cache_hit_rate < 0.5` | 10m | Cache not effective |
| `LexeconHighAuthFailureRate` | `rate(auth_failures) > 10` | 5m | Possible brute force attack |

### Configure Alert Destinations

```yaml
# infrastructure/prometheus/alertmanager.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'

    - match:
        severity: warning
      receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#lexecon-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

## Distributed Tracing

### Enable Tracing

```bash
# Environment variables
TRACING_ENABLED=true
JAEGER_ENDPOINT=jaeger:6831
OTEL_SAMPLE_RATE=0.1  # 10% sampling for production
SERVICE_NAME=lexecon
```

### View Traces

```bash
# Access Jaeger UI
kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring
open http://localhost:16686
```

### Trace HTTP Requests Automatically

HTTP requests are automatically traced when OpenTelemetry is enabled:

```python
# Automatic tracing via FastAPI instrumentation
# No code changes required

from lexecon.observability.tracing import tracer

# Tracer is automatically initialized
# All FastAPI endpoints are instrumented
```

### Custom Spans

```python
from lexecon.observability.tracing import trace_function, tracer

# Decorator approach
@trace_function("evaluate_policy")
def evaluate_policy(actor, action, resource):
    # Function is automatically traced
    return decision

# Context manager approach
with tracer.start_span("cache_lookup") as span:
    span.set_attribute("cache_key", key)
    result = cache.get(key)
    span.set_attribute("cache_hit", result is not None)
```

### Trace Decision Evaluation

```python
from lexecon.observability.metrics_enhanced import enhanced_metrics

# Record decision with distributed trace context
with tracer.start_span("decision_evaluation") as span:
    span.set_attribute("actor", actor)
    span.set_attribute("action", action)
    span.set_attribute("resource", resource)

    result = evaluate(actor, action, resource)

    span.set_attribute("allowed", result.allowed)
    span.set_attribute("risk_level", result.risk_level)
```

## Health Checks

### Kubernetes Probes

Lexecon implements all three Kubernetes probe types:

```yaml
# Configured in infrastructure/helm/templates/deployment.yaml

# Liveness probe - is the service running?
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

# Readiness probe - is the service ready for traffic?
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2

# Startup probe - has the service finished initialization?
startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 10
  failureThreshold: 30
```

### Health Check Endpoints

| Endpoint | Purpose | Checks |
|----------|---------|--------|
| `/health` | Overall health | All component checks |
| `/health/live` | Liveness (K8s) | Basic service availability |
| `/health/ready` | Readiness (K8s) | Database, cache, dependencies |
| `/health/startup` | Startup (K8s) | Initialization complete |

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": 1706400000.0,
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "details": {"latency_ms": 2.5}
    },
    {
      "name": "cache",
      "status": "healthy",
      "details": {"hit_rate": 0.85}
    },
    {
      "name": "policy_engine",
      "status": "healthy",
      "details": {"policies_loaded": 12}
    }
  ]
}
```

## Deployment Integration

### Prometheus ServiceMonitor

```yaml
# Automatically scrape metrics from Lexecon pods
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: lexecon
  namespace: staging
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: lexecon
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

### Helm Configuration

```yaml
# infrastructure/helm/values.yaml

observability:
  metrics:
    enabled: true
    port: 8000
    path: /metrics

  tracing:
    enabled: true
    jaegerEndpoint: "jaeger:6831"
    sampleRate: 0.1

  healthChecks:
    liveness:
      enabled: true
      path: /health/live
      initialDelaySeconds: 30
    readiness:
      enabled: true
      path: /health/ready
      initialDelaySeconds: 10
```

## Best Practices

### 1. Metric Naming

```python
# Good: Specific, descriptive names
lexecon_http_request_duration_seconds
lexecon_cache_hits_total

# Bad: Vague, unclear names
http_duration
hits
```

### 2. Label Cardinality

```python
# Good: Low cardinality labels
labels={"method": "GET", "status": "200", "endpoint": "/api/decide"}

# Bad: High cardinality labels (causes metric explosion)
labels={"user_id": "user:12345", "request_id": "uuid-..."}
```

### 3. Sampling for Tracing

```python
# Production: Sample 1-10% of requests
OTEL_SAMPLE_RATE=0.1

# Staging: Sample 50% of requests
OTEL_SAMPLE_RATE=0.5

# Development: Sample 100% of requests
OTEL_SAMPLE_RATE=1.0
```

### 4. Alert Fatigue

```yaml
# Good: Alert on actionable issues
- alert: DatabaseDown
  expr: up{job="postgresql"} == 0

# Bad: Alert on normal variations
- alert: SlightLatencyIncrease
  expr: p95_latency > 100ms  # Too sensitive
```

## Troubleshooting

### Prometheus Not Scraping Metrics

```bash
# Check ServiceMonitor exists
kubectl get servicemonitor -n staging

# Check Prometheus targets
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
open http://localhost:9090/targets

# Check pod metrics endpoint
kubectl exec -it <pod-name> -n staging -- curl http://localhost:8000/metrics
```

### Grafana Dashboard Not Loading

```bash
# Check Grafana pod logs
kubectl logs -f deployment/grafana -n monitoring

# Verify Prometheus datasource
# Grafana UI → Configuration → Data Sources → Prometheus
# URL: http://prometheus:9090
```

### Jaeger Not Receiving Traces

```bash
# Check tracing enabled
kubectl exec -it <pod-name> -n staging -- env | grep TRACING

# Check Jaeger collector
kubectl logs -f deployment/jaeger -n monitoring

# Verify network connectivity
kubectl exec -it <pod-name> -n staging -- nc -zv jaeger 6831
```

### High Memory Usage from Metrics

```python
# Reduce metric cardinality
# Remove high-cardinality labels (user IDs, request IDs)

# Enable metric sampling for high-volume metrics
if random.random() < 0.1:  # Sample 10%
    record_metric()
```

## Cost Optimization

### Metric Retention

```yaml
# Prometheus configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Storage retention
--storage.tsdb.retention.time=15d  # 15 days (default)
--storage.tsdb.retention.size=50GB # 50GB max
```

### Trace Sampling

```bash
# Reduce tracing costs by sampling
# Production: 5-10% sampling
OTEL_SAMPLE_RATE=0.05

# High-traffic endpoints: Lower sampling
OTEL_SAMPLE_RATE=0.01  # 1%

# Critical paths: Higher sampling
# (Configure per-endpoint in code)
```

### Metric Storage Estimates

| Scenario | Metrics/sec | Storage/day | Storage/month |
|----------|-------------|-------------|---------------|
| Development | 100 | 500MB | 15GB |
| Staging | 1,000 | 5GB | 150GB |
| Production (1K RPS) | 10,000 | 50GB | 1.5TB |

## Next Steps

- **Phase 7**: Compliance Documentation (SOC 2, GDPR)
- **Phase 8**: Performance Optimization (baselines, tuning)

## References

- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/
- OpenTelemetry: https://opentelemetry.io/docs/
- Jaeger: https://www.jaegertracing.io/docs/
