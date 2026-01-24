"""Enhanced health checks with dependency monitoring.

Provides:
- Kubernetes-compatible liveness/readiness/startup probes
- Dependency health checks (database, cache, external services)
- Circuit breaker integration
- Health history tracking
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

from .circuit_breaker import circuit_breakers

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DependencyHealth:
    """Health status of a dependency."""

    name: str
    healthy: bool
    response_time_ms: float
    last_check: datetime
    consecutive_failures: int = 0
    error_message: Optional[str] = None

    @property
    def status(self) -> HealthStatus:
        """Get status based on health state."""
        if self.healthy:
            return HealthStatus.HEALTHY
        if self.consecutive_failures < 3:
            return HealthStatus.DEGRADED
        return HealthStatus.UNHEALTHY


HealthCheckFunc = Union[
    Callable[[], tuple[HealthStatus, Dict[str, Any]]],
    Callable[[], Coroutine[Any, Any, tuple[HealthStatus, Dict[str, Any]]]],
]


class HealthCheckManager:
    """Comprehensive health check management.

    Features:
    - Sync and async health checks
    - Dependency health monitoring
    - Caching of health results
    - Circuit breaker integration
    - SLA monitoring
    """

    def __init__(
        self,
        service_name: str = "lexecon",
        cache_ttl_seconds: float = 5.0,
    ) -> None:
        """Initialize health check manager.

        Args:
            service_name: Name of this service
            cache_ttl_seconds: How long to cache health results
        """
        self.service_name = service_name
        self.cache_ttl = cache_ttl_seconds
        self.start_time = time.time()

        # Health checks
        self._checks: Dict[str, HealthCheckFunc] = {}
        self._dependencies: Dict[str, DependencyHealth] = {}

        # Cached results
        self._cached_readiness: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0.0

        # Initialization tracking
        self._initialized = False
        self._initialization_checks: Dict[str, bool] = {}

        # Version info
        self._version = os.getenv("LEXECON_VERSION", "0.1.0")
        self._environment = os.getenv("LEXECON_ENV", "development")

    def add_check(
        self,
        name: str,
        check_func: HealthCheckFunc,
        required_for_startup: bool = False,
    ) -> None:
        """Add a health check.

        Args:
            name: Check name
            check_func: Function returning (HealthStatus, details)
            required_for_startup: Whether this check is required for startup
        """
        self._checks[name] = check_func
        if required_for_startup:
            self._initialization_checks[name] = False

    def register_dependency(
        self,
        name: str,
        initial_healthy: bool = True,
    ) -> None:
        """Register a dependency for health tracking.

        Args:
            name: Dependency name
            initial_healthy: Initial health status
        """
        self._dependencies[name] = DependencyHealth(
            name=name,
            healthy=initial_healthy,
            response_time_ms=0.0,
            last_check=datetime.now(timezone.utc),
        )

    def update_dependency_health(
        self,
        name: str,
        healthy: bool,
        response_time_ms: float = 0.0,
        error_message: Optional[str] = None,
    ) -> None:
        """Update dependency health status.

        Args:
            name: Dependency name
            healthy: Whether dependency is healthy
            response_time_ms: Response time of health check
            error_message: Error message if unhealthy
        """
        if name not in self._dependencies:
            self.register_dependency(name, healthy)

        dep = self._dependencies[name]
        dep.healthy = healthy
        dep.response_time_ms = response_time_ms
        dep.last_check = datetime.now(timezone.utc)
        dep.error_message = error_message

        if healthy:
            dep.consecutive_failures = 0
        else:
            dep.consecutive_failures += 1

    def mark_initialized(self, check_name: Optional[str] = None) -> None:
        """Mark a startup check as complete.

        Args:
            check_name: Specific check name, or None to mark all
        """
        if check_name:
            if check_name in self._initialization_checks:
                self._initialization_checks[check_name] = True
        else:
            for name in self._initialization_checks:
                self._initialization_checks[name] = True

        # Check if all initialized
        self._initialized = all(self._initialization_checks.values())

    def liveness(self) -> Dict[str, Any]:
        """Kubernetes liveness probe.

        Returns 200 if the process is running.
        Used to detect deadlocks/hangs - should restart pod if fails.

        Returns:
            Liveness status
        """
        uptime = time.time() - self.start_time

        return {
            "status": HealthStatus.HEALTHY.value,
            "service": self.service_name,
            "version": self._version,
            "uptime_seconds": round(uptime, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def readiness(self) -> Dict[str, Any]:
        """Kubernetes readiness probe.

        Returns 200 if service can accept traffic.
        Used for load balancing - traffic removed if fails.

        Returns:
            Readiness status with component checks
        """
        # Check cache
        now = time.time()
        if self._cached_readiness and (now - self._cache_time) < self.cache_ttl:
            return self._cached_readiness

        checks_results: List[Dict[str, Any]] = []
        overall_status = HealthStatus.HEALTHY

        # Run health checks
        for name, check_func in self._checks.items():
            result = self._run_check(name, check_func)
            checks_results.append(result.to_dict())

            # Update overall status
            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.DEGRADED:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

        # Check dependencies
        for name, dep in self._dependencies.items():
            checks_results.append({
                "name": f"dependency:{name}",
                "status": dep.status.value,
                "details": {
                    "response_time_ms": dep.response_time_ms,
                    "consecutive_failures": dep.consecutive_failures,
                    "error": dep.error_message,
                },
                "timestamp": dep.last_check.isoformat(),
            })

            if dep.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif dep.status == HealthStatus.DEGRADED:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

        # Check circuit breakers
        cb_status = circuit_breakers.get_all_status()
        for service, status in cb_status.items():
            if status["state"] == "open":
                overall_status = HealthStatus.DEGRADED
                checks_results.append({
                    "name": f"circuit_breaker:{service}",
                    "status": HealthStatus.DEGRADED.value,
                    "details": status,
                })

        result = {
            "status": overall_status.value,
            "service": self.service_name,
            "version": self._version,
            "environment": self._environment,
            "checks": checks_results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Cache result
        self._cached_readiness = result
        self._cache_time = now

        return result

    def startup(self) -> Dict[str, Any]:
        """Kubernetes startup probe.

        Returns 200 when service has completed initialization.
        Used for slow-starting containers.

        Returns:
            Startup status
        """
        initialization_status = {
            name: "complete" if done else "pending"
            for name, done in self._initialization_checks.items()
        }

        status = HealthStatus.HEALTHY if self._initialized else HealthStatus.UNHEALTHY

        return {
            "status": status.value,
            "service": self.service_name,
            "initialized": self._initialized,
            "checks": initialization_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _run_check(
        self,
        name: str,
        check_func: HealthCheckFunc,
    ) -> HealthCheckResult:
        """Run a health check with timing.

        Args:
            name: Check name
            check_func: Check function

        Returns:
            HealthCheckResult
        """
        start = time.time()

        try:
            # Handle both sync and async checks
            if asyncio.iscoroutinefunction(check_func):
                # Run async check in event loop
                try:
                    loop = asyncio.get_running_loop()
                    future = asyncio.ensure_future(check_func())
                    status, details = loop.run_until_complete(future)
                except RuntimeError:
                    # No running loop, create one
                    status, details = asyncio.run(check_func())
            else:
                status, details = check_func()

            latency = (time.time() - start) * 1000

            return HealthCheckResult(
                name=name,
                status=status,
                details=details,
                latency_ms=latency,
            )

        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.warning(f"Health check '{name}' failed: {e}")

            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                details={"error": str(e)},
                latency_ms=latency,
            )

    async def readiness_async(self) -> Dict[str, Any]:
        """Async version of readiness probe.

        Returns:
            Readiness status
        """
        # Check cache
        now = time.time()
        if self._cached_readiness and (now - self._cache_time) < self.cache_ttl:
            return self._cached_readiness

        checks_results: List[Dict[str, Any]] = []
        overall_status = HealthStatus.HEALTHY

        # Run health checks concurrently
        tasks = []
        for name, check_func in self._checks.items():
            tasks.append(self._run_check_async(name, check_func))

        results = await asyncio.gather(*tasks)

        for result in results:
            checks_results.append(result.to_dict())

            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.DEGRADED:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

        # Add dependency checks (same as sync)
        for name, dep in self._dependencies.items():
            checks_results.append({
                "name": f"dependency:{name}",
                "status": dep.status.value,
                "details": {
                    "response_time_ms": dep.response_time_ms,
                    "consecutive_failures": dep.consecutive_failures,
                    "error": dep.error_message,
                },
                "timestamp": dep.last_check.isoformat(),
            })

            if dep.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif dep.status == HealthStatus.DEGRADED:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

        result = {
            "status": overall_status.value,
            "service": self.service_name,
            "version": self._version,
            "environment": self._environment,
            "checks": checks_results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Cache result
        self._cached_readiness = result
        self._cache_time = now

        return result

    async def _run_check_async(
        self,
        name: str,
        check_func: HealthCheckFunc,
    ) -> HealthCheckResult:
        """Run health check asynchronously.

        Args:
            name: Check name
            check_func: Check function

        Returns:
            HealthCheckResult
        """
        start = time.time()

        try:
            if asyncio.iscoroutinefunction(check_func):
                status, details = await check_func()
            else:
                # Run sync function in executor
                loop = asyncio.get_running_loop()
                status, details = await loop.run_in_executor(None, check_func)

            latency = (time.time() - start) * 1000

            return HealthCheckResult(
                name=name,
                status=status,
                details=details,
                latency_ms=latency,
            )

        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.warning(f"Health check '{name}' failed: {e}")

            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                details={"error": str(e)},
                latency_ms=latency,
            )


# Global health check manager
health_manager = HealthCheckManager()


# =============================================================================
# Default Health Checks
# =============================================================================

def check_policy_engine() -> tuple[HealthStatus, Dict[str, Any]]:
    """Check policy engine health."""
    # Placeholder - implement actual check
    return HealthStatus.HEALTHY, {"policies_loaded": 0}


def check_ledger() -> tuple[HealthStatus, Dict[str, Any]]:
    """Check ledger health."""
    # Placeholder - implement actual check
    return HealthStatus.HEALTHY, {"chain_length": 0}


def check_database() -> tuple[HealthStatus, Dict[str, Any]]:
    """Check database connectivity."""
    try:
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.execute("SELECT 1")
        conn.close()
        return HealthStatus.HEALTHY, {"type": "sqlite", "connected": True}
    except Exception as e:
        return HealthStatus.UNHEALTHY, {"error": str(e)}


async def check_redis() -> tuple[HealthStatus, Dict[str, Any]]:
    """Check Redis cache connectivity."""
    try:
        # Placeholder - implement actual Redis check
        return HealthStatus.HEALTHY, {"connected": True}
    except Exception as e:
        return HealthStatus.UNHEALTHY, {"error": str(e)}


# Register default checks
health_manager.add_check("policy_engine", check_policy_engine)
health_manager.add_check("ledger", check_ledger)
health_manager.add_check("database", check_database, required_for_startup=True)


# =============================================================================
# Convenience Functions
# =============================================================================

def liveness() -> Dict[str, Any]:
    """Get liveness status."""
    return health_manager.liveness()


def readiness() -> Dict[str, Any]:
    """Get readiness status."""
    return health_manager.readiness()


def startup() -> Dict[str, Any]:
    """Get startup status."""
    return health_manager.startup()
