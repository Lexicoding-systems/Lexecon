"""Production-grade metrics for Lexecon with cardinality management.

This module provides:
- Cardinality-safe metrics (hashed high-cardinality labels)
- SLI/SLO definitions for governance operations
- Dependency health metrics (Redis, DB, etc.)
- Circuit breaker state metrics
- Proper histogram buckets for latency percentiles
"""

import time
from enum import Enum
from typing import Any, Callable

from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

from .context import hash_high_cardinality

# SLI histogram buckets optimized for different latency profiles
# Fast operations (cache hits, simple lookups): 1ms - 100ms
FAST_BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1)

# Medium operations (DB queries, policy evaluation): 10ms - 1s
MEDIUM_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0)

# Slow operations (complex aggregations, external calls): 100ms - 30s
SLOW_BUCKETS = (0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)

# Default buckets matching Prometheus recommendations
DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# =============================================================================
# Service Info
# =============================================================================

service_info = Info(
    "lexecon_service",
    "Lexecon service information",
)


# =============================================================================
# HTTP Request Metrics (cardinality-safe)
# =============================================================================

http_requests_total = Counter(
    "lexecon_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint_group", "status_class"],  # Grouped endpoints, status class (2xx, 4xx, 5xx)
)

http_request_duration_seconds = Histogram(
    "lexecon_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint_group"],
    buckets=MEDIUM_BUCKETS,
)

http_requests_in_flight = Gauge(
    "lexecon_http_requests_in_flight",
    "Number of HTTP requests currently being processed",
)


# =============================================================================
# Decision Metrics (SLI for governance)
# =============================================================================

# Total decisions - using hashed actor IDs to prevent cardinality explosion
decisions_total = Counter(
    "lexecon_decisions_total",
    "Total governance decisions made",
    ["allowed", "risk_level", "policy_mode"],  # Removed raw 'actor' label
)

decision_evaluation_duration_seconds = Histogram(
    "lexecon_decision_evaluation_duration_seconds",
    "Decision evaluation duration in seconds (SLI)",
    ["policy_mode", "complexity"],  # complexity: simple, moderate, complex
    buckets=MEDIUM_BUCKETS,
)

decisions_denied_total = Counter(
    "lexecon_decisions_denied_total",
    "Total decisions denied by reason category",
    ["reason_category"],  # Removed raw 'actor' label
)

# SLI: Decision availability
decision_errors_total = Counter(
    "lexecon_decision_errors_total",
    "Total decision processing errors (SLI)",
    ["error_type"],
)

# Actor-specific metrics with hashed labels for safe cardinality
decisions_by_actor_hash = Counter(
    "lexecon_decisions_by_actor_hash_total",
    "Decisions by hashed actor ID (cardinality-safe)",
    ["actor_hash", "allowed"],
)


# =============================================================================
# Policy Metrics
# =============================================================================

policies_loaded_total = Counter(
    "lexecon_policies_loaded_total",
    "Total policies loaded",
    ["policy_version"],  # Use version instead of name for lower cardinality
)

active_policies = Gauge(
    "lexecon_active_policies",
    "Number of currently active policies",
)

policy_evaluation_errors_total = Counter(
    "lexecon_policy_evaluation_errors_total",
    "Total policy evaluation errors",
    ["error_type"],
)

policy_cache_operations = Counter(
    "lexecon_policy_cache_operations_total",
    "Policy cache operations",
    ["operation", "result"],  # operation: get/set, result: hit/miss/error
)


# =============================================================================
# Ledger Metrics
# =============================================================================

ledger_entries_total = Counter(
    "lexecon_ledger_entries_total",
    "Total ledger entries created",
    ["entry_type"],
)

ledger_verification_duration_seconds = Histogram(
    "lexecon_ledger_verification_duration_seconds",
    "Ledger verification duration in seconds",
    buckets=SLOW_BUCKETS,
)

ledger_integrity_checks_total = Counter(
    "lexecon_ledger_integrity_checks_total",
    "Total ledger integrity checks",
    ["result"],  # valid, invalid, error
)

ledger_chain_length = Gauge(
    "lexecon_ledger_chain_length",
    "Current length of the ledger chain",
)


# =============================================================================
# Token Metrics
# =============================================================================

tokens_issued_total = Counter(
    "lexecon_tokens_issued_total",
    "Total capability tokens issued",
    ["scope_type"],  # Grouped scope types instead of raw scopes
)

tokens_verified_total = Counter(
    "lexecon_tokens_verified_total",
    "Total token verifications",
    ["valid", "failure_reason"],
)

active_tokens = Gauge(
    "lexecon_active_tokens",
    "Number of currently active capability tokens",
)

token_expiration_seconds = Histogram(
    "lexecon_token_expiration_seconds",
    "Token TTL in seconds at issuance",
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400, 28800, 86400),
)


# =============================================================================
# Dependency Health Metrics
# =============================================================================

# Database connection pool
db_connections_total = Gauge(
    "lexecon_db_connections_total",
    "Total database connections",
    ["pool", "state"],  # state: active, idle, waiting
)

db_query_duration_seconds = Histogram(
    "lexecon_db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],  # select, insert, update, delete
    buckets=MEDIUM_BUCKETS,
)

db_errors_total = Counter(
    "lexecon_db_errors_total",
    "Total database errors",
    ["error_type"],
)

# Redis cache
cache_operations_total = Counter(
    "lexecon_cache_operations_total",
    "Total cache operations",
    ["operation", "result"],  # operation: get/set/delete, result: hit/miss/error
)

cache_operation_duration_seconds = Histogram(
    "lexecon_cache_operation_duration_seconds",
    "Cache operation duration in seconds",
    ["operation"],
    buckets=FAST_BUCKETS,
)

cache_connections = Gauge(
    "lexecon_cache_connections",
    "Number of cache connections",
    ["state"],  # connected, disconnected
)


# =============================================================================
# Circuit Breaker Metrics
# =============================================================================

circuit_breaker_state = Gauge(
    "lexecon_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["service"],
)

circuit_breaker_state_changes_total = Counter(
    "lexecon_circuit_breaker_state_changes_total",
    "Total circuit breaker state changes",
    ["service", "from_state", "to_state"],
)

circuit_breaker_requests_total = Counter(
    "lexecon_circuit_breaker_requests_total",
    "Total requests through circuit breaker",
    ["service", "result"],  # result: success, failure, rejected
)


# =============================================================================
# System Metrics
# =============================================================================

node_info_metric = Gauge(
    "lexecon_node_info",
    "Node information",
    ["node_id", "version", "environment"],
)

node_uptime_seconds = Gauge(
    "lexecon_node_uptime_seconds",
    "Node uptime in seconds",
)


# =============================================================================
# Metrics Collector Class
# =============================================================================

class MetricsCollector:
    """Production metrics collection with cardinality management."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.start_time = time.time()
        self._initialized = False

    def initialize(
        self,
        node_id: str = "unknown",
        version: str = "0.1.0",
        environment: str = "development",
    ) -> None:
        """Initialize service metrics.

        Args:
            node_id: Unique node identifier
            version: Service version
            environment: Deployment environment
        """
        if self._initialized:
            return

        service_info.info({
            "version": version,
            "environment": environment,
            "node_id": node_id,
        })

        node_info_metric.labels(
            node_id=node_id,
            version=version,
            environment=environment,
        ).set(1)

        self._initialized = True

    # -------------------------------------------------------------------------
    # HTTP Metrics
    # -------------------------------------------------------------------------

    def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
    ) -> None:
        """Record HTTP request metrics with cardinality management.

        Args:
            method: HTTP method
            endpoint: Request endpoint
            status: HTTP status code
            duration: Request duration in seconds
        """
        # Group endpoints to prevent cardinality explosion
        endpoint_group = self._normalize_endpoint(endpoint)
        status_class = f"{status // 100}xx"

        http_requests_total.labels(
            method=method,
            endpoint_group=endpoint_group,
            status_class=status_class,
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint_group=endpoint_group,
        ).observe(duration)

    def _normalize_endpoint(self, endpoint: str) -> str:
        """Normalize endpoint to prevent cardinality explosion.

        Replaces dynamic path segments with placeholders.

        Args:
            endpoint: Raw endpoint path

        Returns:
            Normalized endpoint path
        """
        import re

        # Replace UUIDs
        endpoint = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            endpoint,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs
        endpoint = re.sub(r"/\d+", "/{id}", endpoint)

        # Replace base64-like tokens
        endpoint = re.sub(r"/[A-Za-z0-9_-]{20,}", "/{token}", endpoint)

        return endpoint

    # -------------------------------------------------------------------------
    # Decision Metrics
    # -------------------------------------------------------------------------

    def record_decision(
        self,
        allowed: bool,
        actor: str,
        risk_level: int,
        duration: float,
        policy_mode: str = "strict",
        complexity: str = "moderate",
    ) -> None:
        """Record decision metrics with cardinality management.

        Args:
            allowed: Whether decision was allowed
            actor: Actor identifier (will be hashed)
            risk_level: Risk level (0-5)
            duration: Evaluation duration in seconds
            policy_mode: Policy evaluation mode
            complexity: Decision complexity
        """
        # Main decision counter (low cardinality)
        decisions_total.labels(
            allowed=str(allowed),
            risk_level=str(min(risk_level, 5)),  # Cap risk level
            policy_mode=policy_mode,
        ).inc()

        # Duration histogram for SLI
        decision_evaluation_duration_seconds.labels(
            policy_mode=policy_mode,
            complexity=complexity,
        ).observe(duration)

        # Actor-specific counter with hashed ID
        actor_hash = hash_high_cardinality(actor, prefix="actor_")
        decisions_by_actor_hash.labels(
            actor_hash=actor_hash,
            allowed=str(allowed),
        ).inc()

    def record_denial(self, reason_category: str, actor: str) -> None:
        """Record decision denial.

        Args:
            reason_category: Category of denial reason
            actor: Actor identifier (not used in metric, kept for logging)
        """
        decisions_denied_total.labels(reason_category=reason_category).inc()

    def record_decision_error(self, error_type: str) -> None:
        """Record decision processing error (SLI).

        Args:
            error_type: Type of error
        """
        decision_errors_total.labels(error_type=error_type).inc()

    # -------------------------------------------------------------------------
    # Dependency Metrics
    # -------------------------------------------------------------------------

    def record_db_query(self, query_type: str, duration: float) -> None:
        """Record database query metrics.

        Args:
            query_type: Type of query
            duration: Query duration in seconds
        """
        db_query_duration_seconds.labels(query_type=query_type).observe(duration)

    def record_db_error(self, error_type: str) -> None:
        """Record database error.

        Args:
            error_type: Type of error
        """
        db_errors_total.labels(error_type=error_type).inc()

    def update_db_connections(self, pool: str, active: int, idle: int, waiting: int) -> None:
        """Update database connection pool metrics.

        Args:
            pool: Pool name
            active: Active connections
            idle: Idle connections
            waiting: Waiting connections
        """
        db_connections_total.labels(pool=pool, state="active").set(active)
        db_connections_total.labels(pool=pool, state="idle").set(idle)
        db_connections_total.labels(pool=pool, state="waiting").set(waiting)

    def record_cache_operation(
        self,
        operation: str,
        result: str,
        duration: float,
    ) -> None:
        """Record cache operation metrics.

        Args:
            operation: Operation type (get, set, delete)
            result: Operation result (hit, miss, error)
            duration: Operation duration in seconds
        """
        cache_operations_total.labels(operation=operation, result=result).inc()
        cache_operation_duration_seconds.labels(operation=operation).observe(duration)

    def update_cache_connection(self, connected: bool) -> None:
        """Update cache connection status.

        Args:
            connected: Whether cache is connected
        """
        cache_connections.labels(state="connected").set(1 if connected else 0)
        cache_connections.labels(state="disconnected").set(0 if connected else 1)

    # -------------------------------------------------------------------------
    # Circuit Breaker Metrics
    # -------------------------------------------------------------------------

    def record_circuit_state_change(
        self,
        service: str,
        from_state: CircuitState,
        to_state: CircuitState,
    ) -> None:
        """Record circuit breaker state change.

        Args:
            service: Service name
            from_state: Previous state
            to_state: New state
        """
        state_value = {
            CircuitState.CLOSED: 0,
            CircuitState.OPEN: 1,
            CircuitState.HALF_OPEN: 2,
        }

        circuit_breaker_state.labels(service=service).set(state_value[to_state])

        circuit_breaker_state_changes_total.labels(
            service=service,
            from_state=from_state.value,
            to_state=to_state.value,
        ).inc()

    def record_circuit_request(self, service: str, result: str) -> None:
        """Record request through circuit breaker.

        Args:
            service: Service name
            result: Request result (success, failure, rejected)
        """
        circuit_breaker_requests_total.labels(
            service=service,
            result=result,
        ).inc()

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_uptime(self) -> float:
        """Get node uptime in seconds."""
        uptime = time.time() - self.start_time
        node_uptime_seconds.set(uptime)
        return uptime

    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format."""
        self.get_uptime()  # Update uptime before export
        return generate_latest(REGISTRY)


# Global metrics instance
metrics = MetricsCollector()


# =============================================================================
# Convenience Functions
# =============================================================================

def record_decision(
    allowed: bool,
    actor: str,
    risk_level: int,
    duration: float,
    **kwargs: Any,
) -> None:
    """Record a decision metric."""
    metrics.record_decision(allowed, actor, risk_level, duration, **kwargs)


def record_policy_load(policy_name: str, version: str = "1.0") -> None:
    """Record a policy load metric."""
    policies_loaded_total.labels(policy_version=version).inc()
    active_policies.inc()


def timed_operation(metric_histogram: Histogram, **labels: str) -> Callable:
    """Decorator to time operations and record to histogram.

    Args:
        metric_histogram: Histogram to record to
        **labels: Labels for the histogram

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                metric_histogram.labels(**labels).observe(duration)

        return wrapper

    return decorator
