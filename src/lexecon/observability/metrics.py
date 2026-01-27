"""Prometheus metrics for Lexecon.

This module provides backward compatibility by re-exporting from metrics_v2.
All metrics are created in metrics_v2 to avoid duplication in CollectorRegistry.
"""

# Re-export all metric objects from metrics_v2 to avoid duplication
from lexecon.observability.metrics_v2 import (
    MetricsCollector,
    active_policies,
    active_tokens,
    decision_evaluation_duration_seconds,
    decisions_denied_total,
    decisions_total,
    http_request_duration_seconds,
    http_requests_total,
    ledger_entries_total,
    ledger_integrity_checks_total,
    ledger_verification_duration_seconds,
    metrics,
    node_info,
    node_uptime_seconds,
    policies_loaded_total,
    policy_evaluation_errors_total,
    record_decision,
    record_policy_load,
    tokens_issued_total,
    tokens_verified_total,
)

__all__ = [
    # Metric objects
    "http_requests_total",
    "http_request_duration_seconds",
    "decisions_total",
    "decision_evaluation_duration_seconds",
    "decisions_denied_total",
    "policies_loaded_total",
    "active_policies",
    "policy_evaluation_errors_total",
    "ledger_entries_total",
    "ledger_verification_duration_seconds",
    "ledger_integrity_checks_total",
    "tokens_issued_total",
    "tokens_verified_total",
    "active_tokens",
    "node_info",
    "node_uptime_seconds",
    # Collector and functions
    "MetricsCollector",
    "metrics",
    "record_decision",
    "record_policy_load",
]
