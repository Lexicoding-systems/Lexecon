"""Error correlation and telemetry for Lexecon.

This module provides unified error tracking across:
- Logs (structured error logging)
- Traces (span error recording)
- Metrics (error counters and rates)

It enables debugging production issues by correlating errors
with their trace context and system state.
"""

import logging
import time
import traceback
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Callable, Deque, Dict, List, Optional, Type

from .context import ObservabilityContext, get_current_context

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels for classification."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification and routing."""

    # Infrastructure errors
    DATABASE = "database"
    CACHE = "cache"
    NETWORK = "network"
    FILESYSTEM = "filesystem"

    # Application errors
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"

    # External service errors
    EXTERNAL_API = "external_api"
    TIMEOUT = "timeout"

    # System errors
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONFIGURATION = "configuration"

    # Unknown
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Structured error record with full context."""

    # Error identification
    error_id: str
    timestamp: datetime
    error_type: str
    message: str

    # Classification
    severity: ErrorSeverity
    category: ErrorCategory

    # Context correlation
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    operation: Optional[str] = None

    # Error details
    stack_trace: Optional[str] = None
    cause: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    # System state at error time
    service_name: str = "lexecon"
    hostname: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "operation": self.operation,
            "stack_trace": self.stack_trace,
            "cause": self.cause,
            "attributes": self.attributes,
            "service_name": self.service_name,
            "hostname": self.hostname,
        }


class ErrorClassifier:
    """Classifies exceptions into categories and severities."""

    # Default exception to category mapping
    DEFAULT_MAPPINGS: Dict[Type[Exception], ErrorCategory] = {
        # Database errors
        ConnectionError: ErrorCategory.DATABASE,
        # Network errors
        TimeoutError: ErrorCategory.TIMEOUT,
        OSError: ErrorCategory.NETWORK,
        # Validation errors
        ValueError: ErrorCategory.VALIDATION,
        TypeError: ErrorCategory.VALIDATION,
        KeyError: ErrorCategory.VALIDATION,
        # Auth errors
        PermissionError: ErrorCategory.AUTHORIZATION,
    }

    # Exception patterns for string matching
    PATTERN_MAPPINGS: Dict[str, ErrorCategory] = {
        "connection": ErrorCategory.DATABASE,
        "timeout": ErrorCategory.TIMEOUT,
        "redis": ErrorCategory.CACHE,
        "sql": ErrorCategory.DATABASE,
        "postgres": ErrorCategory.DATABASE,
        "sqlite": ErrorCategory.DATABASE,
        "authentication": ErrorCategory.AUTHENTICATION,
        "authorization": ErrorCategory.AUTHORIZATION,
        "permission": ErrorCategory.AUTHORIZATION,
        "forbidden": ErrorCategory.AUTHORIZATION,
        "unauthorized": ErrorCategory.AUTHENTICATION,
        "validation": ErrorCategory.VALIDATION,
        "invalid": ErrorCategory.VALIDATION,
    }

    def __init__(self) -> None:
        """Initialize classifier with default mappings."""
        self._custom_mappings: Dict[Type[Exception], ErrorCategory] = {}
        self._custom_severities: Dict[Type[Exception], ErrorSeverity] = {}

    def register_mapping(
        self,
        exception_type: Type[Exception],
        category: ErrorCategory,
        severity: Optional[ErrorSeverity] = None,
    ) -> None:
        """Register custom exception mapping.

        Args:
            exception_type: Exception class to map
            category: Error category
            severity: Optional severity override
        """
        self._custom_mappings[exception_type] = category
        if severity:
            self._custom_severities[exception_type] = severity

    def classify(self, exception: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classify an exception into category and severity.

        Args:
            exception: Exception to classify

        Returns:
            Tuple of (category, severity)
        """
        exc_type = type(exception)

        # Check custom mappings first
        if exc_type in self._custom_mappings:
            category = self._custom_mappings[exc_type]
            severity = self._custom_severities.get(exc_type, ErrorSeverity.ERROR)
            return category, severity

        # Check default mappings
        for mapped_type, category in self.DEFAULT_MAPPINGS.items():
            if isinstance(exception, mapped_type):
                return category, ErrorSeverity.ERROR

        # Pattern matching on exception message
        message = str(exception).lower()
        for pattern, category in self.PATTERN_MAPPINGS.items():
            if pattern in message:
                return category, ErrorSeverity.ERROR

        # Default
        return ErrorCategory.UNKNOWN, ErrorSeverity.ERROR


class ErrorCorrelator:
    """Correlates and tracks errors across the system.

    Provides:
    - Error rate tracking
    - Recent error history
    - Error pattern detection
    - Integration with logs, traces, and metrics
    """

    def __init__(
        self,
        max_history: int = 1000,
        error_window_seconds: int = 60,
    ) -> None:
        """Initialize error correlator.

        Args:
            max_history: Maximum number of recent errors to retain
            error_window_seconds: Time window for error rate calculation
        """
        self._classifier = ErrorClassifier()
        self._history: Deque[ErrorRecord] = deque(maxlen=max_history)
        self._lock = Lock()
        self._error_window = error_window_seconds

        # Callbacks for error notifications
        self._callbacks: List[Callable[[ErrorRecord], None]] = []

        # Error counters by category (for rate limiting)
        self._error_counts: Dict[str, List[float]] = {}

        # Import hostname
        import socket
        self._hostname = socket.gethostname()

    def register_callback(self, callback: Callable[[ErrorRecord], None]) -> None:
        """Register callback to be notified of errors.

        Args:
            callback: Function to call with ErrorRecord
        """
        self._callbacks.append(callback)

    def record_error(
        self,
        exception: Exception,
        context: Optional[ObservabilityContext] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        **attributes: Any,
    ) -> ErrorRecord:
        """Record an error with full context correlation.

        Args:
            exception: Exception to record
            context: Optional observability context (uses current if not provided)
            severity: Optional severity override
            category: Optional category override
            **attributes: Additional error attributes

        Returns:
            ErrorRecord with full context
        """
        import secrets

        # Get context
        ctx = context or get_current_context()

        # Classify error
        auto_category, auto_severity = self._classifier.classify(exception)
        final_category = category or auto_category
        final_severity = severity or auto_severity

        # Extract cause if chained exception
        cause = None
        if exception.__cause__:
            cause = f"{type(exception.__cause__).__name__}: {exception.__cause__}"

        # Create error record
        record = ErrorRecord(
            error_id=f"err_{secrets.token_hex(8)}",
            timestamp=datetime.now(timezone.utc),
            error_type=type(exception).__name__,
            message=str(exception),
            severity=final_severity,
            category=final_category,
            trace_id=ctx.trace_id if ctx else None,
            span_id=ctx.span_id if ctx else None,
            request_id=ctx.request_id if ctx else None,
            user_id=ctx.user_id if ctx else None,
            operation=ctx.operation_name if ctx else None,
            stack_trace=traceback.format_exc(),
            cause=cause,
            attributes=attributes,
            hostname=self._hostname,
        )

        # Store in history
        with self._lock:
            self._history.append(record)
            self._update_error_counts(final_category.value)

        # Log the error with correlation context
        self._log_error(record)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(record)
            except Exception as e:
                logger.warning(f"Error callback failed: {e}")

        return record

    def _update_error_counts(self, category: str) -> None:
        """Update error counts for rate tracking.

        Args:
            category: Error category
        """
        now = time.time()
        cutoff = now - self._error_window

        if category not in self._error_counts:
            self._error_counts[category] = []

        # Remove old entries
        self._error_counts[category] = [
            t for t in self._error_counts[category] if t > cutoff
        ]

        # Add new entry
        self._error_counts[category].append(now)

    def _log_error(self, record: ErrorRecord) -> None:
        """Log error with structured context.

        Args:
            record: ErrorRecord to log
        """
        log_level = {
            ErrorSeverity.DEBUG: logging.DEBUG,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(record.severity, logging.ERROR)

        extra = {
            "error_id": record.error_id,
            "error_type": record.error_type,
            "category": record.category.value,
            "trace_id": record.trace_id,
            "span_id": record.span_id,
            "request_id": record.request_id,
            "operation": record.operation,
        }

        logger.log(
            log_level,
            f"[{record.category.value.upper()}] {record.error_type}: {record.message}",
            extra={"extra_fields": extra},
            exc_info=False,  # Stack trace already in record
        )

    def get_error_rate(self, category: Optional[ErrorCategory] = None) -> float:
        """Get error rate per second for category.

        Args:
            category: Optional category filter

        Returns:
            Errors per second in the time window
        """
        with self._lock:
            if category:
                counts = self._error_counts.get(category.value, [])
            else:
                counts = []
                for cat_counts in self._error_counts.values():
                    counts.extend(cat_counts)

            if not counts:
                return 0.0

            return len(counts) / self._error_window

    def get_recent_errors(
        self,
        limit: int = 100,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
    ) -> List[ErrorRecord]:
        """Get recent error records.

        Args:
            limit: Maximum number of records to return
            category: Optional category filter
            severity: Optional severity filter

        Returns:
            List of ErrorRecords
        """
        with self._lock:
            records = list(self._history)

        # Apply filters
        if category:
            records = [r for r in records if r.category == category]
        if severity:
            records = [r for r in records if r.severity == severity]

        # Return most recent
        return records[-limit:]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors.

        Returns:
            Summary dict with counts by category and severity
        """
        with self._lock:
            records = list(self._history)

        by_category: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}

        for record in records:
            cat = record.category.value
            sev = record.severity.value

            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "total": len(records),
            "by_category": by_category,
            "by_severity": by_severity,
            "error_rate": self.get_error_rate(),
        }


# Global error correlator instance
error_correlator = ErrorCorrelator()


def record_error(
    exception: Exception,
    **kwargs: Any,
) -> ErrorRecord:
    """Record an error with context correlation.

    Args:
        exception: Exception to record
        **kwargs: Additional attributes

    Returns:
        ErrorRecord
    """
    return error_correlator.record_error(exception, **kwargs)


def error_boundary(
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None,
    reraise: bool = True,
) -> Callable:
    """Decorator to create an error boundary with automatic recording.

    Args:
        category: Error category for this boundary
        severity: Error severity for this boundary
        reraise: Whether to re-raise the exception

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                record_error(
                    e,
                    category=category,
                    severity=severity,
                    function=func.__name__,
                    module=func.__module__,
                )
                if reraise:
                    raise

        return wrapper

    return decorator


async def async_error_boundary(
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None,
    reraise: bool = True,
) -> Callable:
    """Async decorator to create an error boundary.

    Args:
        category: Error category
        severity: Error severity
        reraise: Whether to re-raise

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                record_error(
                    e,
                    category=category,
                    severity=severity,
                    function=func.__name__,
                    module=func.__module__,
                )
                if reraise:
                    raise

        return wrapper

    return decorator
