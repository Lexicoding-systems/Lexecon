# Lexecon Load Testing (k6)

Load testing scripts for Lexecon API performance validation.

## Prerequisites

Install k6:
```bash
# macOS
brew install k6

# Ubuntu/Debian
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Docker
docker pull grafana/k6
```

## Running Tests

### Quick Smoke Test
```bash
k6 run load_test.js
```

### Load Test (50-100 users)
```bash
k6 run --stage 30s:50,2m:50,30s:100,2m:100,30s:0 load_test.js
```

### Stress Test (200-500 users)
```bash
k6 run --stage 1m:200,5m:200,1m:500,5m:500,1m:0 load_test.js
```

### With Custom Base URL
```bash
BASE_URL=http://production.lexecon.com k6 run load_test.js
```

### Thresholds
- 95th percentile latency: < 200ms
- Error rate: < 1%
- Failed requests: < 1%

## Expected Results

**Performance Targets**:
- Decision API: < 100ms (p95)
- Status/Health: < 50ms (p95)
- Audit queries: < 200ms (p95)
- Throughput: 1,000+ requests/sec

**Scaling**:
- Single instance: 50-100 concurrent users
- With Redis: 500+ concurrent users
- Kubernetes (3 pods): 1,000+ concurrent users
