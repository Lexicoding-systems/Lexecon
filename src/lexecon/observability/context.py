"""Observability context management for distributed tracing and correlation.

This module provides async-safe context propagation using contextvars,
implementing W3C Trace Context standard for distributed tracing correlation.
"""

import hashlib
import secrets
import time
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# W3C Trace Context format: version-trace_id-parent_id-flags
# https://www.w3.org/TR/trace-context/
TRACE_CONTEXT_VERSION = "00"
TRACE_FLAG_SAMPLED = "01"
TRACE_FLAG_NOT_SAMPLED = "00"


@dataclass
class SpanContext:
    """Immutable span context for W3C Trace Context propagation."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    is_sampled: bool = True
    baggage: Dict[str, str] = field(default_factory=dict)

    def to_traceparent(self) -> str:
        """Serialize to W3C traceparent header format.

        Returns:
            traceparent header value: {version}-{trace_id}-{span_id}-{flags}
        """
        flags = TRACE_FLAG_SAMPLED if self.is_sampled else TRACE_FLAG_NOT_SAMPLED
        return f"{TRACE_CONTEXT_VERSION}-{self.trace_id}-{self.span_id}-{flags}"

    def to_tracestate(self) -> str:
        """Serialize baggage to W3C tracestate header format.

        Returns:
            tracestate header value
        """
        if not self.baggage:
            return ""
        return ",".join(f"lexecon={k}={v}" for k, v in self.baggage.items())

    @classmethod
    def from_traceparent(cls, traceparent: str, tracestate: Optional[str] = None) -> Optional["SpanContext"]:
        """Parse W3C traceparent header.

        Args:
            traceparent: W3C traceparent header value
            tracestate: Optional W3C tracestate header value

        Returns:
            SpanContext if valid, None otherwise
        """
        try:
            parts = traceparent.split("-")
            if len(parts) != 4:
                return None

            version, trace_id, parent_id, flags = parts

            # Validate format
            if version != TRACE_CONTEXT_VERSION:
                return None
            if len(trace_id) != 32 or len(parent_id) != 16:
                return None

            is_sampled = flags == TRACE_FLAG_SAMPLED

            # Parse tracestate baggage
            baggage: Dict[str, str] = {}
            if tracestate:
                for item in tracestate.split(","):
                    if item.startswith("lexecon="):
                        kv = item[8:].split("=", 1)
                        if len(kv) == 2:
                            baggage[kv[0]] = kv[1]

            return cls(
                trace_id=trace_id,
                span_id=_generate_span_id(),  # Generate new span ID for this service
                parent_span_id=parent_id,
                is_sampled=is_sampled,
                baggage=baggage,
            )
        except (ValueError, IndexError):
            return None


@dataclass
class ObservabilityContext:
    """Complete observability context for a request/operation.

    Combines tracing, logging, and metrics context for unified observability.
    """

    # Tracing context
    span_context: Optional[SpanContext] = None

    # Request context
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Operation context
    operation_name: Optional[str] = None
    service_name: str = "lexecon"

    # Timing
    start_time: float = field(default_factory=time.time)

    # Custom attributes for logging/tracing
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Error tracking
    error: Optional[Exception] = None
    error_recorded: bool = False

    @property
    def trace_id(self) -> Optional[str]:
        """Get trace ID for correlation."""
        return self.span_context.trace_id if self.span_context else None

    @property
    def span_id(self) -> Optional[str]:
        """Get current span ID."""
        return self.span_context.span_id if self.span_context else None

    @property
    def duration_ms(self) -> float:
        """Get duration since context creation in milliseconds."""
        return (time.time() - self.start_time) * 1000

    def with_attribute(self, key: str, value: Any) -> "ObservabilityContext":
        """Add attribute and return self for chaining."""
        self.attributes[key] = value
        return self

    def record_error(self, error: Exception) -> None:
        """Record an error in this context."""
        self.error = error
        self.error_recorded = True

    def get_log_context(self) -> Dict[str, Any]:
        """Get context dict for structured logging.

        Returns:
            Dict with trace correlation IDs and context
        """
        ctx: Dict[str, Any] = {}

        if self.trace_id:
            ctx["trace_id"] = self.trace_id
        if self.span_id:
            ctx["span_id"] = self.span_id
        if self.request_id:
            ctx["request_id"] = self.request_id
        if self.user_id:
            ctx["user_id"] = self.user_id
        if self.operation_name:
            ctx["operation"] = self.operation_name

        ctx.update(self.attributes)
        return ctx


# Context variable for current observability context (async-safe)
_current_context: ContextVar[Optional[ObservabilityContext]] = ContextVar("obs_context", default=None)


def _generate_trace_id() -> str:
    """Generate a 128-bit trace ID as 32 hex characters."""
    return secrets.token_hex(16)


def _generate_span_id() -> str:
    """Generate a 64-bit span ID as 16 hex characters."""
    return secrets.token_hex(8)


def _generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"req_{secrets.token_hex(12)}"


def get_current_context() -> Optional[ObservabilityContext]:
    """Get the current observability context.

    Returns:
        Current ObservabilityContext or None if not in a traced context
    """
    return _current_context.get()


def set_current_context(ctx: ObservabilityContext) -> Token[Optional[ObservabilityContext]]:
    """Set the current observability context.

    Args:
        ctx: ObservabilityContext to set

    Returns:
        Token for resetting the context
    """
    return _current_context.set(ctx)


def reset_context(token: Token[Optional[ObservabilityContext]]) -> None:
    """Reset context to previous state.

    Args:
        token: Token from set_current_context
    """
    _current_context.reset(token)


def create_context(
    operation_name: str,
    parent_context: Optional[ObservabilityContext] = None,
    traceparent: Optional[str] = None,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    is_sampled: bool = True,
    **attributes: Any,
) -> ObservabilityContext:
    """Create a new observability context.

    Args:
        operation_name: Name of the operation being traced
        parent_context: Parent context for nested spans
        traceparent: W3C traceparent header for distributed tracing
        request_id: Optional request ID (generated if not provided)
        user_id: Optional user ID
        is_sampled: Whether this trace should be sampled
        **attributes: Additional attributes

    Returns:
        New ObservabilityContext
    """
    # Determine span context
    span_context: Optional[SpanContext] = None

    if traceparent:
        # Parse incoming trace context
        span_context = SpanContext.from_traceparent(traceparent)

    if not span_context and parent_context and parent_context.span_context:
        # Create child span from parent
        parent = parent_context.span_context
        span_context = SpanContext(
            trace_id=parent.trace_id,
            span_id=_generate_span_id(),
            parent_span_id=parent.span_id,
            is_sampled=parent.is_sampled,
            baggage=parent.baggage.copy(),
        )

    if not span_context:
        # Create new root span
        span_context = SpanContext(
            trace_id=_generate_trace_id(),
            span_id=_generate_span_id(),
            is_sampled=is_sampled,
        )

    # Inherit request context from parent if not provided
    if parent_context:
        request_id = request_id or parent_context.request_id
        user_id = user_id or parent_context.user_id

    return ObservabilityContext(
        span_context=span_context,
        request_id=request_id or _generate_request_id(),
        user_id=user_id,
        operation_name=operation_name,
        attributes=dict(attributes),
    )


def hash_high_cardinality(value: str, prefix: str = "") -> str:
    """Hash a high-cardinality value for safe metric labeling.

    This prevents cardinality explosion in Prometheus by hashing
    unbounded values like user IDs, IP addresses, etc.

    Args:
        value: High-cardinality value to hash
        prefix: Optional prefix for the hash

    Returns:
        Hashed value safe for metric labels (8 char hex)
    """
    h = hashlib.sha256(value.encode()).hexdigest()[:8]
    return f"{prefix}{h}" if prefix else h


class ContextManager:
    """Context manager for observability context lifecycle."""

    def __init__(
        self,
        operation_name: str,
        parent_context: Optional[ObservabilityContext] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize context manager.

        Args:
            operation_name: Name of the operation
            parent_context: Optional parent context
            **kwargs: Additional context attributes
        """
        self.operation_name = operation_name
        self.parent_context = parent_context or get_current_context()
        self.kwargs = kwargs
        self.context: Optional[ObservabilityContext] = None
        self.token: Optional[Token[Optional[ObservabilityContext]]] = None

    def __enter__(self) -> ObservabilityContext:
        """Enter context and set as current."""
        self.context = create_context(
            operation_name=self.operation_name,
            parent_context=self.parent_context,
            **self.kwargs,
        )
        self.token = set_current_context(self.context)
        return self.context

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and restore previous."""
        if exc_val and self.context:
            self.context.record_error(exc_val)

        if self.token:
            reset_context(self.token)

    async def __aenter__(self) -> ObservabilityContext:
        """Async enter context."""
        return self.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async exit context."""
        self.__exit__(exc_type, exc_val, exc_tb)


def observe(operation_name: str, **kwargs: Any) -> ContextManager:
    """Create an observability context manager.

    Usage:
        with observe("process_decision") as ctx:
            # Do work
            ctx.with_attribute("policy_id", policy_id)

        async with observe("async_operation") as ctx:
            # Async work
            await some_async_call()

    Args:
        operation_name: Name of the operation
        **kwargs: Additional context attributes

    Returns:
        ContextManager for use with 'with' or 'async with'
    """
    return ContextManager(operation_name, **kwargs)
