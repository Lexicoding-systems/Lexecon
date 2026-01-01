"""Health check endpoints for Lexecon."""

from typing import Dict, Any, List
from enum import Enum
import time


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """Health check manager."""

    def __init__(self) -> None:
        """Initialize health check manager."""
        self.start_time = time.time()
        self.checks: Dict[str, Any] = {}

    def add_check(self, name: str, check_func: Any) -> None:
        """Add a health check.

        Args:
            name: Check name
            check_func: Function that returns (status, details)
        """
        self.checks[name] = check_func

    def liveness(self) -> Dict[str, Any]:
        """Liveness probe - is the service running?

        Returns:
            Liveness status
        """
        return {
            "status": HealthStatus.HEALTHY,
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.start_time,
        }

    def readiness(self) -> Dict[str, Any]:
        """Readiness probe - is the service ready to accept traffic?

        Returns:
            Readiness status with component checks
        """
        checks_results: List[Dict[str, Any]] = []
        overall_status = HealthStatus.HEALTHY

        for name, check_func in self.checks.items():
            try:
                status, details = check_func()
                checks_results.append(
                    {"name": name, "status": status, "details": details}
                )

                # Update overall status
                if status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif status == HealthStatus.DEGRADED and overall_status != HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.DEGRADED

            except Exception as e:
                checks_results.append(
                    {
                        "name": name,
                        "status": HealthStatus.UNHEALTHY,
                        "details": {"error": str(e)},
                    }
                )
                overall_status = HealthStatus.UNHEALTHY

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "checks": checks_results,
        }

    def startup(self) -> Dict[str, Any]:
        """Startup probe - has the service completed initialization?

        Returns:
            Startup status
        """
        # Check if essential components are initialized
        return {
            "status": HealthStatus.HEALTHY,
            "timestamp": time.time(),
            "message": "Service initialized",
        }


# Global health check instance
health_check = HealthCheck()


# Example health checks
def check_policy_engine() -> tuple[HealthStatus, Dict[str, Any]]:
    """Check policy engine health."""
    # Implement actual check
    return HealthStatus.HEALTHY, {"policies_loaded": 3}


def check_ledger() -> tuple[HealthStatus, Dict[str, Any]]:
    """Check ledger health."""
    # Implement actual check
    return HealthStatus.HEALTHY, {"entries": 100, "last_verified": time.time()}


def check_identity() -> tuple[HealthStatus, Dict[str, Any]]:
    """Check identity system health."""
    # Implement actual check
    return HealthStatus.HEALTHY, {"key_loaded": True}


# Register default checks
health_check.add_check("policy_engine", check_policy_engine)
health_check.add_check("ledger", check_ledger)
health_check.add_check("identity", check_identity)
