"""OpenTelemetry tracing for Lexecon."""

from typing import Any, Callable, Optional
from functools import wraps
import time

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    trace = None  # type: ignore
    TracerProvider = None  # type: ignore


class TracingManager:
    """Manage OpenTelemetry tracing."""

    def __init__(self) -> None:
        """Initialize tracing manager."""
        self.enabled = False
        self.tracer: Optional[Any] = None

        if TRACING_AVAILABLE:
            self._setup_tracing()

    def _setup_tracing(self) -> None:
        """Set up OpenTelemetry tracing."""
        if not TRACING_AVAILABLE:
            return

        # Set up tracer provider
        provider = TracerProvider()
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        self.enabled = True

    def start_span(self, name: str, **attributes: Any) -> Any:
        """Start a new span."""
        if not self.enabled or not self.tracer:
            return None

        span = self.tracer.start_span(name)
        for key, value in attributes.items():
            span.set_attribute(key, value)
        return span

    def instrument_fastapi(self, app: Any) -> None:
        """Instrument FastAPI application."""
        if TRACING_AVAILABLE:
            FastAPIInstrumentor.instrument_app(app)


# Global tracing instance
tracer = TracingManager()


def trace_function(name: Optional[str] = None) -> Callable:
    """Decorator to trace a function.

    Args:
        name: Span name (defaults to function name)

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        span_name = name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not tracer.enabled:
                return func(*args, **kwargs)

            with tracer.start_span(span_name) as span:
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise
                finally:
                    duration = time.time() - start
                    span.set_attribute("duration_ms", duration * 1000)

        return wrapper

    return decorator
