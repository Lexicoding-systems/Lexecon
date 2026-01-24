"""Circuit breaker pattern implementation with observability.

Provides resilient service calls with:
- Automatic failure detection and circuit opening
- Half-open state for recovery testing
- Full metrics integration
- Fallback support
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from .metrics_v2 import CircuitState, metrics

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, service: str, state: CircuitState, message: str = "") -> None:
        self.service = service
        self.state = state
        super().__init__(message or f"Circuit breaker for {service} is {state.value}")


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    # Number of failures before opening circuit
    failure_threshold: int = 5

    # Number of successes in half-open to close circuit
    success_threshold: int = 3

    # Time in seconds before attempting recovery (half-open)
    recovery_timeout: float = 30.0

    # Time window for counting failures
    failure_window: float = 60.0

    # Exceptions that should trigger circuit breaker
    # If empty, all exceptions trigger it
    trigger_exceptions: tuple = ()

    # Exceptions that should NOT trigger circuit breaker
    exclude_exceptions: tuple = ()

    # Maximum number of requests allowed in half-open state
    half_open_max_requests: int = 3


@dataclass
class CircuitBreakerState:
    """Internal state of circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_state_change: float = field(default_factory=time.time)
    half_open_requests: int = 0
    failure_timestamps: list = field(default_factory=list)


class CircuitBreaker(Generic[T]):
    """Circuit breaker for protecting service calls.

    Usage:
        cb = CircuitBreaker("redis", config=CircuitBreakerConfig(failure_threshold=3))

        @cb.protect
        def call_redis():
            return redis.get("key")

        # Or with fallback
        @cb.protect_with_fallback(lambda: "default")
        def call_redis():
            return redis.get("key")

        # Manual usage
        try:
            result = cb.call(lambda: redis.get("key"))
        except CircuitBreakerError:
            result = "fallback"
    """

    def __init__(
        self,
        service_name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            service_name: Name of the protected service
            config: Circuit breaker configuration
        """
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitBreakerState()
        self._lock = Lock()

        # Initialize metrics
        metrics.record_circuit_state_change(
            service_name,
            CircuitState.CLOSED,
            CircuitState.CLOSED,
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state.state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN

    def _should_trigger(self, exception: Exception) -> bool:
        """Check if exception should trigger circuit breaker.

        Args:
            exception: Exception to check

        Returns:
            True if exception should trigger circuit breaker
        """
        # Check exclusions first
        if self.config.exclude_exceptions:
            for exc_type in self.config.exclude_exceptions:
                if isinstance(exception, exc_type):
                    return False

        # Check triggers if specified
        if self.config.trigger_exceptions:
            for exc_type in self.config.trigger_exceptions:
                if isinstance(exception, exc_type):
                    return True
            return False

        # Default: all exceptions trigger
        return True

    def _clean_failure_window(self) -> None:
        """Remove failures outside the time window."""
        cutoff = time.time() - self.config.failure_window
        self._state.failure_timestamps = [
            t for t in self._state.failure_timestamps if t > cutoff
        ]

    def _record_failure(self, exception: Exception) -> None:
        """Record a failure and potentially open circuit.

        Args:
            exception: The exception that occurred
        """
        if not self._should_trigger(exception):
            return

        with self._lock:
            now = time.time()
            self._state.failure_timestamps.append(now)
            self._state.last_failure_time = now
            self._clean_failure_window()

            failure_count = len(self._state.failure_timestamps)
            self._state.failure_count = failure_count

            # Record metric
            metrics.record_circuit_request(self.service_name, "failure")

            if self._state.state == CircuitState.CLOSED:
                if failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

            elif self._state.state == CircuitState.HALF_OPEN:
                # Any failure in half-open immediately opens circuit
                self._transition_to(CircuitState.OPEN)

    def _record_success(self) -> None:
        """Record a success and potentially close circuit."""
        with self._lock:
            self._state.success_count += 1

            # Record metric
            metrics.record_circuit_request(self.service_name, "success")

            if self._state.state == CircuitState.HALF_OPEN:
                if self._state.success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state.

        Args:
            new_state: Target state
        """
        old_state = self._state.state

        if old_state == new_state:
            return

        logger.info(
            f"Circuit breaker [{self.service_name}] transitioning from "
            f"{old_state.value} to {new_state.value}",
        )

        # Record state change metric
        metrics.record_circuit_state_change(self.service_name, old_state, new_state)

        # Update state
        self._state.state = new_state
        self._state.last_state_change = time.time()

        # Reset counters based on new state
        if new_state == CircuitState.CLOSED:
            self._state.failure_count = 0
            self._state.success_count = 0
            self._state.failure_timestamps = []

        elif new_state == CircuitState.HALF_OPEN:
            self._state.success_count = 0
            self._state.half_open_requests = 0

        elif new_state == CircuitState.OPEN:
            self._state.success_count = 0

    def _check_state(self) -> None:
        """Check and potentially update circuit state."""
        with self._lock:
            if self._state.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                elapsed = time.time() - self._state.last_state_change
                if elapsed >= self.config.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)

    def _can_execute(self) -> bool:
        """Check if a call can be executed.

        Returns:
            True if call is allowed
        """
        self._check_state()

        with self._lock:
            if self._state.state == CircuitState.CLOSED:
                return True

            if self._state.state == CircuitState.OPEN:
                return False

            if self._state.state == CircuitState.HALF_OPEN:
                # Limit requests in half-open state
                if self._state.half_open_requests >= self.config.half_open_max_requests:
                    return False
                self._state.half_open_requests += 1
                return True

            return False

    def call(
        self,
        func: Callable[[], T],
        fallback: Optional[Callable[[], T]] = None,
    ) -> T:
        """Execute a function with circuit breaker protection.

        Args:
            func: Function to execute
            fallback: Optional fallback function if circuit is open

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open and no fallback
        """
        if not self._can_execute():
            metrics.record_circuit_request(self.service_name, "rejected")

            if fallback:
                logger.debug(
                    f"Circuit [{self.service_name}] is open, using fallback",
                )
                return fallback()

            raise CircuitBreakerError(self.service_name, self._state.state)

        try:
            result = func()
            self._record_success()
            return result

        except Exception as e:
            self._record_failure(e)
            raise

    async def call_async(
        self,
        func: Callable[[], Any],
        fallback: Optional[Callable[[], Any]] = None,
    ) -> Any:
        """Execute an async function with circuit breaker protection.

        Args:
            func: Async function to execute
            fallback: Optional fallback function

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open and no fallback
        """
        if not self._can_execute():
            metrics.record_circuit_request(self.service_name, "rejected")

            if fallback:
                logger.debug(
                    f"Circuit [{self.service_name}] is open, using fallback",
                )
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback()
                return fallback()

            raise CircuitBreakerError(self.service_name, self._state.state)

        try:
            result = await func()
            self._record_success()
            return result

        except Exception as e:
            self._record_failure(e)
            raise

    def protect(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to protect a function with circuit breaker.

        Args:
            func: Function to protect

        Returns:
            Protected function
        """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return self.call(lambda: func(*args, **kwargs))

        return wrapper

    def protect_async(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to protect an async function with circuit breaker.

        Args:
            func: Async function to protect

        Returns:
            Protected async function
        """
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await self.call_async(lambda: func(*args, **kwargs))

        return wrapper

    def protect_with_fallback(
        self,
        fallback: Callable[[], T],
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator to protect with fallback on circuit open.

        Args:
            fallback: Fallback function to call when circuit is open

        Returns:
            Decorator function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                return self.call(lambda: func(*args, **kwargs), fallback)

            return wrapper

        return decorator

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status.

        Returns:
            Status dictionary
        """
        with self._lock:
            return {
                "service": self.service_name,
                "state": self._state.state.value,
                "failure_count": self._state.failure_count,
                "success_count": self._state.success_count,
                "last_failure_time": self._state.last_failure_time,
                "last_state_change": self._state.last_state_change,
                "time_in_state": time.time() - self._state.last_state_change,
            }

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self) -> None:
        """Initialize registry."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def get_or_create(
        self,
        service_name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker for a service.

        Args:
            service_name: Service name
            config: Optional configuration

        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if service_name not in self._breakers:
                self._breakers[service_name] = CircuitBreaker(service_name, config)
            return self._breakers[service_name]

    def get(self, service_name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name.

        Args:
            service_name: Service name

        Returns:
            CircuitBreaker or None
        """
        with self._lock:
            return self._breakers.get(service_name)

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers.

        Returns:
            Dict mapping service names to status
        """
        with self._lock:
            return {
                name: cb.get_status()
                for name, cb in self._breakers.items()
            }

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for cb in self._breakers.values():
                cb.reset()


# Global registry
circuit_breakers = CircuitBreakerRegistry()


def get_circuit_breaker(
    service_name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """Get or create a circuit breaker.

    Args:
        service_name: Service name
        config: Optional configuration

    Returns:
        CircuitBreaker instance
    """
    return circuit_breakers.get_or_create(service_name, config)
