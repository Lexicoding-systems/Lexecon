# Production Deployment Guide

Comprehensive guide for deploying Lexecon in production with observability, monitoring, and high availability.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Helm Deployment](#helm-deployment)
- [Observability Setup](#observability-setup)
- [Monitoring & Alerting](#monitoring--alerting)
- [Scaling](#scaling)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Production Checklist](#production-checklist)

---

## Overview

Lexecon provides multiple deployment options:
- **Docker**: Single-node deployment
- **Docker Compose**: Local development with monitoring stack
- **Kubernetes**: Production-grade orchestration
- **Helm**: Easy Kubernetes deployment

All deployments include:
- ✅ Structured JSON logging
- ✅ Prometheus metrics
- ✅ Health checks (liveness/readiness)
- ✅ Auto-scaling capabilities
- ✅ Security hardening

---

## Prerequisites

### Required
- Docker 20.10+
- For Kubernetes: kubectl, Kubernetes cluster
- For Helm: Helm 3.0+

### Recommended
- Prometheus for metrics
- Grafana for dashboards
- Load balancer (for production)
- SSL/TLS certificates

---

## Deployment Options

### Quick Comparison

| Option | Use Case | Complexity | HA Support | Auto-scaling |
|--------|----------|------------|------------|-------------|
| **Docker** | Development, single-node | Low | ❌ | ❌ |
| **Docker Compose** | Local dev with monitoring | Low | ❌ | ❌ |
| **Kubernetes** | Production | Medium | ✅ | ✅ |
| **Helm** | Easy prod deployment | Low-Medium | ✅ | ✅ |

---

## Docker Deployment

### Build Image

```bash
# Build from source
docker build -t lexecon:latest .

# Or pull from registry (when available)
docker pull lexecon/lexecon:latest
```

### Run Container

```bash
docker run -d \
  --name lexecon \
  -p 8000:8000 \
  -e LEXECON_NODE_ID=prod-node \
  -e LEXECON_LOG_LEVEL=INFO \
  -e LEXECON_LOG_FORMAT=json \
  -v lexecon-data:/data/.lexecon \
  lexecon:latest
```

### Health Check

```bash
# Check health
curl http://localhost:8000/health

# View logs
docker logs -f lexecon

# View metrics
curl http://localhost:8000/metrics
```

---

## Docker Compose Deployment

### Start Full Stack

```bash
# Start Lexecon + Prometheus + Grafana
docker-compose up -d

# View logs
docker-compose logs -f

# Stop stack
docker-compose down
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Lexecon API** | http://localhost:8000 | N/A |
| **Prometheus** | http://localhost:9090 | N/A |
| **Grafana** | http://localhost:3000 | admin/admin |

### Configure Grafana

1. Login to Grafana (admin/admin)
2. Navigate to Dashboards
3. Lexecon dashboards should be pre-loaded
4. If not, import from `deployment/grafana/dashboards/`

---

## Kubernetes Deployment

### Prerequisites

```bash
# Verify kubectl access
kubectl cluster-info

# Create namespace
kubectl create namespace lexecon
```

### Deploy Manifests

```bash
# Apply all manifests
kubectl apply -f deployment/kubernetes/ -n lexecon

# Or apply individually
kubectl apply -f deployment/kubernetes/configmap.yaml -n lexecon
kubectl apply -f deployment/kubernetes/pvc.yaml -n lexecon
kubectl apply -f deployment/kubernetes/deployment.yaml -n lexecon
kubectl apply -f deployment/kubernetes/hpa.yaml -n lexecon
kubectl apply -f deployment/kubernetes/ingress.yaml -n lexecon
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n lexecon

# Check services
kubectl get svc -n lexecon

# Check HPA
kubectl get hpa -n lexecon

# View logs
kubectl logs -f deployment/lexecon -n lexecon
```

### Access Application

```bash
# Port forward (for testing)
kubectl port-forward svc/lexecon 8000:80 -n lexecon

# Access via Ingress (production)
# Update ingress.yaml with your domain
curl https://lexecon.yourdomain.com/health
```

---

## Helm Deployment

### Install Chart

```bash
# Add Helm repo (when published)
helm repo add lexecon https://charts.lexecon.io
helm repo update

# Or install from local
helm install lexecon ./deployment/helm/lexecon \
  --namespace lexecon \
  --create-namespace
```

### Customize Values

```bash
# Create custom values file
cat > values-prod.yaml <<EOF
replicaCount: 5

image:
  tag: "v0.1.0"

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 200m
    memory: 256Mi

autoscaling:
  minReplicas: 3
  maxReplicas: 20

ingress:
  enabled: true
  hosts:
    - host: lexecon.prod.example.com
      paths:
        - path: /
          pathType: Prefix

config:
  logLevel: INFO
  policyMode: strict
EOF

# Install with custom values
helm install lexecon ./deployment/helm/lexecon \
  --namespace lexecon \
  --create-namespace \
  --values values-prod.yaml
```

### Upgrade Deployment

```bash
# Upgrade to new version
helm upgrade lexecon ./deployment/helm/lexecon \
  --namespace lexecon \
  --values values-prod.yaml

# Rollback if needed
helm rollback lexecon -n lexecon
```

### Uninstall

```bash
helm uninstall lexecon -n lexecon
```

---

## Observability Setup

### Structured Logging

Lexecon outputs JSON-formatted logs:

```json
{
  "timestamp": "2026-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "lexecon.api",
  "message": "Decision approved",
  "request_id": "req_abc123",
  "user_id": "user_456",
  "decision": {
    "allowed": true,
    "actor": "model",
    "risk_level": 2
  }
}
```

**Log aggregation**:
- Send to ELK Stack (Elasticsearch, Logstash, Kibana)
- Or use Loki + Grafana
- Or CloudWatch, Stackdriver, etc.

### Prometheus Metrics

**Available metrics**:

```
# HTTP metrics
lexecon_http_requests_total{method, endpoint, status}
lexecon_http_request_duration_seconds{method, endpoint}

# Decision metrics
lexecon_decisions_total{allowed, actor, risk_level}
lexecon_decision_evaluation_duration_seconds{policy_mode}
lexecon_decisions_denied_total{reason_category, actor}

# Policy metrics
lexecon_policies_loaded_total{policy_name}
lexecon_active_policies
lexecon_policy_evaluation_errors_total{error_type}

# Ledger metrics
lexecon_ledger_entries_total
lexecon_ledger_verification_duration_seconds
lexecon_ledger_integrity_checks_total{result}

# Token metrics
lexecon_tokens_issued_total{scope}
lexecon_tokens_verified_total{valid}
lexecon_active_tokens

# System metrics
lexecon_node_info{node_id, version}
lexecon_node_uptime_seconds
```

**Scrape configuration** (already in `deployment/prometheus/prometheus.yml`):

```yaml
scrape_configs:
  - job_name: 'lexecon'
    static_configs:
      - targets: ['lexecon:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

---

## Monitoring & Alerting

### Grafana Dashboards

**Pre-built dashboards** in `deployment/grafana/dashboards/`:
- `lexecon-overview.json` - Main dashboard

**Panels include**:
- Request rate
- Error rate
- Decision metrics (allowed vs denied)
- Latency (p95, p99)
- Policy evaluation performance
- Ledger health

### Alert Rules

**Pre-configured alerts** in `deployment/prometheus/alerts/lexecon.yml`:

| Alert | Threshold | Severity |
|-------|-----------|----------|
| **HighErrorRate** | >5% | Warning |
| **HighDenialRate** | >50% | Warning |
| **SlowDecisionEvaluation** | p95 >1s | Warning |
| **LedgerIntegrityFailure** | Any failure | Critical |
| **LexeconDown** | Service down 2min | Critical |
| **HighMemoryUsage** | >90% | Warning |
| **PolicyEvaluationErrors** | >0.1/sec | Warning |

### Configure Alertmanager

```yaml
# alertmanager.yml
route:
  group_by: ['alertname', 'severity']
  receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: 'Lexecon Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

---

## Scaling

### Horizontal Scaling (Kubernetes)

**Manual scaling**:
```bash
kubectl scale deployment lexecon --replicas=10 -n lexecon
```

**Auto-scaling** (HPA already configured):
- Min replicas: 2
- Max replicas: 10
- CPU threshold: 70%
- Memory threshold: 80%

**Monitor scaling**:
```bash
kubectl get hpa -n lexecon -w
```

### Vertical Scaling

**Adjust resources in Helm values**:
```yaml
resources:
  limits:
    cpu: 2000m      # Increase from 500m
    memory: 2Gi     # Increase from 512Mi
  requests:
    cpu: 500m
    memory: 512Mi
```

### Performance Tuning

**Optimize for high throughput**:

```yaml
# Increase worker processes
config:
  serverWorkers: 8  # Default: 4
  
  # Enable evaluation caching
  cacheEvaluations: true
  
  # Adjust token TTL
  defaultTTL: 600   # 10 minutes
```

---

## Security

### TLS/SSL

**Using cert-manager** (Kubernetes):

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

Ingress will auto-provision certificates.

### Secrets Management

**Using Kubernetes Secrets**:

```bash
# Create secret for sensitive config
kubectl create secret generic lexecon-secrets \
  --from-literal=api-key=your-secret-key \
  -n lexecon

# Reference in deployment
# See deployment.yaml for examples
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: lexecon-netpol
  namespace: lexecon
spec:
  podSelector:
    matchLabels:
      app: lexecon
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53  # DNS
```

---

## Troubleshooting

### Common Issues

#### Pods not starting

```bash
# Check pod status
kubectl get pods -n lexecon

# Describe pod
kubectl describe pod <pod-name> -n lexecon

# Check logs
kubectl logs <pod-name> -n lexecon

# Check events
kubectl get events -n lexecon --sort-by='.lastTimestamp'
```

#### Health checks failing

```bash
# Test health endpoint
kubectl exec -it <pod-name> -n lexecon -- curl localhost:8000/health

# Check readiness
kubectl exec -it <pod-name> -n lexecon -- curl localhost:8000/health/ready
```

#### High memory usage

```bash
# Check metrics
kubectl top pods -n lexecon

# Increase memory limits
kubectl set resources deployment lexecon --limits=memory=1Gi -n lexecon
```

#### Metrics not appearing

```bash
# Test metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus targets
# Visit Prometheus UI: http://localhost:9090/targets
```

---

## Production Checklist

### Pre-Deployment

- [ ] SSL/TLS certificates configured
- [ ] Resource limits set appropriately
- [ ] Auto-scaling configured
- [ ] Health checks tested
- [ ] Monitoring and alerting set up
- [ ] Backup strategy defined
- [ ] Disaster recovery plan documented
- [ ] Security scanning completed
- [ ] Load testing performed
- [ ] Logging aggregation configured

### Post-Deployment

- [ ] Verify all pods are running
- [ ] Check health endpoints
- [ ] Verify metrics in Prometheus
- [ ] Confirm Grafana dashboards working
- [ ] Test alert firing
- [ ] Verify ingress/load balancer
- [ ] Check SSL certificate validity
- [ ] Test auto-scaling behavior
- [ ] Verify logging pipeline
- [ ] Run smoke tests

### Ongoing

- [ ] Monitor alerts daily
- [ ] Review metrics weekly
- [ ] Update dependencies monthly
- [ ] Review and rotate secrets quarterly
- [ ] Disaster recovery drills quarterly
- [ ] Capacity planning quarterly
- [ ] Security audits annually

---

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Docker Documentation](https://docs.docker.com/)

---

## Support

For deployment issues:
- GitHub Issues: https://github.com/Lexicoding-systems/Lexecon/issues
- Email: jacobporter@lexicoding.tech
- Discussions: https://github.com/Lexicoding-systems/Lexecon/discussions
