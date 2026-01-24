"""Observability utilities for Lexecon.

This module provides production-grade observability infrastructure:

- **Context**: Async-safe context propagation with W3C Trace Context support
- **Tracing**: Distributed tracing with OTLP export support
- **Metrics**: Cardinality-safe Prometheus metrics with SLI definitions
- **Logging**: Structured JSON logging with trace correlation
- **Errors**: Error correlation across logs, traces, and metrics
- **Circuit Breakers**: Resilience patterns with full observability
- **Health Checks**: Kubernetes-compatible probes with dependency monitoring

Quick Start:
    from lexecon.observability import (
        observe,
        traced,
        record_decision,
        record_error,
        health_manager,
        get_circuit_breaker,
    )

    # Trace a function
    @traced("my_operation")
    def my_function():
        ...

    # Use context for manual tracing
    with observe("process_request") as ctx:
        ctx.with_attribute("user_id", user_id)
        ...

    # Record errors with correlation
    try:
        ...
    except Exception as e:
        record_error(e)
        raise

    # Use circuit breaker for external calls
    cb = get_circuit_breaker("redis")

    @cb.protect
    def call_redis():
        ...
"""

# Logging (backward compatible)
# Circuit breaker (new)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    circuit_breakers,
    get_circuit_breaker,
)

# Context propagation (new)
from .context import (
    ObservabilityContext,
    SpanContext,
    create_context,
    get_current_context,
    hash_high_cardinality,
    observe,
    reset_context,
    set_current_context,
)

# Error correlation (new)
from .errors import (
    ErrorCategory,
    ErrorCorrelator,
    ErrorRecord,
    ErrorSeverity,
    error_boundary,
    error_correlator,
    record_error,
)

# Health checks - import both old and new
from .health import HealthCheck, HealthStatus, health_check
from .health_v2 import (
    DependencyHealth,
    HealthCheckManager,
    HealthCheckResult,
    health_manager,
    liveness,
    readiness,
    startup,
)
from .health_v2 import HealthStatus as HealthStatusV2
from .logging import (
    LoggerAdapter,
    StructuredFormatter,
    configure_logging,
    get_logger,
    request_id_var,
    user_id_var,
)

# Metrics - import both old and new for backward compatibility
from .metrics import metrics, record_decision, record_policy_load
from .metrics_v2 import (
    CircuitState,
    MetricsCollector,
    timed_operation,
)
from .metrics_v2 import metrics as metrics_v2
from .metrics_v2 import record_decision as record_decision_v2

# Tracing - import both old and new for backward compatibility
from .tracing import trace_function, tracer
from .tracing_v2 import (
    Span,
    SpanContextManager,
    TracingManager,
    extract_trace_context,
    inject_trace_context,
    traced,
    traced_async,
)
from .tracing_v2 import tracer as tracer_v2

__all__ = [
    # Logging
    "configure_logging",
    "get_logger",
    "LoggerAdapter",
    "StructuredFormatter",
    "request_id_var",
    "user_id_var",
    # Context
    "ObservabilityContext",
    "SpanContext",
    "create_context",
    "get_current_context",
    "set_current_context",
    "reset_context",
    "observe",
    "hash_high_cardinality",
    # Tracing (backward compatible)
    "tracer",
    "trace_function",
    # Tracing v2
    "tracer_v2",
    "traced",
    "traced_async",
    "TracingManager",
    "Span",
    "SpanContextManager",
    "inject_trace_context",
    "extract_trace_context",
    # Metrics (backward compatible)
    "metrics",
    "record_decision",
    "record_policy_load",
    # Metrics v2
    "metrics_v2",
    "record_decision_v2",
    "MetricsCollector",
    "CircuitState",
    "timed_operation",
    # Health (backward compatible)
    "health_check",
    "HealthCheck",
    "HealthStatus",
    # Health v2
    "health_manager",
    "HealthCheckManager",
    "HealthCheckResult",
    "DependencyHealth",
    "HealthStatusV2",
    "liveness",
    "readiness",
    "startup",
    # Errors
    "record_error",
    "error_correlator",
    "ErrorCorrelator",
    "ErrorRecord",
    "ErrorSeverity",
    "ErrorCategory",
    "error_boundary",
    # Circuit Breaker
    "get_circuit_breaker",
    "circuit_breakers",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerRegistry",
]


def initialize_observability(
    service_name: str = "lexecon",
    version: str = "0.1.0",
    environment: str = "development",
    log_level: str = "INFO",
    log_format: str = "json",
    enable_tracing: bool = True,
) -> None:
    """Initialize all observability components.

    This is a convenience function to set up logging, tracing,
    metrics, and health checks in one call.

    Args:
        service_name: Name of the service
        version: Service version
        environment: Deployment environment
        log_level: Logging level
        log_format: Log format (json or text)
        enable_tracing: Whether to enable distributed tracing
    """
    # Configure logging
    configure_logging(level=log_level, format=log_format)

    # Initialize metrics
    metrics_v2.initialize(
        node_id=service_name,
        version=version,
        environment=environment,
    )

    # Initialize tracing
    if enable_tracing:
        tracer_v2.initialize()

    # Update health manager
    health_manager.service_name = service_name
    health_manager._version = version
    health_manager._environment = environment

    logger = get_logger(__name__)
    logger.info(
        f"Observability initialized for {service_name} v{version} ({environment})",
    )
