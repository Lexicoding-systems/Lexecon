"""Tests for structured logging functionality."""

import json
import logging
import os
import tempfile
from io import StringIO

import pytest

from lexecon.observability.logging import (
    LoggerAdapter,
    StructuredFormatter,
    configure_logging,
    get_logger,
    request_id_var,
    user_id_var,
)


class TestStructuredFormatter:
    """Tests for StructuredFormatter class."""

    def test_format_basic_log(self):
        """Test formatting a basic log record."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        # Should be valid JSON
        data = json.loads(output)
        assert data["message"] == "Test message"
        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["line"] == 42

    def test_format_includes_timestamp(self):
        """Test that formatted log includes timestamp."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "timestamp" in data
        # Should end with Z (UTC)
        assert data["timestamp"].endswith("Z")

    def test_format_with_request_context(self):
        """Test formatting includes request context from ContextVar."""
        formatter = StructuredFormatter()

        # Set context variables
        request_id_var.set("req_123")
        user_id_var.set("user_456")

        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test with context",
                args=(),
                exc_info=None,
            )

            output = formatter.format(record)
            data = json.loads(output)

            assert data["request_id"] == "req_123"
            assert data["user_id"] == "user_456"
        finally:
            # Clean up context
            request_id_var.set(None)
            user_id_var.set(None)

    def test_format_without_context(self):
        """Test formatting when context variables are not set."""
        formatter = StructuredFormatter()

        # Ensure context is clear
        request_id_var.set(None)
        user_id_var.set(None)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="No context",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "request_id" not in data
        assert "user_id" not in data

    def test_format_with_exception(self):
        """Test formatting log with exception info."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "Test error"
        assert "traceback" in data["exception"]

    def test_format_error_without_exception(self):
        """Test that errors without exc_info include stack trace."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error without exception",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "stack_trace" in data
        assert isinstance(data["stack_trace"], list)

    def test_format_warning_no_stack_trace(self):
        """Test that warnings don't include stack trace."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Warning message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "stack_trace" not in data
        assert "exception" not in data

    def test_format_with_extra_fields(self):
        """Test formatting with custom extra fields."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.extra_fields = {"custom_field": "custom_value", "count": 42}

        output = formatter.format(record)
        data = json.loads(output)

        assert data["custom_field"] == "custom_value"
        assert data["count"] == 42

    def test_format_includes_module_and_function(self):
        """Test that log includes module and function information."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/module.py",
            lineno=100,
            msg="Test",
            args=(),
            exc_info=None,
            func="test_function",
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["module"] == "module"
        assert data["function"] == "test_function"

    def test_format_different_log_levels(self):
        """Test formatting different log levels."""
        formatter = StructuredFormatter()

        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        for level_num, level_name in levels:
            record = logging.LogRecord(
                name="test",
                level=level_num,
                pathname="test.py",
                lineno=1,
                msg=f"{level_name} message",
                args=(),
                exc_info=None,
            )

            output = formatter.format(record)
            data = json.loads(output)

            assert data["level"] == level_name
            assert data["message"] == f"{level_name} message"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_with_json_format(self):
        """Test configuring logging with JSON format."""
        configure_logging(level="INFO", format="json", output="stdout")

        root = logging.getLogger()
        assert root.level == logging.INFO
        assert len(root.handlers) > 0

        # Check that handler has StructuredFormatter
        handler = root.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)

    def test_configure_with_text_format(self):
        """Test configuring logging with text format."""
        configure_logging(level="DEBUG", format="text", output="stdout")

        root = logging.getLogger()
        assert root.level == logging.DEBUG

        handler = root.handlers[0]
        assert isinstance(handler.formatter, logging.Formatter)
        assert not isinstance(handler.formatter, StructuredFormatter)

    def test_configure_different_log_levels(self):
        """Test configuring different log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        expected = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

        for level_str, level_expected in zip(levels, expected):
            configure_logging(level=level_str, format="json", output="stdout")
            root = logging.getLogger()
            assert root.level == level_expected

    def test_configure_removes_existing_handlers(self):
        """Test that configuration removes existing handlers."""
        root = logging.getLogger()

        # Add some handlers
        handler1 = logging.StreamHandler()
        handler2 = logging.StreamHandler()
        root.addHandler(handler1)
        root.addHandler(handler2)

        initial_count = len(root.handlers)
        assert initial_count >= 2

        # Reconfigure
        configure_logging(level="INFO", format="json", output="stdout")

        # Should have only 1 handler now
        assert len(root.handlers) == 1

    def test_configure_with_file_output(self):
        """Test configuring logging with file output."""
        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=".log")
        os.close(fd)

        try:
            configure_logging(level="INFO", format="json", output=temp_path)

            root = logging.getLogger()
            assert len(root.handlers) > 0

            # Check that handler is a FileHandler
            handler = root.handlers[0]
            assert isinstance(handler, logging.FileHandler)
            assert isinstance(handler.formatter, StructuredFormatter)
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_same_name_same_instance(self):
        """Test that getting logger with same name returns same instance."""
        logger1 = get_logger("shared_module")
        logger2 = get_logger("shared_module")

        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names create different loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1 is not logger2
        assert logger1.name == "module1"
        assert logger2.name == "module2"


class TestLoggerAdapter:
    """Tests for LoggerAdapter class."""

    def test_adapter_creation(self):
        """Test creating logger adapter."""
        base_logger = logging.getLogger("test")
        adapter = LoggerAdapter(base_logger, {})

        assert adapter.logger is base_logger

    def test_adapter_adds_context_vars(self):
        """Test that adapter adds context variables."""
        request_id_var.set("req_999")
        user_id_var.set("user_888")

        try:
            base_logger = logging.getLogger("test")
            adapter = LoggerAdapter(base_logger, {})

            _msg, kwargs = adapter.process("Test message", {})

            assert "extra" in kwargs
            assert kwargs["extra"]["request_id"] == "req_999"
            assert kwargs["extra"]["user_id"] == "user_888"
        finally:
            request_id_var.set(None)
            user_id_var.set(None)

    def test_adapter_without_context_vars(self):
        """Test adapter when context vars are not set."""
        request_id_var.set(None)
        user_id_var.set(None)

        base_logger = logging.getLogger("test")
        adapter = LoggerAdapter(base_logger, {})

        _msg, kwargs = adapter.process("Test message", {})

        assert "extra" in kwargs
        assert "request_id" not in kwargs["extra"]
        assert "user_id" not in kwargs["extra"]

    def test_adapter_preserves_existing_extra(self):
        """Test that adapter preserves existing extra fields."""
        request_id_var.set("req_777")

        try:
            base_logger = logging.getLogger("test")
            adapter = LoggerAdapter(base_logger, {})

            _msg, kwargs = adapter.process(
                "Test message", {"extra": {"custom": "field"}},
            )

            assert kwargs["extra"]["custom"] == "field"
            assert kwargs["extra"]["request_id"] == "req_777"
        finally:
            request_id_var.set(None)


class TestLoggingIntegration:
    """Integration tests for logging system."""

    def test_end_to_end_logging(self):
        """Test complete logging workflow."""
        # Configure logging
        stream = StringIO()
        configure_logging(level="INFO", format="json", output="stdout")

        # Get logger and log message
        logger = get_logger("integration_test")

        # Capture output
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Set context
        request_id_var.set("req_integration")

        try:
            logger.info("Integration test message", extra={"test_id": 123})

            output = stream.getvalue()
            data = json.loads(output)

            assert data["message"] == "Integration test message"
            assert data["level"] == "INFO"
            assert data["request_id"] == "req_integration"
            assert data["logger"] == "integration_test"
        finally:
            request_id_var.set(None)
            logger.removeHandler(handler)

    def test_logging_with_formatting(self):
        """Test logging with message formatting."""
        stream = StringIO()
        logger = logging.getLogger("format_test")
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("User %s logged in from %s", "alice", "192.168.1.1")

        output = stream.getvalue()
        data = json.loads(output)

        assert data["message"] == "User alice logged in from 192.168.1.1"
        logger.removeHandler(handler)

    def test_concurrent_context_isolation(self):
        """Test that context variables are properly isolated."""
        # This is a simplified test - in real concurrent scenarios,
        # ContextVar provides proper isolation per async task/thread

        request_id_var.set("req_first")
        assert request_id_var.get() == "req_first"

        request_id_var.set("req_second")
        assert request_id_var.get() == "req_second"

        request_id_var.set(None)
        assert request_id_var.get() is None


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_format_with_none_message(self):
        """Test formatting log with None message."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=None,
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["message"] == "None"

    def test_format_with_unicode_message(self):
        """Test formatting log with unicode characters."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Unicode test: 你好世界 🌍",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["message"] == "Unicode test: 你好世界 🌍"

    def test_format_with_very_long_message(self):
        """Test formatting very long log message."""
        formatter = StructuredFormatter()

        long_message = "A" * 10000
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=long_message,
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["message"] == long_message

    def test_configure_with_invalid_level(self):
        """Test configuring with invalid log level."""
        with pytest.raises(AttributeError):
            configure_logging(level="INVALID", format="json", output="stdout")

    def test_context_var_cleanup(self):
        """Test that context variables can be cleaned up."""
        request_id_var.set("test_req")
        user_id_var.set("test_user")

        request_id_var.set(None)
        user_id_var.set(None)

        assert request_id_var.get() is None
        assert user_id_var.get() is None

    def test_multiple_formatters_different_loggers(self):
        """Test using different formatters for different loggers."""
        logger1 = logging.getLogger("logger1")
        logger2 = logging.getLogger("logger2")

        stream1 = StringIO()
        stream2 = StringIO()

        handler1 = logging.StreamHandler(stream1)
        handler1.setFormatter(StructuredFormatter())

        handler2 = logging.StreamHandler(stream2)
        handler2.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

        logger1.addHandler(handler1)
        logger2.addHandler(handler2)

        logger1.setLevel(logging.INFO)
        logger2.setLevel(logging.INFO)

        logger1.info("JSON log")
        logger2.info("Text log")

        # Logger1 should have JSON
        output1 = stream1.getvalue()
        data1 = json.loads(output1)
        assert data1["message"] == "JSON log"

        # Logger2 should have text
        output2 = stream2.getvalue()
        assert "INFO: Text log" in output2

        logger1.removeHandler(handler1)
        logger2.removeHandler(handler2)
