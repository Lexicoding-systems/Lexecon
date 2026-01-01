"""Prometheus metrics for Lexecon."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from typing import Dict, Any
import time

# Request metrics
http_requests_total = Counter(
    "lexecon_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "lexecon_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# Decision metrics
decisions_total = Counter(
    "lexecon_decisions_total",
    "Total governance decisions made",
    ["allowed", "actor", "risk_level"],
)

decision_evaluation_duration_seconds = Histogram(
    "lexecon_decision_evaluation_duration_seconds",
    "Decision evaluation duration in seconds",
    ["policy_mode"],
)

decisions_denied_total = Counter(
    "lexecon_decisions_denied_total",
    "Total decisions denied",
    ["reason_category", "actor"],
)

# Policy metrics
policies_loaded_total = Counter(
    "lexecon_policies_loaded_total",
    "Total policies loaded",
    ["policy_name"],
)

active_policies = Gauge(
    "lexecon_active_policies",
    "Number of currently active policies",
)

policy_evaluation_errors_total = Counter(
    "lexecon_policy_evaluation_errors_total",
    "Total policy evaluation errors",
    ["error_type"],
)

# Ledger metrics
ledger_entries_total = Counter(
    "lexecon_ledger_entries_total",
    "Total ledger entries created",
)

ledger_verification_duration_seconds = Histogram(
    "lexecon_ledger_verification_duration_seconds",
    "Ledger verification duration in seconds",
)

ledger_integrity_checks_total = Counter(
    "lexecon_ledger_integrity_checks_total",
    "Total ledger integrity checks",
    ["result"],
)

# Capability token metrics
tokens_issued_total = Counter(
    "lexecon_tokens_issued_total",
    "Total capability tokens issued",
    ["scope"],
)

tokens_verified_total = Counter(
    "lexecon_tokens_verified_total",
    "Total token verifications",
    ["valid"],
)

active_tokens = Gauge(
    "lexecon_active_tokens",
    "Number of currently active capability tokens",
)

# System metrics
node_info = Gauge(
    "lexecon_node_info",
    "Node information",
    ["node_id", "version"],
)

node_uptime_seconds = Gauge(
    "lexecon_node_uptime_seconds",
    "Node uptime in seconds",
)


class MetricsCollector:
    """Metrics collection helper."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.start_time = time.time()

    def record_request(
        self, method: str, endpoint: str, status: int, duration: float
    ) -> None:
        """Record HTTP request metrics."""
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    def record_decision(
        self, allowed: bool, actor: str, risk_level: int, duration: float
    ) -> None:
        """Record decision metrics."""
        decisions_total.labels(
            allowed=str(allowed), actor=actor, risk_level=str(risk_level)
        ).inc()
        decision_evaluation_duration_seconds.labels(policy_mode="strict").observe(
            duration
        )

    def record_denial(self, reason_category: str, actor: str) -> None:
        """Record decision denial."""
        decisions_denied_total.labels(
            reason_category=reason_category, actor=actor
        ).inc()

    def record_policy_load(self, policy_name: str) -> None:
        """Record policy load."""
        policies_loaded_total.labels(policy_name=policy_name).inc()
        active_policies.inc()

    def record_ledger_entry(self) -> None:
        """Record ledger entry creation."""
        ledger_entries_total.inc()

    def record_token_issuance(self, scope: str) -> None:
        """Record token issuance."""
        tokens_issued_total.labels(scope=scope).inc()
        active_tokens.inc()

    def record_token_verification(self, valid: bool) -> None:
        """Record token verification."""
        tokens_verified_total.labels(valid=str(valid)).inc()

    def get_uptime(self) -> float:
        """Get node uptime in seconds."""
        return time.time() - self.start_time

    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format."""
        return generate_latest(REGISTRY)


# Global metrics instance
metrics = MetricsCollector()


# Convenience functions
def record_decision(allowed: bool, actor: str, risk_level: int, duration: float) -> None:
    """Record a decision metric."""
    metrics.record_decision(allowed, actor, risk_level, duration)


def record_policy_load(policy_name: str) -> None:
    """Record a policy load metric."""
    metrics.record_policy_load(policy_name)
