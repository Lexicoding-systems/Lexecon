"""Production-grade distributed tracing for Lexecon.

This module provides:
- Async-safe tracing with proper context propagation
- W3C Trace Context standard support
- OTLP exporter for production backends (Jaeger, Datadog, etc.)
- Trace-log correlation via ObservabilityContext
- Both sync and async function decorators
"""

import os
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .context import (
    ObservabilityContext,
    create_context,
    get_current_context,
    reset_context,
    set_current_context,
)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])

# Configuration from environment
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
OTLP_HEADERS = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "lexecon")
TRACING_ENABLED = os.getenv("LEXECON_TRACING_ENABLED", "true").lower() == "true"
SAMPLING_RATE = float(os.getenv("LEXECON_TRACE_SAMPLING_RATE", "1.0"))

# Optional OpenTelemetry imports
try:
    from opentelemetry import trace as otel_trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.propagate import extract, inject
    from opentelemetry.sdk.resources import SERVICE_NAME as RESOURCE_SERVICE_NAME
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.trace import SpanKind, Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class Span:
    """Represents an active tracing span with context propagation."""

    def __init__(
        self,
        name: str,
        context: ObservabilityContext,
        otel_span: Optional[Any] = None,
    ) -> None:
        """Initialize span.

        Args:
            name: Span name
            context: ObservabilityContext for this span
            otel_span: Optional OpenTelemetry span for export
        """
        self.name = name
        self.context = context
        self.otel_span = otel_span
        self.start_time = time.time()
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self._ended = False

    def set_attribute(self, key: str, value: Any) -> "Span":
        """Set a span attribute.

        Args:
            key: Attribute name
            value: Attribute value

        Returns:
            Self for chaining
        """
        self.attributes[key] = value
        self.context.with_attribute(key, value)

        if self.otel_span:
            self.otel_span.set_attribute(key, str(value))

        return self

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> "Span":
        """Add an event to the span.

        Args:
            name: Event name
            attributes: Optional event attributes

        Returns:
            Self for chaining
        """
        event = {
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        }
        self.events.append(event)

        if self.otel_span:
            self.otel_span.add_event(name, attributes or {})

        return self

    def record_exception(self, exception: Exception) -> "Span":
        """Record an exception in the span.

        Args:
            exception: Exception to record

        Returns:
            Self for chaining
        """
        self.context.record_error(exception)
        self.set_attribute("error", True)
        self.set_attribute("error.type", type(exception).__name__)
        self.set_attribute("error.message", str(exception))

        if self.otel_span:
            self.otel_span.record_exception(exception)
            self.otel_span.set_status(Status(StatusCode.ERROR, str(exception)))

        return self

    def set_status_ok(self) -> "Span":
        """Mark span as successful."""
        self.set_attribute("success", True)
        if self.otel_span:
            self.otel_span.set_status(Status(StatusCode.OK))
        return self

    def end(self) -> None:
        """End the span and record duration."""
        if self._ended:
            return

        self._ended = True
        duration_ms = (time.time() - self.start_time) * 1000
        self.set_attribute("duration_ms", duration_ms)

        if self.otel_span:
            self.otel_span.end()

    @property
    def trace_id(self) -> Optional[str]:
        """Get trace ID."""
        return self.context.trace_id

    @property
    def span_id(self) -> Optional[str]:
        """Get span ID."""
        return self.context.span_id


class TracingManager:
    """Production-grade tracing manager with OTLP support."""

    def __init__(self) -> None:
        """Initialize tracing manager."""
        self.enabled = TRACING_ENABLED
        self.sampling_rate = SAMPLING_RATE
        self._otel_tracer: Optional[Any] = None
        self._provider: Optional[Any] = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize tracing infrastructure."""
        if self._initialized or not self.enabled:
            return

        if OTEL_AVAILABLE:
            self._setup_opentelemetry()

        self._initialized = True

    def _setup_opentelemetry(self) -> None:
        """Set up OpenTelemetry tracing."""
        # Create resource with service info
        resource = Resource.create({
            RESOURCE_SERVICE_NAME: SERVICE_NAME,
            "service.version": os.getenv("LEXECON_VERSION", "0.1.0"),
            "deployment.environment": os.getenv("LEXECON_ENV", "development"),
        })

        # Create tracer provider
        self._provider = TracerProvider(resource=resource)

        # Add OTLP exporter if configured
        if OTLP_ENDPOINT:
            headers = {}
            if OTLP_HEADERS:
                for header in OTLP_HEADERS.split(","):
                    key, value = header.split("=", 1)
                    headers[key.strip()] = value.strip()

            otlp_exporter = OTLPSpanExporter(
                endpoint=OTLP_ENDPOINT,
                headers=headers,
            )
            self._provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        else:
            # Console exporter for development
            self._provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        otel_trace.set_tracer_provider(self._provider)
        self._otel_tracer = otel_trace.get_tracer(__name__)

    def start_span(
        self,
        name: str,
        parent_context: Optional[ObservabilityContext] = None,
        traceparent: Optional[str] = None,
        kind: str = "internal",
        **attributes: Any,
    ) -> Span:
        """Start a new span.

        Args:
            name: Span name
            parent_context: Optional parent context
            traceparent: W3C traceparent header for distributed tracing
            kind: Span kind (internal, server, client, producer, consumer)
            **attributes: Initial span attributes

        Returns:
            New Span instance
        """
        # Determine if we should sample this trace
        import random
        should_sample = random.random() < self.sampling_rate  # nosec

        # Create observability context
        ctx = create_context(
            operation_name=name,
            parent_context=parent_context or get_current_context(),
            traceparent=traceparent,
            is_sampled=should_sample,
            **attributes,
        )

        # Create OpenTelemetry span if available
        otel_span = None
        if OTEL_AVAILABLE and self._otel_tracer and should_sample:
            span_kind = {
                "internal": SpanKind.INTERNAL,
                "server": SpanKind.SERVER,
                "client": SpanKind.CLIENT,
                "producer": SpanKind.PRODUCER,
                "consumer": SpanKind.CONSUMER,
            }.get(kind, SpanKind.INTERNAL)

            otel_span = self._otel_tracer.start_span(
                name,
                kind=span_kind,
                attributes=attributes,
            )

        span = Span(name=name, context=ctx, otel_span=otel_span)

        # Set initial attributes
        for key, value in attributes.items():
            span.set_attribute(key, value)

        return span

    def get_traceparent(self) -> Optional[str]:
        """Get W3C traceparent header for current context.

        Returns:
            traceparent header value or None
        """
        ctx = get_current_context()
        if ctx and ctx.span_context:
            return ctx.span_context.to_traceparent()
        return None

    def instrument_fastapi(self, app: Any) -> None:
        """Instrument FastAPI application for automatic tracing.

        Args:
            app: FastAPI application instance
        """
        if OTEL_AVAILABLE and self.enabled:
            FastAPIInstrumentor.instrument_app(app)

    def shutdown(self) -> None:
        """Shutdown tracing and flush spans."""
        if self._provider:
            self._provider.shutdown()


# Global tracer instance
tracer = TracingManager()


class SpanContextManager:
    """Context manager for span lifecycle."""

    def __init__(self, span: Span) -> None:
        """Initialize with span."""
        self.span = span
        self.token: Optional[Any] = None

    def __enter__(self) -> Span:
        """Enter span context."""
        self.token = set_current_context(self.span.context)
        return self.span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit span context."""
        if exc_val:
            self.span.record_exception(exc_val)
        else:
            self.span.set_status_ok()

        self.span.end()

        if self.token:
            reset_context(self.token)

    async def __aenter__(self) -> Span:
        """Async enter span context."""
        return self.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async exit span context."""
        self.__exit__(exc_type, exc_val, exc_tb)


def traced(
    name: Optional[str] = None,
    kind: str = "internal",
    record_args: bool = False,
    record_result: bool = False,
) -> Callable[[F], F]:
    """Decorator for tracing sync functions.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind
        record_args: Whether to record function arguments as attributes
        record_result: Whether to record function result as attribute

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        span_name = name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not tracer.enabled:
                return func(*args, **kwargs)

            span = tracer.start_span(span_name, kind=kind)

            if record_args:
                span.set_attribute("args", str(args)[:256])
                span.set_attribute("kwargs", str(kwargs)[:256])

            with SpanContextManager(span):
                result = func(*args, **kwargs)

                if record_result:
                    span.set_attribute("result", str(result)[:256])

                return result

        return wrapper  # type: ignore

    return decorator


def traced_async(
    name: Optional[str] = None,
    kind: str = "internal",
    record_args: bool = False,
    record_result: bool = False,
) -> Callable[[F], F]:
    """Decorator for tracing async functions.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind
        record_args: Whether to record function arguments as attributes
        record_result: Whether to record function result as attribute

    Returns:
        Decorated async function
    """
    def decorator(func: F) -> F:
        span_name = name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not tracer.enabled:
                return await func(*args, **kwargs)

            span = tracer.start_span(span_name, kind=kind)

            if record_args:
                span.set_attribute("args", str(args)[:256])
                span.set_attribute("kwargs", str(kwargs)[:256])

            async with SpanContextManager(span):
                result = await func(*args, **kwargs)

                if record_result:
                    span.set_attribute("result", str(result)[:256])

                return result

        return wrapper  # type: ignore

    return decorator


def trace_function(name: Optional[str] = None) -> Callable[[F], F]:
    """Backwards-compatible decorator alias.

    This maintains compatibility with existing code using trace_function.

    Args:
        name: Span name

    Returns:
        Decorated function
    """
    return traced(name=name)


def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """Inject trace context into outgoing request headers.

    Args:
        headers: Existing headers dict

    Returns:
        Headers dict with trace context added
    """
    traceparent = tracer.get_traceparent()
    if traceparent:
        headers["traceparent"] = traceparent

    ctx = get_current_context()
    if ctx and ctx.span_context:
        tracestate = ctx.span_context.to_tracestate()
        if tracestate:
            headers["tracestate"] = tracestate

    return headers


def extract_trace_context(headers: Dict[str, str]) -> Optional[str]:
    """Extract trace context from incoming request headers.

    Args:
        headers: Request headers

    Returns:
        traceparent header value or None
    """
    return headers.get("traceparent") or headers.get("Traceparent")
