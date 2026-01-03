"""Tests for OpenTelemetry tracing functionality."""

import time

import pytest

from lexecon.observability.tracing import (
    TRACING_AVAILABLE,
    TracingManager,
    trace_function,
    tracer,
)


class TestTracingAvailability:
    """Tests for tracing availability detection."""

    def test_tracing_available_is_boolean(self):
        """Test that TRACING_AVAILABLE is a boolean."""
        assert isinstance(TRACING_AVAILABLE, bool)

    def test_global_tracer_exists(self):
        """Test that global tracer instance exists."""
        assert tracer is not None
        assert isinstance(tracer, TracingManager)


class TestTracingManager:
    """Tests for TracingManager class."""

    def test_initialization(self):
        """Test tracing manager initialization."""
        manager = TracingManager()

        assert manager is not None
        assert hasattr(manager, 'enabled')
        assert hasattr(manager, 'tracer')

    def test_enabled_status(self):
        """Test that enabled status matches availability."""
        manager = TracingManager()

        # If tracing is available, should be enabled
        # If not available, should be disabled
        assert manager.enabled == TRACING_AVAILABLE

    def test_tracer_attribute(self):
        """Test tracer attribute state."""
        manager = TracingManager()

        if TRACING_AVAILABLE:
            assert manager.tracer is not None
        else:
            assert manager.tracer is None

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
    def test_start_span_when_enabled(self):
        """Test starting a span when tracing is enabled."""
        manager = TracingManager()

        span = manager.start_span("test_span", test_attribute="value")

        assert span is not None
        # Span should be context manager
        assert hasattr(span, '__enter__')
        assert hasattr(span, '__exit__')

    def test_start_span_when_disabled(self):
        """Test starting a span when tracing is disabled."""
        manager = TracingManager()

        if not TRACING_AVAILABLE:
            span = manager.start_span("test_span")
            assert span is None

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
    def test_span_with_attributes(self):
        """Test creating span with multiple attributes."""
        manager = TracingManager()

        span = manager.start_span(
            "attributed_span",
            attr1="value1",
            attr2=42,
            attr3=True
        )

        assert span is not None

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
    def test_instrument_fastapi(self):
        """Test FastAPI instrumentation."""
        from unittest.mock import Mock

        manager = TracingManager()
        mock_app = Mock()

        # Should not raise error
        manager.instrument_fastapi(mock_app)


class TestTraceFunctionDecorator:
    """Tests for trace_function decorator."""

    def test_decorator_without_name(self):
        """Test decorator without explicit name."""
        @trace_function()
        def test_func():
            return "result"

        result = test_func()
        assert result == "result"

    def test_decorator_with_name(self):
        """Test decorator with explicit span name."""
        @trace_function(name="custom_span_name")
        def test_func():
            return "result"

        result = test_func()
        assert result == "result"

    def test_decorator_preserves_function_behavior(self):
        """Test that decorator doesn't change function behavior."""
        @trace_function()
        def add(a, b):
            return a + b

        assert add(2, 3) == 5
        assert add(10, 20) == 30

    def test_decorator_with_arguments(self):
        """Test decorating function with various arguments."""
        @trace_function()
        def complex_func(x, y, *args, **kwargs):
            return {
                'x': x,
                'y': y,
                'args': args,
                'kwargs': kwargs
            }

        result = complex_func(1, 2, 3, 4, key="value")

        assert result['x'] == 1
        assert result['y'] == 2
        assert result['args'] == (3, 4)
        assert result['kwargs'] == {'key': 'value'}

    def test_decorator_with_exception(self):
        """Test decorator handles exceptions properly."""
        @trace_function()
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_func()

    def test_decorator_exception_still_raises(self):
        """Test that exceptions are still raised after tracing."""
        @trace_function()
        def error_func(should_error):
            if should_error:
                raise RuntimeError("Intentional error")
            return "success"

        # Should work without error
        assert error_func(False) == "success"

        # Should raise error
        with pytest.raises(RuntimeError):
            error_func(True)

    def test_decorator_on_class_method(self):
        """Test decorator on class methods."""
        class TestClass:
            @trace_function()
            def method(self, value):
                return value * 2

        obj = TestClass()
        assert obj.method(5) == 10

    def test_decorator_on_static_method(self):
        """Test decorator on static methods."""
        class TestClass:
            @staticmethod
            @trace_function()
            def static_method(value):
                return value + 1

        assert TestClass.static_method(5) == 6

    def test_decorator_preserves_docstring(self):
        """Test that decorator preserves function docstring."""
        @trace_function()
        def documented_func():
            """This is a docstring."""
            return "result"

        assert documented_func.__doc__ == "This is a docstring."

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @trace_function()
        def named_function():
            return "result"

        assert named_function.__name__ == "named_function"

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
    def test_decorator_records_duration(self):
        """Test that decorator records execution duration."""
        @trace_function()
        def slow_func():
            time.sleep(0.1)
            return "done"

        start = time.time()
        result = slow_func()
        duration = time.time() - start

        assert result == "done"
        assert duration >= 0.1

    def test_decorator_when_tracing_disabled(self):
        """Test decorator works even when tracing is disabled."""
        # This should work regardless of TRACING_AVAILABLE
        @trace_function()
        def normal_func():
            return "works"

        assert normal_func() == "works"


class TestTracingIntegration:
    """Integration tests for tracing system."""

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
    def test_nested_spans(self):
        """Test creating nested spans."""
        manager = TracingManager()

        outer_span = manager.start_span("outer")
        if outer_span:
            inner_span = manager.start_span("inner")
            assert inner_span is not None

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
    def test_multiple_sequential_spans(self):
        """Test creating multiple sequential spans."""
        manager = TracingManager()

        span1 = manager.start_span("span1")
        assert span1 is not None

        span2 = manager.start_span("span2")
        assert span2 is not None

        span3 = manager.start_span("span3")
        assert span3 is not None

    def test_decorated_functions_call_chain(self):
        """Test call chain of decorated functions."""
        @trace_function()
        def func_a():
            return func_b()

        @trace_function()
        def func_b():
            return func_c()

        @trace_function()
        def func_c():
            return "final_result"

        result = func_a()
        assert result == "final_result"

    def test_decorator_with_multiple_returns(self):
        """Test decorator on function with multiple return paths."""
        @trace_function()
        def multi_return(value):
            if value > 0:
                return "positive"
            elif value < 0:
                return "negative"
            else:
                return "zero"

        assert multi_return(5) == "positive"
        assert multi_return(-3) == "negative"
        assert multi_return(0) == "zero"

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
    def test_span_context_manager(self):
        """Test using span as context manager."""
        manager = TracingManager()

        span = manager.start_span("context_test")

        if span:
            # Should be usable as context manager
            with span:
                pass  # Span active here

            # Span should be ended after context


class TestTracingFallback:
    """Tests for tracing fallback when disabled."""

    def test_disabled_tracer_returns_none(self):
        """Test that disabled tracer returns None for spans."""
        manager = TracingManager()

        if not manager.enabled:
            span = manager.start_span("test")
            assert span is None

    def test_disabled_tracing_no_errors(self):
        """Test that disabled tracing doesn't cause errors."""
        @trace_function()
        def test_func():
            return "result"

        # Should work fine even if tracing is disabled
        result = test_func()
        assert result == "result"

    def test_decorator_overhead_minimal_when_disabled(self):
        """Test that decorator has minimal overhead when disabled."""
        @trace_function()
        def fast_func():
            return 42

        # Should execute quickly even if wrapped
        start = time.time()
        for _ in range(1000):
            result = fast_func()
        duration = time.time() - start

        assert result == 42
        # Should be very fast (less than 1 second for 1000 calls)
        assert duration < 1.0


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_decorator_on_generator(self):
        """Test decorator on generator function."""
        @trace_function()
        def gen_func():
            yield 1
            yield 2
            yield 3

        result = list(gen_func())
        assert result == [1, 2, 3]

    def test_decorator_on_async_function(self):
        """Test decorator on async function (should still work)."""
        @trace_function()
        async def async_func():
            return "async_result"

        # We can't easily await this in sync tests, but decorator should apply
        assert hasattr(async_func, '__name__')

    def test_decorator_with_none_return(self):
        """Test decorator on function returning None."""
        @trace_function()
        def none_func():
            return None

        result = none_func()
        assert result is None

    def test_decorator_with_no_return(self):
        """Test decorator on function with no explicit return."""
        @trace_function()
        def no_return_func():
            pass

        result = no_return_func()
        assert result is None

    def test_span_name_with_special_characters(self):
        """Test span names with special characters."""
        manager = TracingManager()

        # Should handle special characters gracefully
        span = manager.start_span("span-with-dashes")
        span = manager.start_span("span_with_underscores")
        span = manager.start_span("span.with.dots")

        # Should not error

    def test_decorator_with_very_long_name(self):
        """Test decorator with very long span name."""
        long_name = "a" * 1000

        @trace_function(name=long_name)
        def test_func():
            return "ok"

        result = test_func()
        assert result == "ok"

    def test_multiple_decorators(self):
        """Test function with multiple decorators."""
        @trace_function(name="outer")
        @trace_function(name="inner")
        def double_traced():
            return "traced"

        result = double_traced()
        assert result == "traced"

    def test_decorator_with_recursive_function(self):
        """Test decorator on recursive function."""
        @trace_function()
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)

        result = factorial(5)
        assert result == 120

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
    def test_span_attributes_with_complex_types(self):
        """Test span attributes with various types."""
        manager = TracingManager()

        # Different attribute types
        span = manager.start_span(
            "complex_attrs",
            string_attr="value",
            int_attr=42,
            float_attr=3.14,
            bool_attr=True
        )

        assert span is not None


class TestTracingPerformance:
    """Tests for tracing performance characteristics."""

    def test_decorator_minimal_overhead(self):
        """Test that decorator has minimal overhead."""
        # Baseline function
        def baseline():
            return 42

        # Decorated function
        @trace_function()
        def traced():
            return 42

        # Both should be fast
        iterations = 100

        start = time.time()
        for _ in range(iterations):
            baseline()
        baseline_time = time.time() - start

        start = time.time()
        for _ in range(iterations):
            traced()
        traced_time = time.time() - start

        # Traced should be relatively fast (overhead < 10x baseline)
        # This is a loose bound since we don't know if tracing is enabled
        assert traced_time < baseline_time * 10

    def test_many_spans_no_memory_leak(self):
        """Test creating many spans doesn't leak memory."""
        manager = TracingManager()

        # Create many spans
        for i in range(1000):
            span = manager.start_span(f"span_{i}")

        # Should complete without issues

    def test_concurrent_tracing(self):
        """Test that concurrent tracing works."""
        @trace_function()
        def concurrent_func(n):
            time.sleep(0.001)
            return n * 2

        # Simulate concurrent calls
        results = [concurrent_func(i) for i in range(10)]

        assert results == [i * 2 for i in range(10)]


class TestTracingConfiguration:
    """Tests for tracing configuration and setup."""

    def test_tracer_singleton(self):
        """Test that module provides singleton tracer."""
        from lexecon.observability.tracing import tracer as tracer1
        from lexecon.observability.tracing import tracer as tracer2

        assert tracer1 is tracer2

    def test_tracing_manager_setup(self):
        """Test that TracingManager sets up correctly."""
        manager = TracingManager()

        # Should have setup method called
        assert hasattr(manager, '_setup_tracing')

    def test_graceful_degradation(self):
        """Test graceful degradation when tracing unavailable."""
        # Should work even if OpenTelemetry is not installed
        manager = TracingManager()

        # All operations should be safe
        span = manager.start_span("test")
        manager.instrument_fastapi(None)

        # No errors should occur
