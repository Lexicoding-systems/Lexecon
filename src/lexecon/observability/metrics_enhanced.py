"""
Enhanced Prometheus metrics for enterprise monitoring (Phase 6).

Extends base metrics with detailed observability for:
- Error tracking and categorization
- Cache performance
- Rate limiting
- Authentication/authorization
- Database operations
- Feature flag usage
"""

from prometheus_client import Counter, Gauge, Histogram, Summary

# ============================================================================
# Error & Exception Metrics
# ============================================================================

errors_total = Counter(
    "lexecon_errors_total",
    "Total errors by type and severity",
    ["error_type", "severity", "component"],
)

exceptions_total = Counter(
    "lexecon_exceptions_total",
    "Total exceptions caught",
    ["exception_class", "endpoint"],
)

error_recovery_total = Counter(
    "lexecon_error_recovery_total",
    "Total successful error recoveries",
    ["error_type", "recovery_method"],
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_hits_total = Counter(
    "lexecon_cache_hits_total",
    "Total cache hits",
    ["cache_name"],
)

cache_misses_total = Counter(
    "lexecon_cache_misses_total",
    "Total cache misses",
    ["cache_name"],
)

cache_evictions_total = Counter(
    "lexecon_cache_evictions_total",
    "Total cache evictions",
    ["cache_name", "reason"],
)

cache_size_bytes = Gauge(
    "lexecon_cache_size_bytes",
    "Current cache size in bytes",
    ["cache_name"],
)

cache_items = Gauge(
    "lexecon_cache_items",
    "Number of items in cache",
    ["cache_name"],
)

cache_operation_duration_seconds = Histogram(
    "lexecon_cache_operation_duration_seconds",
    "Cache operation duration",
    ["cache_name", "operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# ============================================================================
# Rate Limiting Metrics
# ============================================================================

rate_limit_hits_total = Counter(
    "lexecon_rate_limit_hits_total",
    "Total rate limit hits (requests blocked)",
    ["limiter_type", "user_id"],
)

rate_limit_current_usage = Gauge(
    "lexecon_rate_limit_current_usage",
    "Current rate limit usage",
    ["limiter_type", "user_id"],
)

rate_limit_resets_total = Counter(
    "lexecon_rate_limit_resets_total",
    "Total rate limit window resets",
    ["limiter_type"],
)

# ============================================================================
# Authentication & Authorization Metrics
# ============================================================================

auth_attempts_total = Counter(
    "lexecon_auth_attempts_total",
    "Total authentication attempts",
    ["method", "result"],
)

auth_failures_total = Counter(
    "lexecon_auth_failures_total",
    "Total authentication failures",
    ["method", "reason"],
)

mfa_challenges_total = Counter(
    "lexecon_mfa_challenges_total",
    "Total MFA challenges issued",
    ["method"],
)

mfa_verifications_total = Counter(
    "lexecon_mfa_verifications_total",
    "Total MFA verifications",
    ["method", "result"],
)

active_sessions = Gauge(
    "lexecon_active_sessions",
    "Number of active user sessions",
)

session_duration_seconds = Histogram(
    "lexecon_session_duration_seconds",
    "Session duration in seconds",
    buckets=(60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400),
)

password_expiration_warnings_total = Counter(
    "lexecon_password_expiration_warnings_total",
    "Total password expiration warnings issued",
)

# ============================================================================
# Database Metrics
# ============================================================================

db_connections_active = Gauge(
    "lexecon_db_connections_active",
    "Number of active database connections",
)

db_connections_idle = Gauge(
    "lexecon_db_connections_idle",
    "Number of idle database connections",
)

db_query_duration_seconds = Histogram(
    "lexecon_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

db_errors_total = Counter(
    "lexecon_db_errors_total",
    "Total database errors",
    ["error_type", "operation"],
)

db_transaction_duration_seconds = Histogram(
    "lexecon_db_transaction_duration_seconds",
    "Database transaction duration in seconds",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
)

# ============================================================================
# Feature Flag Metrics
# ============================================================================

feature_flag_evaluations_total = Counter(
    "lexecon_feature_flag_evaluations_total",
    "Total feature flag evaluations",
    ["flag_name", "result"],
)

feature_flag_errors_total = Counter(
    "lexecon_feature_flag_errors_total",
    "Total feature flag evaluation errors",
    ["flag_name", "error_type"],
)

# ============================================================================
# Business Metrics
# ============================================================================

compliance_violations_total = Counter(
    "lexecon_compliance_violations_total",
    "Total compliance violations detected",
    ["violation_type", "severity"],
)

audit_log_entries_total = Counter(
    "lexecon_audit_log_entries_total",
    "Total audit log entries created",
    ["event_type"],
)

risk_assessments_total = Counter(
    "lexecon_risk_assessments_total",
    "Total risk assessments performed",
    ["risk_level"],
)

# ============================================================================
# API Performance Metrics
# ============================================================================

api_latency_summary = Summary(
    "lexecon_api_latency_summary",
    "API latency summary statistics",
    ["endpoint", "method"],
)

api_response_size_bytes = Histogram(
    "lexecon_api_response_size_bytes",
    "API response size in bytes",
    ["endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000, 10000000),
)

concurrent_requests = Gauge(
    "lexecon_concurrent_requests",
    "Number of concurrent requests being processed",
)

# ============================================================================
# Background Job Metrics
# ============================================================================

background_jobs_queued = Gauge(
    "lexecon_background_jobs_queued",
    "Number of queued background jobs",
    ["job_type"],
)

background_jobs_completed_total = Counter(
    "lexecon_background_jobs_completed_total",
    "Total background jobs completed",
    ["job_type", "result"],
)

background_job_duration_seconds = Histogram(
    "lexecon_background_job_duration_seconds",
    "Background job duration in seconds",
    ["job_type"],
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600),
)


class EnhancedMetricsCollector:
    """Enhanced metrics collector with advanced observability."""

    def __init__(self):
        """Initialize enhanced metrics collector."""
        pass

    # Error tracking
    def record_error(self, error_type: str, severity: str, component: str):
        """Record an error occurrence."""
        errors_total.labels(error_type=error_type, severity=severity, component=component).inc()

    def record_exception(self, exception_class: str, endpoint: str):
        """Record an exception."""
        exceptions_total.labels(exception_class=exception_class, endpoint=endpoint).inc()

    def record_error_recovery(self, error_type: str, recovery_method: str):
        """Record successful error recovery."""
        error_recovery_total.labels(error_type=error_type, recovery_method=recovery_method).inc()

    # Cache operations
    def record_cache_hit(self, cache_name: str):
        """Record cache hit."""
        cache_hits_total.labels(cache_name=cache_name).inc()

    def record_cache_miss(self, cache_name: str):
        """Record cache miss."""
        cache_misses_total.labels(cache_name=cache_name).inc()

    def record_cache_eviction(self, cache_name: str, reason: str):
        """Record cache eviction."""
        cache_evictions_total.labels(cache_name=cache_name, reason=reason).inc()

    def update_cache_size(self, cache_name: str, size_bytes: float):
        """Update cache size gauge."""
        cache_size_bytes.labels(cache_name=cache_name).set(size_bytes)

    def update_cache_items(self, cache_name: str, count: int):
        """Update cache item count."""
        cache_items.labels(cache_name=cache_name).set(count)

    # Rate limiting
    def record_rate_limit_hit(self, limiter_type: str, user_id: str):
        """Record rate limit hit."""
        rate_limit_hits_total.labels(limiter_type=limiter_type, user_id=user_id).inc()

    def update_rate_limit_usage(self, limiter_type: str, user_id: str, usage: float):
        """Update current rate limit usage."""
        rate_limit_current_usage.labels(limiter_type=limiter_type, user_id=user_id).set(usage)

    def record_rate_limit_reset(self, limiter_type: str):
        """Record rate limit window reset."""
        rate_limit_resets_total.labels(limiter_type=limiter_type).inc()

    # Authentication
    def record_auth_attempt(self, method: str, result: str):
        """Record authentication attempt."""
        auth_attempts_total.labels(method=method, result=result).inc()

    def record_auth_failure(self, method: str, reason: str):
        """Record authentication failure."""
        auth_failures_total.labels(method=method, reason=reason).inc()

    def record_mfa_challenge(self, method: str):
        """Record MFA challenge issued."""
        mfa_challenges_total.labels(method=method).inc()

    def record_mfa_verification(self, method: str, result: str):
        """Record MFA verification."""
        mfa_verifications_total.labels(method=method, result=result).inc()

    def update_active_sessions(self, count: int):
        """Update active sessions count."""
        active_sessions.set(count)

    # Database
    def update_db_connections(self, active: int, idle: int):
        """Update database connection counts."""
        db_connections_active.set(active)
        db_connections_idle.set(idle)

    def record_db_error(self, error_type: str, operation: str):
        """Record database error."""
        db_errors_total.labels(error_type=error_type, operation=operation).inc()

    # Feature flags
    def record_feature_flag_evaluation(self, flag_name: str, result: str):
        """Record feature flag evaluation."""
        feature_flag_evaluations_total.labels(flag_name=flag_name, result=result).inc()

    def record_feature_flag_error(self, flag_name: str, error_type: str):
        """Record feature flag error."""
        feature_flag_errors_total.labels(flag_name=flag_name, error_type=error_type).inc()

    # Business metrics
    def record_compliance_violation(self, violation_type: str, severity: str):
        """Record compliance violation."""
        compliance_violations_total.labels(
            violation_type=violation_type, severity=severity
        ).inc()

    def record_audit_log_entry(self, event_type: str):
        """Record audit log entry."""
        audit_log_entries_total.labels(event_type=event_type).inc()

    def record_risk_assessment(self, risk_level: str):
        """Record risk assessment."""
        risk_assessments_total.labels(risk_level=risk_level).inc()

    # API performance
    def update_concurrent_requests(self, count: int):
        """Update concurrent requests gauge."""
        concurrent_requests.set(count)

    # Background jobs
    def update_background_jobs_queued(self, job_type: str, count: int):
        """Update queued background jobs."""
        background_jobs_queued.labels(job_type=job_type).set(count)

    def record_background_job_completion(self, job_type: str, result: str):
        """Record background job completion."""
        background_jobs_completed_total.labels(job_type=job_type, result=result).inc()


# Global instance
enhanced_metrics = EnhancedMetricsCollector()
