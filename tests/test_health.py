"""Tests for health check and observability functionality."""

import time

from lexecon.observability.health import (
    HealthCheck,
    HealthStatus,
    check_identity,
    check_ledger,
    check_policy_engine,
)


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_health_status_values(self):
        """Test that health status enum has expected values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"

    def test_health_status_is_string(self):
        """Test that health status values are strings."""
        assert isinstance(HealthStatus.HEALTHY, str)
        assert isinstance(HealthStatus.DEGRADED, str)
        assert isinstance(HealthStatus.UNHEALTHY, str)


class TestHealthCheck:
    """Tests for HealthCheck class."""

    def test_initialization(self):
        """Test health check initialization."""
        hc = HealthCheck()

        assert hc.checks is not None
        assert hc.start_time > 0
        assert isinstance(hc.checks, dict)

    def test_liveness_probe(self):
        """Test liveness probe returns healthy status."""
        hc = HealthCheck()

        result = hc.liveness()

        assert result["status"] == HealthStatus.HEALTHY
        assert "timestamp" in result
        assert "uptime_seconds" in result
        assert result["uptime_seconds"] >= 0

    def test_liveness_uptime_increases(self):
        """Test that uptime increases over time."""
        hc = HealthCheck()

        result1 = hc.liveness()
        time.sleep(0.1)
        result2 = hc.liveness()

        assert result2["uptime_seconds"] > result1["uptime_seconds"]

    def test_readiness_probe_no_checks(self):
        """Test readiness probe with no health checks registered."""
        hc = HealthCheck()
        hc.checks = {}  # Clear default checks

        result = hc.readiness()

        assert result["status"] == HealthStatus.HEALTHY
        assert "timestamp" in result
        assert "checks" in result
        assert len(result["checks"]) == 0

    def test_readiness_probe_all_healthy(self):
        """Test readiness probe when all checks are healthy."""
        hc = HealthCheck()
        hc.checks = {}  # Clear default checks

        # Add healthy checks
        hc.add_check("check1", lambda: (HealthStatus.HEALTHY, {"detail": "ok"}))
        hc.add_check("check2", lambda: (HealthStatus.HEALTHY, {"detail": "ok"}))

        result = hc.readiness()

        assert result["status"] == HealthStatus.HEALTHY
        assert len(result["checks"]) == 2
        assert all(c["status"] == HealthStatus.HEALTHY for c in result["checks"])

    def test_readiness_probe_one_degraded(self):
        """Test readiness probe with one degraded check."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("healthy", lambda: (HealthStatus.HEALTHY, {}))
        hc.add_check("degraded", lambda: (HealthStatus.DEGRADED, {"reason": "slow"}))

        result = hc.readiness()

        assert result["status"] == HealthStatus.DEGRADED
        assert len(result["checks"]) == 2

    def test_readiness_probe_one_unhealthy(self):
        """Test readiness probe with one unhealthy check."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("healthy", lambda: (HealthStatus.HEALTHY, {}))
        hc.add_check("unhealthy", lambda: (HealthStatus.UNHEALTHY, {"error": "failed"}))

        result = hc.readiness()

        assert result["status"] == HealthStatus.UNHEALTHY
        assert len(result["checks"]) == 2

        # Find unhealthy check
        unhealthy_check = next(c for c in result["checks"] if c["name"] == "unhealthy")
        assert unhealthy_check["details"]["error"] == "failed"

    def test_readiness_unhealthy_takes_precedence(self):
        """Test that unhealthy status takes precedence over degraded."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("degraded", lambda: (HealthStatus.DEGRADED, {}))
        hc.add_check("unhealthy", lambda: (HealthStatus.UNHEALTHY, {}))
        hc.add_check("healthy", lambda: (HealthStatus.HEALTHY, {}))

        result = hc.readiness()

        assert result["status"] == HealthStatus.UNHEALTHY

    def test_readiness_handles_check_exception(self):
        """Test readiness probe handles exceptions in health checks."""
        hc = HealthCheck()
        hc.checks = {}

        def failing_check():
            raise RuntimeError("Check failed")

        hc.add_check("healthy", lambda: (HealthStatus.HEALTHY, {}))
        hc.add_check("failing", failing_check)

        result = hc.readiness()

        # Overall status should be unhealthy
        assert result["status"] == HealthStatus.UNHEALTHY

        # Failing check should show error
        failing_result = next(c for c in result["checks"] if c["name"] == "failing")
        assert failing_result["status"] == HealthStatus.UNHEALTHY
        assert "error" in failing_result["details"]
        assert "Check failed" in failing_result["details"]["error"]

    def test_add_check(self):
        """Test adding custom health check."""
        hc = HealthCheck()
        hc.checks = {}

        def custom_check():
            return HealthStatus.HEALTHY, {"custom": "data"}

        hc.add_check("custom", custom_check)

        assert "custom" in hc.checks
        assert hc.checks["custom"] == custom_check

    def test_add_multiple_checks(self):
        """Test adding multiple health checks."""
        hc = HealthCheck()
        hc.checks = {}

        for i in range(5):
            hc.add_check(f"check{i}", lambda: (HealthStatus.HEALTHY, {}))

        assert len(hc.checks) == 5

    def test_startup_probe(self):
        """Test startup probe."""
        hc = HealthCheck()

        result = hc.startup()

        assert result["status"] == HealthStatus.HEALTHY
        assert "timestamp" in result
        assert "message" in result
        assert result["message"] == "Service initialized"

    def test_readiness_check_details(self):
        """Test that readiness probe includes check details."""
        hc = HealthCheck()
        hc.checks = {}

        details = {"version": "1.0", "connections": 5}
        hc.add_check("detailed", lambda: (HealthStatus.HEALTHY, details))

        result = hc.readiness()

        check_result = result["checks"][0]
        assert check_result["name"] == "detailed"
        assert check_result["details"] == details

    def test_multiple_unhealthy_checks(self):
        """Test handling multiple unhealthy checks."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("fail1", lambda: (HealthStatus.UNHEALTHY, {"error": "error1"}))
        hc.add_check("fail2", lambda: (HealthStatus.UNHEALTHY, {"error": "error2"}))

        result = hc.readiness()

        assert result["status"] == HealthStatus.UNHEALTHY
        assert len(result["checks"]) == 2
        assert all(c["status"] == HealthStatus.UNHEALTHY for c in result["checks"])


class TestDefaultHealthChecks:
    """Tests for default health check functions."""

    def test_check_policy_engine(self):
        """Test policy engine health check."""
        status, details = check_policy_engine()

        assert status == HealthStatus.HEALTHY
        assert "policies_loaded" in details
        assert isinstance(details["policies_loaded"], int)

    def test_check_ledger(self):
        """Test ledger health check."""
        status, details = check_ledger()

        assert status == HealthStatus.HEALTHY
        assert "entries" in details
        assert "last_verified" in details
        assert isinstance(details["entries"], int)
        assert isinstance(details["last_verified"], float)

    def test_check_identity(self):
        """Test identity health check."""
        status, details = check_identity()

        assert status == HealthStatus.HEALTHY
        assert "key_loaded" in details
        assert isinstance(details["key_loaded"], bool)


class TestHealthCheckIntegration:
    """Integration tests for health check system."""

    def test_default_health_check_instance(self):
        """Test that default health check instance has checks registered."""
        from lexecon.observability.health import health_check

        # Should have default checks registered
        assert len(health_check.checks) > 0
        assert "policy_engine" in health_check.checks
        assert "ledger" in health_check.checks
        assert "identity" in health_check.checks

    def test_full_readiness_check(self):
        """Test full readiness check with default checks."""
        from lexecon.observability.health import health_check

        result = health_check.readiness()

        assert "status" in result
        assert "checks" in result
        assert len(result["checks"]) >= 3  # At least the 3 default checks

    def test_liveness_timestamp_is_recent(self):
        """Test that liveness timestamp is recent."""
        hc = HealthCheck()

        result = hc.liveness()

        # Timestamp should be within last second
        now = time.time()
        assert abs(now - result["timestamp"]) < 1.0

    def test_readiness_timestamp_is_recent(self):
        """Test that readiness timestamp is recent."""
        hc = HealthCheck()

        result = hc.readiness()

        now = time.time()
        assert abs(now - result["timestamp"]) < 1.0


class TestHealthCheckEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_check_returning_none(self):
        """Test handling check that returns None."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("none_check", lambda: None)

        # Should handle by catching exception in readiness check
        result = hc.readiness()
        # Should mark as unhealthy due to exception
        assert result["status"] == HealthStatus.UNHEALTHY

    def test_check_returning_invalid_status(self):
        """Test handling check with invalid status."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("invalid", lambda: ("invalid_status", {}))

        result = hc.readiness()

        # Should still run, but status might not be recognized
        assert result is not None

    def test_check_with_empty_details(self):
        """Test check with empty details."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("empty", lambda: (HealthStatus.HEALTHY, {}))

        result = hc.readiness()

        assert result["status"] == HealthStatus.HEALTHY
        check = result["checks"][0]
        assert check["details"] == {}

    def test_check_with_complex_details(self):
        """Test check with complex nested details."""
        hc = HealthCheck()
        hc.checks = {}

        complex_details = {
            "metrics": {"cpu": 45.2, "memory": 1024},
            "connections": [{"id": 1, "status": "active"}, {"id": 2, "status": "idle"}],
            "metadata": {"version": "1.0", "uptime": 3600},
        }

        hc.add_check("complex", lambda: (HealthStatus.HEALTHY, complex_details))

        result = hc.readiness()

        check = result["checks"][0]
        assert check["details"] == complex_details

    def test_overwrite_check(self):
        """Test that adding check with same name overwrites."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("check", lambda: (HealthStatus.HEALTHY, {"version": 1}))
        hc.add_check("check", lambda: (HealthStatus.DEGRADED, {"version": 2}))

        result = hc.readiness()

        # Should only have 1 check
        assert len(result["checks"]) == 1

        # Should be the second one
        assert result["checks"][0]["status"] == HealthStatus.DEGRADED
        assert result["checks"][0]["details"]["version"] == 2

    def test_check_with_very_long_execution_time(self):
        """Test check that takes long to execute."""
        hc = HealthCheck()
        hc.checks = {}

        def slow_check():
            time.sleep(0.2)
            return HealthStatus.HEALTHY, {"slow": True}

        hc.add_check("slow", slow_check)

        start = time.time()
        result = hc.readiness()
        duration = time.time() - start

        # Should still complete
        assert result["status"] == HealthStatus.HEALTHY
        assert duration >= 0.2

    def test_many_checks(self):
        """Test with many health checks."""
        hc = HealthCheck()
        hc.checks = {}

        # Add 100 checks
        for i in range(100):
            hc.add_check(f"check{i}", lambda: (HealthStatus.HEALTHY, {}))

        result = hc.readiness()

        assert len(result["checks"]) == 100
        assert result["status"] == HealthStatus.HEALTHY

    def test_mixed_status_priority(self):
        """Test status priority with all three statuses."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("healthy1", lambda: (HealthStatus.HEALTHY, {}))
        hc.add_check("healthy2", lambda: (HealthStatus.HEALTHY, {}))
        hc.add_check("degraded1", lambda: (HealthStatus.DEGRADED, {}))
        hc.add_check("unhealthy1", lambda: (HealthStatus.UNHEALTHY, {}))

        result = hc.readiness()

        # Unhealthy should take precedence
        assert result["status"] == HealthStatus.UNHEALTHY

    def test_only_degraded_checks(self):
        """Test with only degraded checks."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("deg1", lambda: (HealthStatus.DEGRADED, {}))
        hc.add_check("deg2", lambda: (HealthStatus.DEGRADED, {}))

        result = hc.readiness()

        assert result["status"] == HealthStatus.DEGRADED


class TestHealthCheckConcurrency:
    """Tests for concurrent health check scenarios."""

    def test_multiple_liveness_calls(self):
        """Test multiple simultaneous liveness calls."""
        hc = HealthCheck()

        results = [hc.liveness() for _ in range(10)]

        # All should succeed
        assert len(results) == 10
        assert all(r["status"] == HealthStatus.HEALTHY for r in results)

    def test_multiple_readiness_calls(self):
        """Test multiple simultaneous readiness calls."""
        hc = HealthCheck()
        hc.checks = {}
        hc.add_check("test", lambda: (HealthStatus.HEALTHY, {}))

        results = [hc.readiness() for _ in range(10)]

        # All should succeed
        assert len(results) == 10
        assert all(r["status"] == HealthStatus.HEALTHY for r in results)

    def test_concurrent_check_modifications(self):
        """Test that checks can be added during operation."""
        hc = HealthCheck()
        hc.checks = {}

        hc.add_check("initial", lambda: (HealthStatus.HEALTHY, {}))

        result1 = hc.readiness()
        assert len(result1["checks"]) == 1

        hc.add_check("added", lambda: (HealthStatus.HEALTHY, {}))

        result2 = hc.readiness()
        assert len(result2["checks"]) == 2


class TestHealthCheckSerialization:
    """Tests for health check result serialization."""

    def test_liveness_result_is_dict(self):
        """Test that liveness result is JSON-serializable."""
        hc = HealthCheck()
        result = hc.liveness()

        import json

        # Should be serializable to JSON
        json_str = json.dumps(result)
        assert len(json_str) > 0

        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed["status"] == HealthStatus.HEALTHY

    def test_readiness_result_is_dict(self):
        """Test that readiness result is JSON-serializable."""
        hc = HealthCheck()
        hc.checks = {}
        hc.add_check("test", lambda: (HealthStatus.HEALTHY, {"count": 5}))

        result = hc.readiness()

        import json

        json_str = json.dumps(result)
        parsed = json.loads(json_str)

        assert parsed["status"] == HealthStatus.HEALTHY
        assert len(parsed["checks"]) == 1

    def test_startup_result_is_dict(self):
        """Test that startup result is JSON-serializable."""
        hc = HealthCheck()
        result = hc.startup()

        import json

        json_str = json.dumps(result)
        parsed = json.loads(json_str)

        assert parsed["status"] == HealthStatus.HEALTHY
