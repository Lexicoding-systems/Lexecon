"""Structured logging configuration for Lexecon."""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
import traceback
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add stack trace for errors
        if record.levelno >= logging.ERROR and not record.exc_info:
            log_data["stack_trace"] = traceback.format_stack()

        return json.dumps(log_data)


def configure_logging(
    level: str = "INFO",
    format: str = "json",  # noqa: A002
    output: str = "stdout",
) -> None:
    """Configure logging for Lexecon.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log format (json, text)
        output: Output destination (stdout, file)
    """
    log_level = getattr(logging, level.upper())

    # Remove existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Create handler
    if output == "stdout":
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(output)

    # Set formatter
    if format == "json":
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter with extra fields support."""

    def process(
        self, msg: str, kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """Process log message with extra fields."""
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        # Add context from ContextVars
        request_id = request_id_var.get()
        if request_id:
            kwargs["extra"]["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            kwargs["extra"]["user_id"] = user_id

        return msg, kwargs
