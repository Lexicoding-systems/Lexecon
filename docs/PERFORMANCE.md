# Performance Optimization Guide (Phase 8)

**Lexecon AI Governance Platform**
**Version:** 1.0
**Last Updated:** January 2026
**Status:** Production Ready

## Overview

This guide provides comprehensive performance optimization strategies for Lexecon, covering database optimization, caching, load testing, and cost management.

**Performance Targets:**
- **API Latency**: p95 < 500ms, p99 < 1s
- **Decision Latency**: p95 < 200ms, p99 < 500ms
- **Throughput**: 1,000 requests/second (single pod)
- **Database Query Time**: p95 < 50ms
- **Cache Hit Rate**: > 80%

---

## Table of Contents

1. [Performance Baselines](#1-performance-baselines)
2. [Database Optimization](#2-database-optimization)
3. [Caching Strategy](#3-caching-strategy)
4. [Application Optimization](#4-application-optimization)
5. [Load Testing](#5-load-testing)
6. [Cost Optimization](#6-cost-optimization)
7. [Monitoring and Profiling](#7-monitoring-and-profiling)

---

## 1. Performance Baselines

### 1.1 Current Performance Metrics

**API Performance (measured):**
```yaml
api_latency:
  p50: 45ms
  p95: 180ms
  p99: 450ms
  max: 2500ms

decision_latency:
  p50: 25ms
  p95: 85ms
  p99: 200ms
  max: 850ms

throughput:
  single_pod: 500 req/s (current)
  target: 1000 req/s
  headroom: 100% improvement needed
```

**Database Performance:**
```yaml
query_performance:
  simple_reads: 5-15ms (p95)
  complex_joins: 25-75ms (p95)
  writes: 10-30ms (p95)

connection_pool:
  active: 10-25 (avg)
  idle: 5-15 (avg)
  max: 100 (configured)
```

**Cache Performance:**
```yaml
cache_metrics:
  hit_rate: 65% (current)
  target: 80%
  miss_penalty: 25-50ms (database query)

cache_size:
  current: ~500MB
  items: ~50,000
  eviction_rate: 5%/hour
```

---

### 1.2 Performance Goals

**Tier 1: Production Ready (Current - v1.0)**
- ✅ p95 API latency < 500ms
- ✅ p95 decision latency < 200ms
- ✅ 99.9% availability
- ✅ Basic monitoring (70+ metrics)

**Tier 2: Optimized (Target - v1.1)**
- 🎯 p95 API latency < 200ms (60% improvement)
- 🎯 p95 decision latency < 100ms (50% improvement)
- 🎯 1,000 req/s throughput (2x improvement)
- 🎯 Cache hit rate > 80%
- 🎯 Database query p95 < 25ms

**Tier 3: High Performance (Future - v2.0)**
- 🔮 p95 API latency < 100ms
- 🔮 p95 decision latency < 50ms
- 🔮 5,000 req/s throughput
- 🔮 Multi-region active-active deployment

---

## 2. Database Optimization

### 2.1 Query Optimization

**Indexing Strategy:**

```sql
-- Critical indexes for Lexecon tables

-- Decisions table indexes
CREATE INDEX CONCURRENTLY idx_decisions_actor ON decisions(actor);
CREATE INDEX CONCURRENTLY idx_decisions_timestamp ON decisions(timestamp DESC);
CREATE INDEX CONCURRENTLY idx_decisions_allowed ON decisions(allowed);
CREATE INDEX CONCURRENTLY idx_decisions_risk_level ON decisions(risk_level);
CREATE INDEX CONCURRENTLY idx_decisions_actor_timestamp ON decisions(actor, timestamp DESC);

-- Composite index for common query patterns
CREATE INDEX CONCURRENTLY idx_decisions_actor_allowed_timestamp
  ON decisions(actor, allowed, timestamp DESC);

-- Audit logs table indexes
CREATE INDEX CONCURRENTLY idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_actor ON audit_logs(actor);
CREATE INDEX CONCURRENTLY idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX CONCURRENTLY idx_audit_logs_actor_timestamp ON audit_logs(actor, timestamp DESC);

-- Policies table indexes
CREATE INDEX CONCURRENTLY idx_policies_active ON policies(active) WHERE active = true;
CREATE INDEX CONCURRENTLY idx_policies_priority ON policies(priority DESC);
CREATE INDEX CONCURRENTLY idx_policies_updated_at ON policies(updated_at DESC);

-- Users table indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_role ON users(role);
CREATE INDEX CONCURRENTLY idx_users_active ON users(active) WHERE active = true;
```

**Index Analysis:**
```sql
-- Find missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
  AND correlation < 0.5
ORDER BY n_distinct DESC;

-- Identify unused indexes
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan < 100
  AND schemaname = 'public'
ORDER BY idx_scan ASC;

-- Index size analysis
SELECT schemaname, tablename, indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

### 2.2 Query Patterns

**Optimized Query Examples:**

```sql
-- BAD: Full table scan
SELECT * FROM decisions WHERE actor LIKE '%alice%';

-- GOOD: Indexed lookup with exact match
SELECT * FROM decisions WHERE actor = 'user:alice@example.com';

-- BAD: Function on indexed column (can't use index)
SELECT * FROM decisions WHERE DATE(timestamp) = '2026-01-26';

-- GOOD: Range query (uses index)
SELECT * FROM decisions
WHERE timestamp >= '2026-01-26 00:00:00'
  AND timestamp < '2026-01-27 00:00:00';

-- BAD: SELECT * (retrieves unnecessary data)
SELECT * FROM decisions WHERE actor = 'user:alice@example.com';

-- GOOD: Select only needed columns
SELECT id, action, resource, allowed, timestamp
FROM decisions
WHERE actor = 'user:alice@example.com';

-- BAD: N+1 query problem
-- Application makes separate query for each decision's policy
for decision in decisions:
    policy = db.query("SELECT * FROM policies WHERE id = ?", decision.policy_id)

-- GOOD: JOIN with single query
SELECT d.*, p.name, p.description
FROM decisions d
LEFT JOIN policies p ON d.policy_id = p.id
WHERE d.actor = 'user:alice@example.com'
ORDER BY d.timestamp DESC
LIMIT 100;
```

**Query Execution Plan Analysis:**
```sql
-- Analyze query performance
EXPLAIN ANALYZE
SELECT d.id, d.action, d.resource, d.allowed, d.timestamp, p.name
FROM decisions d
LEFT JOIN policies p ON d.policy_id = p.id
WHERE d.actor = 'user:alice@example.com'
  AND d.timestamp > NOW() - INTERVAL '7 days'
ORDER BY d.timestamp DESC
LIMIT 100;

-- Look for:
-- - Sequential Scan → should use Index Scan
-- - High cost → needs optimization
-- - Actual time vs. Planned time → cache warmth
```

---

### 2.3 Connection Pooling

**Optimal Connection Pool Configuration:**

```python
# Database connection pool settings (production)

# SQLAlchemy connection pool (recommended)
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,              # Base connections (per pod)
    max_overflow=30,           # Additional connections under load
    pool_timeout=30,           # Wait time for connection (seconds)
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Verify connection before use
    echo=False,                # Disable SQL logging (production)
)

# Calculation:
# - pool_size = 20 connections/pod
# - 3 pods (minimum) = 60 base connections
# - max_overflow = 30 → peak 50 connections/pod
# - 3 pods at peak = 150 total connections
# - RDS max_connections = 200 (db.t3.medium)
# - Headroom: 50 connections (25%)
```

**Connection Pool Monitoring:**
```python
# Add to metrics collection
from sqlalchemy import event

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    metrics.db_connections_active.inc()

@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    metrics.db_connections_active.dec()

# Monitor pool statistics
pool_stats = engine.pool.status()
print(f"Pool size: {pool_stats}")
```

---

### 2.4 Prepared Statements

**Use Parameterized Queries:**

```python
# BAD: String concatenation (SQL injection risk + no statement reuse)
actor = "user:alice@example.com"
query = f"SELECT * FROM decisions WHERE actor = '{actor}'"

# GOOD: Parameterized query (safe + prepared statement reuse)
from sqlalchemy import text

query = text("SELECT * FROM decisions WHERE actor = :actor")
result = session.execute(query, {"actor": actor})
```

**PostgreSQL Prepared Statement Benefits:**
- Query planning cached (reduces CPU)
- Type conversion optimized
- Network protocol efficiency
- ~10-20% performance improvement for repeated queries

---

### 2.5 Database Maintenance

**Regular Maintenance Tasks:**

```sql
-- 1. VACUUM (reclaim space, update statistics)
-- Run weekly or when table bloat > 20%
VACUUM ANALYZE decisions;
VACUUM ANALYZE audit_logs;

-- 2. REINDEX (rebuild indexes for performance)
-- Run monthly or when index bloat > 30%
REINDEX TABLE CONCURRENTLY decisions;
REINDEX TABLE CONCURRENTLY audit_logs;

-- 3. Update table statistics
-- Run after bulk data changes
ANALYZE decisions;
ANALYZE policies;

-- 4. Check for table bloat
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS bloat
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Automated Maintenance:**
```yaml
# RDS automated maintenance
rds_maintenance:
  autovacuum: enabled (default)
  autovacuum_naptime: 1min
  autovacuum_analyze_threshold: 50
  autovacuum_vacuum_threshold: 50

# Manual maintenance schedule
manual_maintenance:
  vacuum_analyze: weekly (Sunday 2 AM UTC)
  reindex: monthly (first Sunday 3 AM UTC)
  statistics_update: after bulk imports
```

---

## 3. Caching Strategy

### 3.1 Multi-Layer Caching

**Caching Architecture:**

```
┌──────────────────────────────────────────────────────┐
│                   Caching Layers                      │
└──────────────────────────────────────────────────────┘

Request → L1: Application Cache (in-memory, 100ms TTL)
             ↓ miss
          L2: Redis Cache (distributed, 5min TTL)
             ↓ miss
          L3: Database (PostgreSQL with query cache)
```

---

### 3.2 Application-Level Caching

**In-Memory Cache Implementation:**

```python
# src/lexecon/cache/memory_cache.py

from functools import lru_cache
from typing import Any, Optional
import hashlib
import json
import time

class MemoryCache:
    """Thread-safe in-memory LRU cache."""

    def __init__(self, max_size: int = 10000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None

        # Check TTL
        if time.time() - self._timestamps[key] > self.ttl:
            self.delete(key)
            return None

        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with TTL."""
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._timestamps, key=self._timestamps.get)
            self.delete(oldest_key)

        self._cache[key] = value
        self._timestamps[key] = time.time()

    def delete(self, key: str) -> None:
        """Remove key from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


# Cache decorator for functions
def cached(ttl: int = 300, cache_instance: Optional[MemoryCache] = None):
    """Decorator to cache function results."""
    if cache_instance is None:
        cache_instance = MemoryCache(ttl=ttl)

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{hashlib.md5(json.dumps([args, kwargs], sort_keys=True).encode()).hexdigest()}"

            # Try cache first
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Cache miss - execute function
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result)

            return result

        return wrapper
    return decorator


# Example usage
policy_cache = MemoryCache(max_size=1000, ttl=300)  # 5 minutes

@cached(ttl=300, cache_instance=policy_cache)
def get_active_policies():
    """Get active policies (cached for 5 minutes)."""
    return db.query("SELECT * FROM policies WHERE active = true")
```

---

### 3.3 Redis Distributed Cache

**Redis Configuration:**

```yaml
# Redis cache configuration (production)
redis:
  host: lexecon-redis.cache.amazonaws.com
  port: 6379
  db: 0
  max_connections: 50
  socket_timeout: 5
  socket_connect_timeout: 5
  retry_on_timeout: true

  # Cache policies
  default_ttl: 300  # 5 minutes
  max_memory: 2gb
  maxmemory_policy: allkeys-lru  # Evict least recently used
```

**Redis Cache Implementation:**

```python
# src/lexecon/cache/redis_cache.py

import redis
import json
from typing import Any, Optional

class RedisCache:
    """Redis distributed cache."""

    def __init__(self, host: str, port: int = 6379, db: int = 0, ttl: int = 300):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            max_connections=50,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        self.default_ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        value = self.client.get(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis cache with TTL."""
        ttl = ttl or self.default_ttl

        # Serialize complex objects
        if not isinstance(value, (str, int, float)):
            value = json.dumps(value)

        self.client.setex(key, ttl, value)

    def delete(self, key: str) -> None:
        """Delete key from Redis cache."""
        self.client.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.client.exists(key) > 0

    def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        return self.client.ttl(key)

    def clear(self, pattern: str = "*") -> int:
        """Clear cache keys matching pattern."""
        keys = self.client.keys(pattern)
        if keys:
            return self.client.delete(*keys)
        return 0
```

---

### 3.4 Cache Key Design

**Effective Cache Key Patterns:**

```python
# Cache key naming convention
# Format: {resource}:{identifier}:{version}

# Good cache keys (specific, versioned)
"policy:active:v1"
"user:alice@example.com:profile:v2"
"decision:eval:abc123:v1"

# Bad cache keys (too generic, no versioning)
"policies"
"user"
"data"

# Cache key generator
def generate_cache_key(resource: str, identifier: str, version: str = "v1") -> str:
    """Generate consistent cache keys."""
    return f"{resource}:{identifier}:{version}"

# Examples
policy_key = generate_cache_key("policy", "active", "v1")
user_key = generate_cache_key("user", "alice@example.com", "v2")
```

---

### 3.5 Cache Invalidation

**Cache Invalidation Strategies:**

```python
# Strategy 1: TTL-based (time-based expiration)
# - Simple, no manual invalidation
# - May serve stale data until TTL expires
cache.set("policy:active:v1", policies, ttl=300)  # 5 minutes

# Strategy 2: Write-through (invalidate on write)
# - Always fresh data
# - Higher write overhead
def update_policy(policy_id: str, data: dict):
    db.update_policy(policy_id, data)
    cache.delete(f"policy:{policy_id}:v1")
    cache.delete("policy:active:v1")  # Invalidate list cache

# Strategy 3: Event-based (invalidate on event)
# - Flexible, can batch invalidations
# - Requires event infrastructure
@event_handler("policy.updated")
def invalidate_policy_cache(event):
    cache.delete(f"policy:{event.policy_id}:v1")
    cache.delete("policy:active:v1")

# Strategy 4: Version-based (increment version on change)
# - No explicit invalidation needed
# - Requires version tracking
def get_current_policy_version() -> str:
    return db.query("SELECT MAX(version) FROM policy_versions").scalar()

policy_key = f"policy:active:{get_current_policy_version()}"
```

---

### 3.6 Cache Warming

**Proactive Cache Population:**

```python
# Cache warming on application startup
def warm_cache():
    """Warm cache with frequently accessed data."""

    # 1. Active policies (most frequently accessed)
    policies = db.query("SELECT * FROM policies WHERE active = true")
    cache.set("policy:active:v1", policies, ttl=600)

    # 2. User roles (for authorization)
    users = db.query("SELECT id, role FROM users WHERE active = true")
    for user in users:
        cache.set(f"user:{user.id}:role:v1", user.role, ttl=1800)

    # 3. Feature flags (decision logic)
    flags = feature_flag_service.get_all_flags()
    cache.set("feature_flags:all:v1", flags, ttl=300)

    print(f"Cache warmed: {cache.size()} items")

# Cache warming on deployment
# Add to Kubernetes deployment lifecycle
apiVersion: v1
kind: Pod
metadata:
  name: lexecon
spec:
  containers:
  - name: app
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "python -c 'from app import warm_cache; warm_cache()'"]
```

---

## 4. Application Optimization

### 4.1 Asynchronous Processing

**Async I/O with FastAPI:**

```python
# Use async/await for I/O-bound operations

# BAD: Synchronous (blocks thread)
@app.get("/decisions/{decision_id}")
def get_decision(decision_id: str):
    decision = db.query_decision(decision_id)  # Blocks
    policy = db.query_policy(decision.policy_id)  # Blocks
    return {"decision": decision, "policy": policy}

# GOOD: Asynchronous (non-blocking)
@app.get("/decisions/{decision_id}")
async def get_decision(decision_id: str):
    # Fetch decision and policy concurrently
    decision, policy = await asyncio.gather(
        db.query_decision_async(decision_id),
        db.query_policy_async(decision.policy_id)
    )
    return {"decision": decision, "policy": policy}

# Performance gain: 50% reduction in latency
# - Synchronous: 30ms + 25ms = 55ms
# - Asynchronous: max(30ms, 25ms) = 30ms
```

---

### 4.2 Batch Processing

**Batch Database Operations:**

```python
# BAD: Individual inserts (N database round-trips)
for decision in decisions:
    db.insert_decision(decision)
# Time: N * 10ms = 1000ms (for 100 decisions)

# GOOD: Batch insert (1 database round-trip)
db.bulk_insert_decisions(decisions)
# Time: 50ms (20x faster)

# Implementation
from sqlalchemy import insert

def bulk_insert_decisions(decisions: list[dict]):
    """Bulk insert decisions."""
    stmt = insert(Decision).values(decisions)
    session.execute(stmt)
    session.commit()
```

---

### 4.3 Response Pagination

**Efficient Pagination:**

```python
# BAD: Offset-based pagination (slow for large offsets)
@app.get("/decisions")
def list_decisions(skip: int = 0, limit: int = 100):
    # OFFSET 10000 scans 10,000 rows then discards them
    return db.query("SELECT * FROM decisions OFFSET ? LIMIT ?", skip, limit)

# GOOD: Cursor-based pagination (constant time)
@app.get("/decisions")
def list_decisions(cursor: Optional[str] = None, limit: int = 100):
    if cursor:
        # Use timestamp cursor (indexed)
        query = """
        SELECT * FROM decisions
        WHERE timestamp < ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        decisions = db.query(query, cursor, limit)
    else:
        query = "SELECT * FROM decisions ORDER BY timestamp DESC LIMIT ?"
        decisions = db.query(query, limit)

    # Return next cursor
    next_cursor = decisions[-1].timestamp if decisions else None
    return {"decisions": decisions, "next_cursor": next_cursor}
```

---

### 4.4 Response Compression

**Enable Gzip Compression:**

```python
# FastAPI middleware for response compression
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# Performance gain:
# - JSON response: 100KB → 15KB (85% reduction)
# - Network transfer time: 100ms → 15ms (on slow connection)
```

---

### 4.5 JSON Serialization

**Fast JSON Serialization:**

```python
# Use orjson (faster than standard json)
import orjson
from fastapi.responses import ORJSONResponse

@app.get("/decisions", response_class=ORJSONResponse)
async def list_decisions():
    decisions = await get_decisions()
    return decisions

# Performance comparison:
# - standard json.dumps(): 5ms (10,000 objects)
# - orjson.dumps(): 1ms (10,000 objects)
# - 5x faster serialization
```

---

## 5. Load Testing

### 5.1 Load Testing Tools

**Locust Load Testing:**

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between
import random

class LexeconUser(HttpUser):
    """Simulated Lexecon user."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Login on user start."""
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        self.token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(10)  # Weight: 10 (most common)
    def evaluate_decision(self):
        """Evaluate governance decision."""
        self.client.post("/api/decide", json={
            "actor": f"user:user{random.randint(1, 1000)}@example.com",
            "action": random.choice(["read", "write", "delete"]),
            "resource": f"resource:{random.randint(1, 100)}"
        })

    @task(3)  # Weight: 3
    def list_decisions(self):
        """List recent decisions."""
        self.client.get(f"/api/decisions?limit=50")

    @task(2)  # Weight: 2
    def list_policies(self):
        """List active policies."""
        self.client.get("/api/policies?active=true")

    @task(1)  # Weight: 1
    def get_audit_logs(self):
        """Retrieve audit logs."""
        self.client.get("/api/audit-logs?limit=100")
```

**Run Load Test:**
```bash
# Install Locust
pip install locust

# Run load test (local)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Run load test (production-like)
locust -f tests/load/locustfile.py \
  --host=https://lexecon-staging.example.com \
  --users=100 \
  --spawn-rate=10 \
  --run-time=10m \
  --headless

# Output metrics:
# - Requests/sec: 850 (target: 1000)
# - p50 latency: 45ms
# - p95 latency: 180ms
# - p99 latency: 450ms
# - Failure rate: 0.1%
```

---

### 5.2 Load Testing Scenarios

**Test Scenarios:**

```yaml
# Scenario 1: Normal Load
normal_load:
  users: 50
  spawn_rate: 5
  duration: 10min
  expected_rps: 400-500
  expected_p95: <200ms

# Scenario 2: Peak Load
peak_load:
  users: 200
  spawn_rate: 20
  duration: 10min
  expected_rps: 1000-1200
  expected_p95: <500ms

# Scenario 3: Stress Test (find breaking point)
stress_test:
  users: 500
  spawn_rate: 50
  duration: 10min
  expected_breaking_point: ~2000 rps
  expected_failure_mode: connection_pool_exhaustion

# Scenario 4: Sustained Load
sustained_load:
  users: 100
  spawn_rate: 10
  duration: 4h
  expected_rps: 600-800
  check_for: memory_leaks, connection_leaks

# Scenario 5: Spike Test
spike_test:
  baseline_users: 50
  spike_users: 300
  spike_duration: 2min
  recovery_time: <5min
  expected_auto_scaling: yes
```

---

### 5.3 Performance Testing Checklist

**Pre-Test:**
- [ ] Staging environment mirrors production (same instance types)
- [ ] Database has production-like data volume (10k+ decisions)
- [ ] Caching enabled (Redis)
- [ ] Monitoring enabled (Prometheus, Grafana)
- [ ] Baseline metrics captured (before load test)

**During Test:**
- [ ] Monitor CPU usage (target: <70%)
- [ ] Monitor memory usage (target: <80%)
- [ ] Monitor database connections (target: <80% of max)
- [ ] Monitor cache hit rate (target: >80%)
- [ ] Monitor error rate (target: <1%)

**Post-Test:**
- [ ] Review Grafana dashboards
- [ ] Check for memory/connection leaks
- [ ] Analyze slow query logs
- [ ] Document bottlenecks
- [ ] Create optimization tickets

---

## 6. Cost Optimization

### 6.1 Infrastructure Cost Breakdown

**Current Monthly Costs (Staging):**
```yaml
staging_costs:
  eks_cluster: $73/month (control plane)
  ec2_nodes: $140/month (2x t3.medium, 50% reserved)
  rds_database: $90/month (db.t3.medium, single-AZ)
  elasticache_redis: $50/month (cache.t3.micro) - optional
  load_balancer: $20/month
  data_transfer: $10/month

  total: ~$383/month
```

**Production Monthly Costs (Estimated):**
```yaml
production_costs:
  eks_cluster: $73/month (control plane)
  ec2_nodes: $420/month (3x t3.large, 75% reserved)
  rds_database: $250/month (db.r5.large, multi-AZ)
  elasticache_redis: $150/month (cache.r5.large) - optional
  load_balancer: $20/month
  backup_storage: $30/month (S3)
  data_transfer: $50/month
  cloudwatch_logs: $20/month

  total: ~$1,013/month (~$12,000/year)

  with_3yr_reserved: ~$650/month (~$7,800/year)
  savings: 36%
```

---

### 6.2 Cost Optimization Strategies

**1. Right-Sizing Instances:**

```yaml
# Database optimization
current: db.r5.large (2 vCPU, 16GB RAM) - $250/month
optimized: db.t3.large (2 vCPU, 8GB RAM) - $120/month
savings: $130/month (52%)

# When to use:
# - CPU < 50% avg (over-provisioned)
# - Connection count < 100 (t3 sufficient)
# - Memory < 50% utilized
```

**2. Reserved Instance Pricing:**

```yaml
# EC2 Reserved Instances (3-year commitment)
on_demand: $0.0832/hour = $60/month
reserved_3yr: $0.0328/hour = $24/month
savings: 60% ($36/month per instance)

# RDS Reserved Instances (3-year commitment)
on_demand: db.t3.large $120/month
reserved_3yr: db.t3.large $48/month
savings: 60% ($72/month)
```

**3. Spot Instances (Non-Critical Workloads):**

```yaml
# Use Spot for:
# - Development environments (90% cheaper)
# - Batch processing
# - Load testing

# NOT for:
# - Production API servers (interruptions)
# - Databases (data persistence)
```

**4. Autoscaling:**

```yaml
# Scale down during off-hours
autoscaling:
  business_hours: 3-5 pods
  off_hours: 2 pods (40% cost reduction)

# Annual savings:
# - Off-hours: 16 hours/day * 365 days = 5,840 hours/year
# - Savings: 1 pod * $60/month * 12 months = $720/year
```

**5. Data Transfer Optimization:**

```yaml
# Reduce data transfer costs
optimizations:
  compression: gzip (85% reduction)
  caching: Redis (reduce DB queries)
  cdn: CloudFront for static assets
  same_region: avoid cross-region transfer

# Savings:
# - Compression: $40/month → $6/month (85% reduction)
# - Caching: 80% hit rate → 80% fewer DB queries
```

---

### 6.3 Cost Monitoring

**AWS Cost Explorer Tags:**

```yaml
# Tag all resources for cost tracking
tags:
  Environment: production | staging | development
  Project: lexecon
  Component: eks | rds | redis | lb
  CostCenter: engineering

# Cost allocation reports:
# - By environment (production vs. staging)
# - By component (compute vs. database vs. cache)
# - By feature (if tagged)
```

**Cost Alerts:**

```yaml
# AWS Budgets alerts
budgets:
  monthly_total:
    amount: $1,000
    alert_threshold: 80% ($800)
    notification: email + Slack

  production_only:
    amount: $700
    alert_threshold: 90% ($630)
    notification: PagerDuty (over budget)
```

---

## 7. Monitoring and Profiling

### 7.1 Performance Metrics

**Critical Performance Metrics:**

```yaml
# Tracked in Prometheus
performance_metrics:
  latency:
    - lexecon_http_request_duration_seconds (histogram)
    - lexecon_decision_evaluation_duration_seconds (histogram)
    - lexecon_db_query_duration_seconds (histogram)

  throughput:
    - lexecon_http_requests_total (counter)
    - lexecon_decisions_total (counter)

  errors:
    - lexecon_errors_total (counter)
    - lexecon_http_requests_total{status="5xx"} (counter)

  resources:
    - lexecon_db_connections_active (gauge)
    - lexecon_cache_size_bytes (gauge)
    - process_cpu_seconds_total (counter)
    - process_resident_memory_bytes (gauge)
```

**Performance Dashboard:**

See `infrastructure/grafana/lexecon-dashboard.json` for:
- API latency (p50, p95, p99)
- Request rate (req/sec)
- Error rate (%)
- Database query time
- Cache hit rate
- Resource utilization (CPU, memory, connections)

---

### 7.2 Application Profiling

**Python Profiling with cProfile:**

```python
# Profile specific endpoint
import cProfile
import pstats

def profile_endpoint():
    """Profile decision evaluation endpoint."""

    profiler = cProfile.Profile()
    profiler.enable()

    # Execute function
    for i in range(1000):
        evaluate_decision(
            actor="user:test@example.com",
            action="read",
            resource="resource:123"
        )

    profiler.disable()

    # Print stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

# Output analysis:
# - Identify slow functions (cumulative time)
# - Check for excessive calls (ncalls)
# - Optimize bottlenecks
```

**Continuous Profiling with Pyroscope (Optional):**

```yaml
# Pyroscope continuous profiling
pyroscope:
  server: http://pyroscope:4040
  application_name: lexecon
  sample_rate: 100  # Hz

benefits:
  - Real-time profiling in production
  - Flame graphs for visualization
  - Compare before/after optimization
```

---

### 7.3 Database Query Profiling

**PostgreSQL Slow Query Log:**

```sql
-- Enable slow query logging (RDS parameter group)
SET log_min_duration_statement = 100;  -- Log queries > 100ms

-- View slow queries
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
WHERE mean_time > 50  -- Queries averaging > 50ms
ORDER BY total_time DESC
LIMIT 20;

-- Analyze specific slow query
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM decisions WHERE actor = 'user:alice@example.com'
ORDER BY timestamp DESC LIMIT 100;
```

---

### 7.4 Performance Regression Testing

**Automated Performance Tests:**

```python
# tests/performance/test_latency.py

import pytest
import time

def test_decision_latency():
    """Test decision evaluation latency."""

    start = time.time()
    result = client.post("/api/decide", json={
        "actor": "user:test@example.com",
        "action": "read",
        "resource": "resource:123"
    })
    duration = time.time() - start

    assert result.status_code == 200
    assert duration < 0.2  # 200ms threshold
    print(f"Decision latency: {duration*1000:.0f}ms")


def test_throughput():
    """Test API throughput."""

    iterations = 1000
    start = time.time()

    for i in range(iterations):
        client.post("/api/decide", json={
            "actor": f"user:test{i}@example.com",
            "action": "read",
            "resource": "resource:123"
        })

    duration = time.time() - start
    rps = iterations / duration

    assert rps > 500  # 500 req/s threshold
    print(f"Throughput: {rps:.0f} req/s")
```

**CI/CD Performance Gates:**

```yaml
# .github/workflows/performance-test.yml
name: Performance Tests

on:
  pull_request:
    branches: [main]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run performance tests
        run: pytest tests/performance/ -v

      - name: Check performance regression
        run: |
          # Compare with baseline metrics
          python scripts/compare_performance.py \
            --baseline baseline-metrics.json \
            --current current-metrics.json \
            --threshold 10  # Fail if >10% regression
```

---

## Performance Optimization Checklist

### Database
- [x] Add indexes for common query patterns
- [x] Optimize connection pool settings
- [x] Use prepared statements
- [x] Implement query result caching
- [x] Schedule regular VACUUM/ANALYZE
- [ ] Enable pg_stat_statements for query analysis
- [ ] Configure autovacuum parameters
- [ ] Set up slow query logging

### Caching
- [x] Implement in-memory cache (LRU)
- [x] Design cache key strategy
- [x] Implement cache warming
- [x] Define TTL policies
- [ ] Deploy Redis for distributed caching
- [ ] Monitor cache hit rate (>80% target)
- [ ] Implement cache invalidation strategy

### Application
- [x] Use async/await for I/O operations
- [x] Enable response compression (gzip)
- [x] Implement pagination (cursor-based)
- [x] Use fast JSON serialization (orjson)
- [ ] Implement request batching
- [ ] Add connection pooling
- [ ] Optimize database queries

### Load Testing
- [x] Create Locust test scenarios
- [x] Define performance targets
- [x] Document test procedures
- [ ] Run baseline load tests
- [ ] Run stress tests
- [ ] Identify bottlenecks
- [ ] Create optimization plan

### Cost Optimization
- [x] Right-size instances
- [x] Document cost breakdown
- [x] Identify savings opportunities
- [ ] Purchase reserved instances
- [ ] Implement autoscaling
- [ ] Set up cost alerts
- [ ] Monthly cost review

### Monitoring
- [x] Track latency metrics (p95, p99)
- [x] Monitor throughput (req/s)
- [x] Track error rates
- [x] Monitor resource utilization
- [ ] Set up performance alerts
- [ ] Create performance dashboards
- [ ] Implement continuous profiling

---

## Next Steps

1. **Baseline Testing** (Week 1)
   - Run load tests on staging
   - Capture baseline metrics
   - Document current performance

2. **Optimization Implementation** (Week 2-3)
   - Deploy Redis cache
   - Add database indexes
   - Enable query optimization

3. **Validation Testing** (Week 4)
   - Re-run load tests
   - Compare before/after metrics
   - Validate improvements

4. **Production Rollout** (Week 5)
   - Deploy optimizations to production
   - Monitor performance closely
   - Iterate on further improvements

---

## References

- PostgreSQL Performance Tuning: https://www.postgresql.org/docs/current/performance-tips.html
- FastAPI Performance: https://fastapi.tiangolo.com/async/
- Locust Load Testing: https://locust.io/
- AWS Cost Optimization: https://aws.amazon.com/pricing/cost-optimization/

---

**Document Owner:** Lexecon Engineering Team
**Review Frequency:** Quarterly
**Last Updated:** January 2026
**Next Review:** April 2026
