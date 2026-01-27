-- Database Optimization Scripts for Lexecon (Phase 8)
-- Run these scripts on PostgreSQL to optimize performance

-- ============================================================================
-- 1. CREATE INDEXES
-- ============================================================================

-- Decisions table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_actor 
    ON decisions(actor);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_timestamp 
    ON decisions(timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_allowed 
    ON decisions(allowed);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_risk_level 
    ON decisions(risk_level);

-- Composite index for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_actor_timestamp 
    ON decisions(actor, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_actor_allowed_timestamp 
    ON decisions(actor, allowed, timestamp DESC);

-- Audit logs table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_timestamp 
    ON audit_logs(timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_actor 
    ON audit_logs(actor);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_event_type 
    ON audit_logs(event_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_actor_timestamp 
    ON audit_logs(actor, timestamp DESC);

-- Policies table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_policies_active 
    ON policies(active) WHERE active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_policies_priority 
    ON policies(priority DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_policies_updated_at 
    ON policies(updated_at DESC);

-- Users table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email 
    ON users(email);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role 
    ON users(role);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active 
    ON users(active) WHERE active = true;

-- ============================================================================
-- 2. ANALYZE INDEX USAGE
-- ============================================================================

-- Find missing indexes (high-cardinality columns without indexes)
SELECT 
    schemaname, 
    tablename, 
    attname, 
    n_distinct, 
    correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
  AND correlation < 0.5
ORDER BY n_distinct DESC;

-- Identify unused indexes (candidates for removal)
SELECT 
    schemaname, 
    tablename, 
    indexname, 
    idx_scan, 
    idx_tup_read, 
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan < 100
  AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Index size analysis
SELECT 
    schemaname, 
    tablename, 
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS times_used
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- 3. VACUUM AND ANALYZE
-- ============================================================================

-- Update table statistics
ANALYZE decisions;
ANALYZE audit_logs;
ANALYZE policies;
ANALYZE users;

-- Reclaim space and update statistics
VACUUM ANALYZE decisions;
VACUUM ANALYZE audit_logs;
VACUUM ANALYZE policies;
VACUUM ANALYZE users;

-- ============================================================================
-- 4. CHECK TABLE BLOAT
-- ============================================================================

SELECT 
    schemaname, 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================================================
-- 5. SLOW QUERY ANALYSIS
-- ============================================================================

-- Enable pg_stat_statements (run once as superuser)
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries (requires pg_stat_statements)
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 50  -- Queries averaging > 50ms
ORDER BY total_exec_time DESC
LIMIT 20;

-- ============================================================================
-- 6. CONNECTION POOL ANALYSIS
-- ============================================================================

-- Current active connections
SELECT 
    count(*) AS total_connections,
    count(*) FILTER (WHERE state = 'active') AS active,
    count(*) FILTER (WHERE state = 'idle') AS idle,
    count(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_transaction
FROM pg_stat_activity
WHERE datname = current_database();

-- Connections by application
SELECT 
    application_name,
    count(*) AS connections,
    count(*) FILTER (WHERE state = 'active') AS active
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY application_name
ORDER BY connections DESC;

-- ============================================================================
-- 7. LOCK ANALYSIS
-- ============================================================================

-- Current locks
SELECT 
    locktype,
    database,
    relation::regclass,
    mode,
    granted
FROM pg_locks
WHERE NOT granted
ORDER BY relation;

-- Blocking queries
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- ============================================================================
-- 8. CACHE HIT RATIO
-- ============================================================================

-- Buffer cache hit ratio (should be > 95%)
SELECT 
    sum(heap_blks_read) AS heap_read,
    sum(heap_blks_hit) AS heap_hit,
    (sum(heap_blks_hit) * 100.0 / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0)) AS cache_hit_ratio
FROM pg_statio_user_tables;

-- Index cache hit ratio (should be > 95%)
SELECT 
    sum(idx_blks_read) AS index_read,
    sum(idx_blks_hit) AS index_hit,
    (sum(idx_blks_hit) * 100.0 / NULLIF(sum(idx_blks_hit) + sum(idx_blks_read), 0)) AS index_cache_hit_ratio
FROM pg_statio_user_indexes;

-- ============================================================================
-- 9. QUERY OPTIMIZATION EXAMPLES
-- ============================================================================

-- Example: Optimized decision lookup query
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT id, action, resource, allowed, timestamp
FROM decisions
WHERE actor = 'user:alice@example.com'
  AND timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC
LIMIT 100;

-- Example: Optimized audit log query
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT event_type, COUNT(*) AS count
FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY event_type
ORDER BY count DESC;

-- ============================================================================
-- 10. MAINTENANCE SCHEDULE RECOMMENDATIONS
-- ============================================================================

/*
RECOMMENDED MAINTENANCE SCHEDULE:

Daily (automated - autovacuum):
- Autovacuum runs automatically
- Monitor autovacuum_naptime (default: 1 minute)

Weekly (manual - Sunday 2 AM UTC):
- VACUUM ANALYZE decisions;
- VACUUM ANALYZE audit_logs;

Monthly (manual - first Sunday 3 AM UTC):
- REINDEX TABLE CONCURRENTLY decisions;
- REINDEX TABLE CONCURRENTLY audit_logs;
- Check and remove unused indexes

Quarterly:
- Review slow query log
- Analyze table bloat
- Adjust autovacuum parameters if needed
- Review and optimize connection pool settings

After bulk operations:
- ANALYZE affected tables
- Consider VACUUM if significant deletes/updates
*/
