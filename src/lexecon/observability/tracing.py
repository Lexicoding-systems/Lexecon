"""
OpenTelemetry tracing for Lexecon (Phase 6).

Provides distributed tracing with:
- Jaeger integration for production
- Console exporter for development
- Automatic FastAPI instrumentation
- Custom span creation
"""

import logging
import os
import time
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    trace = None  # type: ignore
    TracerProvider = None  # type: ignore
    logger.warning(
        "OpenTelemetry not installed. Install with: pip install opentelemetry-api "
        "opentelemetry-sdk opentelemetry-instrumentation-fastapi"
    )


class TracingManager:
    """Manage OpenTelemetry tracing with Jaeger and console exporters."""

    def __init__(self, service_name: str = "lexecon", sample_rate: float = 1.0) -> None:
        """
        Initialize tracing manager.

        Args:
            service_name: Service name for tracing
            sample_rate: Sampling rate (0.0 to 1.0, default 1.0 = 100%)
        """
        self.enabled = False
        self.tracer: Optional[Any] = None
        self.service_name = service_name
        self.sample_rate = float(os.getenv("OTEL_SAMPLE_RATE", sample_rate))

        # Check if tracing is enabled
        tracing_enabled = os.getenv("TRACING_ENABLED", "false").lower() == "true"

        if TRACING_AVAILABLE and tracing_enabled:
            self._setup_tracing()
        elif not TRACING_AVAILABLE and tracing_enabled:
            logger.warning("Tracing enabled but OpenTelemetry not installed")
        else:
            logger.info("Distributed tracing is disabled (TRACING_ENABLED=false)")

    def _setup_tracing(self) -> None:
        """Set up OpenTelemetry tracing with Jaeger and console exporters."""
        if not TRACING_AVAILABLE:
            return

        try:
            # Create resource
            resource = Resource(attributes={"service.name": self.service_name})

            # Create tracer provider with sampling
            sampler = TraceIdRatioBased(self.sample_rate)
            provider = TracerProvider(resource=resource, sampler=sampler)

            # Add console exporter for development
            if os.getenv("LEXECON_ENV", "development") == "development":
                console_processor = BatchSpanProcessor(ConsoleSpanExporter())
                provider.add_span_processor(console_processor)
                logger.info("Console span exporter enabled (development mode)")

            # Add Jaeger exporter if configured
            jaeger_endpoint = os.getenv("JAEGER_ENDPOINT")
            if jaeger_endpoint:
                try:
                    from opentelemetry.exporter.jaeger.thrift import JaegerExporter

                    # Parse endpoint (e.g., "jaeger:6831" or "http://jaeger:14268/api/traces")
                    if "http" in jaeger_endpoint:
                        # HTTP endpoint
                        jaeger_exporter = JaegerExporter(collector_endpoint=jaeger_endpoint)
                    else:
                        # UDP agent endpoint
                        host, port = jaeger_endpoint.split(":")
                        jaeger_exporter = JaegerExporter(
                            agent_host_name=host, agent_port=int(port)
                        )

                    jaeger_processor = BatchSpanProcessor(jaeger_exporter)
                    provider.add_span_processor(jaeger_processor)
                    logger.info(f"Jaeger exporter enabled: {jaeger_endpoint}")

                except ImportError:
                    logger.warning(
                        "Jaeger exporter not installed. Install with: "
                        "pip install opentelemetry-exporter-jaeger"
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize Jaeger exporter: {e}")

            # Set global tracer provider
            trace.set_tracer_provider(provider)

            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            self.enabled = True

            logger.info(
                f"OpenTelemetry tracing initialized for {self.service_name} "
                f"(sample_rate={self.sample_rate})"
            )

        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
            self.enabled = False

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
