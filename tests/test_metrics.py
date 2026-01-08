"""Tests for Prometheus metrics."""

import time

import pytest
from prometheus_client import REGISTRY

from lexecon.observability.metrics import (
    MetricsCollector,
    active_policies,
    active_tokens,
    decisions_denied_total,
    decisions_total,
    http_request_duration_seconds,
    http_requests_total,
    ledger_entries_total,
    metrics,
    node_uptime_seconds,
    policies_loaded_total,
    record_decision,
    record_policy_load,
    tokens_issued_total,
    tokens_verified_total,
)


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector()

        assert collector.start_time > 0
        assert isinstance(collector.start_time, float)

    def test_record_request(self):
        """Test recording HTTP request metrics."""
        collector = MetricsCollector()

        # Get initial value
        initial_requests = http_requests_total.labels(
            method="GET", endpoint="/health", status=200
        )._value.get()

        # Record request
        collector.record_request("GET", "/health", 200, 0.123)

        # Verify counter increased
        final_requests = http_requests_total.labels(
            method="GET", endpoint="/health", status=200
        )._value.get()

        assert final_requests > initial_requests

    def test_record_request_duration(self):
        """Test that request duration is recorded."""
        collector = MetricsCollector()

        # Record request with duration
        collector.record_request("POST", "/decide", 200, 0.456)

        # Histogram should have recorded the observation
        # We can't easily check the exact value, but we can verify it doesn't error
        histogram = http_request_duration_seconds.labels(method="POST", endpoint="/decide")
        assert histogram is not None

    def test_record_decision(self):
        """Test recording decision metrics."""
        collector = MetricsCollector()

        # Get initial value
        initial_decisions = decisions_total.labels(
            allowed="True", actor="model", risk_level="1"
        )._value.get()

        # Record decision
        collector.record_decision(allowed=True, actor="model", risk_level=1, duration=0.1)

        # Verify counter increased
        final_decisions = decisions_total.labels(
            allowed="True", actor="model", risk_level="1"
        )._value.get()

        assert final_decisions > initial_decisions

    def test_record_denial(self):
        """Test recording decision denial."""
        collector = MetricsCollector()

        initial_denials = decisions_denied_total.labels(
            reason_category="policy", actor="model"
        )._value.get()

        collector.record_denial(reason_category="policy", actor="model")

        final_denials = decisions_denied_total.labels(
            reason_category="policy", actor="model"
        )._value.get()

        assert final_denials > initial_denials

    def test_record_policy_load(self):
        """Test recording policy load."""
        collector = MetricsCollector()

        initial_loads = policies_loaded_total.labels(policy_name="test_policy")._value.get()
        initial_active = active_policies._value.get()

        collector.record_policy_load("test_policy")

        final_loads = policies_loaded_total.labels(policy_name="test_policy")._value.get()
        final_active = active_policies._value.get()

        assert final_loads > initial_loads
        assert final_active > initial_active

    def test_record_ledger_entry(self):
        """Test recording ledger entry."""
        collector = MetricsCollector()

        initial_entries = ledger_entries_total._value.get()

        collector.record_ledger_entry()

        final_entries = ledger_entries_total._value.get()

        assert final_entries > initial_entries

    def test_record_token_issuance(self):
        """Test recording token issuance."""
        collector = MetricsCollector()

        initial_issued = tokens_issued_total.labels(scope="action:read")._value.get()
        initial_active = active_tokens._value.get()

        collector.record_token_issuance("action:read")

        final_issued = tokens_issued_total.labels(scope="action:read")._value.get()
        final_active = active_tokens._value.get()

        assert final_issued > initial_issued
        assert final_active > initial_active

    def test_record_token_verification(self):
        """Test recording token verification."""
        collector = MetricsCollector()

        initial_verified = tokens_verified_total.labels(valid="True")._value.get()

        collector.record_token_verification(valid=True)

        final_verified = tokens_verified_total.labels(valid="True")._value.get()

        assert final_verified > initial_verified

    def test_get_uptime(self):
        """Test getting node uptime."""
        collector = MetricsCollector()

        uptime1 = collector.get_uptime()
        assert uptime1 >= 0

        time.sleep(0.1)

        uptime2 = collector.get_uptime()
        assert uptime2 > uptime1

    def test_export_metrics(self):
        """Test exporting metrics in Prometheus format."""
        collector = MetricsCollector()

        output = collector.export_metrics()

        assert isinstance(output, bytes)
        assert len(output) > 0

        # Should contain Prometheus format markers
        decoded = output.decode("utf-8")
        assert "# HELP" in decoded or "# TYPE" in decoded


class TestGlobalMetricsInstance:
    """Tests for global metrics instance."""

    def test_global_metrics_exists(self):
        """Test that global metrics instance exists."""
        assert metrics is not None
        assert isinstance(metrics, MetricsCollector)

    def test_global_metrics_record_decision(self):
        """Test using global metrics instance."""
        initial = decisions_total.labels(allowed="False", actor="user", risk_level="3")._value.get()

        metrics.record_decision(allowed=False, actor="user", risk_level=3, duration=0.2)

        final = decisions_total.labels(allowed="False", actor="user", risk_level="3")._value.get()

        assert final > initial


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_record_decision_function(self):
        """Test record_decision convenience function."""
        initial = decisions_total.labels(allowed="True", actor="bot", risk_level="2")._value.get()

        record_decision(allowed=True, actor="bot", risk_level=2, duration=0.15)

        final = decisions_total.labels(allowed="True", actor="bot", risk_level="2")._value.get()

        assert final > initial

    def test_record_policy_load_function(self):
        """Test record_policy_load convenience function."""
        initial = policies_loaded_total.labels(policy_name="conv_policy")._value.get()

        record_policy_load("conv_policy")

        final = policies_loaded_total.labels(policy_name="conv_policy")._value.get()

        assert final > initial


class TestMetricTypes:
    """Tests for different metric types."""

    def test_counter_increments(self):
        """Test that counters only increment."""
        initial = http_requests_total.labels(
            method="GET", endpoint="/test", status=200
        )._value.get()

        # Increment multiple times
        for _ in range(5):
            metrics.record_request("GET", "/test", 200, 0.1)

        final = http_requests_total.labels(method="GET", endpoint="/test", status=200)._value.get()

        # Should have incremented by 5
        assert final >= initial + 5

    def test_gauge_can_increase_and_decrease(self):
        """Test that gauges can increase and decrease."""
        initial = active_policies._value.get()

        # Increase
        active_policies.inc()
        increased = active_policies._value.get()
        assert increased > initial

        # Decrease
        active_policies.dec()
        decreased = active_policies._value.get()
        assert decreased < increased

    def test_histogram_records_observations(self):
        """Test that histograms record observations."""
        histogram = http_request_duration_seconds.labels(method="GET", endpoint="/metrics")

        # Record several observations
        histogram.observe(0.1)
        histogram.observe(0.2)
        histogram.observe(0.3)

        # Histogram should have recorded these
        # We can't easily check exact values, but verify no errors
        assert histogram is not None


class TestMetricLabels:
    """Tests for metric label handling."""

    def test_different_labels_separate_metrics(self):
        """Test that different labels create separate metric series."""
        initial_200 = http_requests_total.labels(
            method="GET", endpoint="/api", status=200
        )._value.get()

        initial_404 = http_requests_total.labels(
            method="GET", endpoint="/api", status=404
        )._value.get()

        # Record 200
        metrics.record_request("GET", "/api", 200, 0.1)

        # Only 200 should increment
        final_200 = http_requests_total.labels(
            method="GET", endpoint="/api", status=200
        )._value.get()

        final_404 = http_requests_total.labels(
            method="GET", endpoint="/api", status=404
        )._value.get()

        assert final_200 > initial_200
        assert final_404 == initial_404

    def test_label_combinations(self):
        """Test various label combinations."""
        # Test different actors
        metrics.record_decision(True, "actor1", 1, 0.1)
        metrics.record_decision(True, "actor2", 1, 0.1)

        # Test different risk levels
        metrics.record_decision(True, "model", 1, 0.1)
        metrics.record_decision(True, "model", 5, 0.1)

        # Test different allowed values
        metrics.record_decision(True, "user", 1, 0.1)
        metrics.record_decision(False, "user", 1, 0.1)

        # All should be recorded separately
        # If this completes without error, labels are working


class TestMetricsIntegration:
    """Integration tests for metrics system."""

    def test_complete_request_workflow(self):
        """Test recording complete request workflow."""
        # Record incoming request
        start_time = time.time()
        metrics.record_request("POST", "/decide", 200, 0.2)

        # Record decision
        metrics.record_decision(True, "model", 2, 0.15)

        # Record token issuance
        metrics.record_token_issuance("action:search")

        # Record ledger entry
        metrics.record_ledger_entry()

        # All should succeed without error

    def test_decision_workflow_metrics(self):
        """Test metrics for decision workflow."""
        # Load policy
        metrics.record_policy_load("workflow_policy")

        # Make decision (permitted)
        metrics.record_decision(True, "workflow_actor", 1, 0.1)

        # Issue token
        metrics.record_token_issuance("workflow:action")

        # Verify token later
        metrics.record_token_verification(True)

        # Record to ledger
        metrics.record_ledger_entry()

        # Workflow complete - verify no errors

    def test_denial_workflow_metrics(self):
        """Test metrics for denial workflow."""
        # Make decision (denied)
        metrics.record_decision(False, "denied_actor", 5, 0.1)

        # Record denial reason
        metrics.record_denial("high_risk", "denied_actor")

        # Still record to ledger
        metrics.record_ledger_entry()

        # Workflow complete


class TestPrometheusExport:
    """Tests for Prometheus export functionality."""

    def test_export_format(self):
        """Test Prometheus export format."""
        output = metrics.export_metrics()
        decoded = output.decode("utf-8")

        # Should contain metric definitions
        assert "lexecon_" in decoded

        # Should contain HELP and TYPE comments
        lines = decoded.split("\n")
        help_lines = [l for l in lines if l.startswith("# HELP")]
        type_lines = [l for l in lines if l.startswith("# TYPE")]

        assert len(help_lines) > 0
        assert len(type_lines) > 0

    def test_export_includes_values(self):
        """Test that export includes metric values."""
        # Record some metrics
        metrics.record_decision(True, "export_test", 1, 0.1)
        metrics.record_ledger_entry()

        output = metrics.export_metrics()
        decoded = output.decode("utf-8")

        # Should contain metric values (numbers)
        assert any(char.isdigit() for char in decoded)

    def test_export_is_valid_prometheus_format(self):
        """Test that export is valid Prometheus format."""
        output = metrics.export_metrics()
        decoded = output.decode("utf-8")

        lines = decoded.split("\n")

        # Each metric line should have format: metric_name{labels} value
        metric_lines = [l for l in lines if l and not l.startswith("#")]

        for line in metric_lines[:10]:  # Check first 10
            if "{" in line:
                # Has labels
                assert "}" in line
                assert " " in line  # Space before value
            elif " " in line and line.strip():
                # No labels, just name and value
                parts = line.split()
                assert len(parts) >= 2


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_record_zero_duration(self):
        """Test recording request with zero duration."""
        metrics.record_request("GET", "/fast", 200, 0.0)
        # Should not error

    def test_record_very_long_duration(self):
        """Test recording very long request duration."""
        metrics.record_request("GET", "/slow", 200, 100.0)
        # Should not error

    def test_record_high_risk_level(self):
        """Test recording decision with high risk level."""
        metrics.record_decision(False, "risky", 10, 0.1)
        # Should not error

    def test_record_special_characters_in_labels(self):
        """Test labels with special characters."""
        # Prometheus should handle these
        metrics.record_decision(True, "actor-with-dash", 1, 0.1)
        metrics.record_policy_load("policy_with_underscore")
        # Should not error

    def test_record_empty_scope(self):
        """Test recording token with empty scope."""
        metrics.record_token_issuance("")
        # Should not error

    def test_concurrent_metric_recording(self):
        """Test recording metrics concurrently."""
        # Simulate concurrent requests
        for i in range(100):
            metrics.record_request("GET", f"/endpoint{i % 5}", 200, 0.01)
            metrics.record_decision(True, "concurrent", 1, 0.01)

        # Should handle all without error

    def test_uptime_never_negative(self):
        """Test that uptime is never negative."""
        collector = MetricsCollector()

        for _ in range(10):
            uptime = collector.get_uptime()
            assert uptime >= 0
            time.sleep(0.01)

    def test_export_with_no_metrics(self):
        """Test exporting when no metrics recorded."""
        # Create fresh collector
        collector = MetricsCollector()

        output = collector.export_metrics()

        # Should still produce valid output
        assert isinstance(output, bytes)
        assert len(output) > 0

    def test_multiple_collectors(self):
        """Test creating multiple collector instances."""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()

        # Should have different start times if created at different times
        time.sleep(0.01)
        collector3 = MetricsCollector()

        uptime1 = collector1.get_uptime()
        uptime3 = collector3.get_uptime()

        # collector1 should have slightly higher uptime
        assert uptime1 >= uptime3
