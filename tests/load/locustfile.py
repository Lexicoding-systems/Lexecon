"""
Locust load testing for Lexecon (Phase 8).

Simulates realistic user behavior for performance testing.

Usage:
    # Run with web UI
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Run headless
    locust -f tests/load/locustfile.py \
        --host=http://localhost:8000 \
        --users=100 \
        --spawn-rate=10 \
        --run-time=10m \
        --headless
"""

import random
from locust import HttpUser, task, between, events


class LexeconUser(HttpUser):
    """Simulated Lexecon user for load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self) -> None:
        """Initialize user session (login)."""
        # Login to get access token
        response = self.client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "TestPassword123!"},
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            # Fallback to test mode (if authentication not implemented)
            self.token = None

    @task(10)  # Weight: 10 (most common operation)
    def evaluate_decision(self) -> None:
        """Evaluate governance decision."""
        self.client.post(
            "/api/decide",
            json={
                "actor": f"user:user{random.randint(1, 1000)}@example.com",
                "action": random.choice(["read", "write", "delete", "admin"]),
                "resource": f"resource:{random.randint(1, 100)}",
            },
            name="/api/decide",
        )

    @task(5)  # Weight: 5
    def list_decisions_recent(self) -> None:
        """List recent decisions (paginated)."""
        self.client.get(
            "/api/decisions",
            params={"limit": 50},
            name="/api/decisions?limit=50",
        )

    @task(3)  # Weight: 3
    def list_policies_active(self) -> None:
        """List active policies."""
        self.client.get(
            "/api/policies",
            params={"active": "true"},
            name="/api/policies?active=true",
        )

    @task(2)  # Weight: 2
    def get_specific_decision(self) -> None:
        """Get specific decision by ID."""
        decision_id = f"dec_{random.randint(1, 10000)}"
        self.client.get(f"/api/decisions/{decision_id}", name="/api/decisions/:id")

    @task(2)  # Weight: 2
    def list_audit_logs(self) -> None:
        """Retrieve audit logs."""
        self.client.get(
            "/api/audit-logs",
            params={"limit": 100},
            name="/api/audit-logs?limit=100",
        )

    @task(1)  # Weight: 1
    def health_check(self) -> None:
        """Health check endpoint."""
        self.client.get("/health", name="/health")

    @task(1)  # Weight: 1
    def metrics_endpoint(self) -> None:
        """Metrics endpoint (Prometheus)."""
        self.client.get("/metrics", name="/metrics")


@events.test_start.add_listener
def on_test_start(environment, **kwargs) -> None:
    """Event handler for test start."""
    print("🚀 Starting load test...")
    print(f"   Target host: {environment.host}")
    print(f"   Users: {environment.runner.target_user_count}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:
    """Event handler for test stop."""
    stats = environment.stats
    print("\n📊 Load Test Results:")
    print(f"   Total requests: {stats.total.num_requests}")
    print(f"   Failures: {stats.total.num_failures}")
    print(f"   Requests/sec: {stats.total.total_rps:.2f}")
    print(f"   p50 latency: {stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"   p95 latency: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"   p99 latency: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print(f"   Max latency: {stats.total.max_response_time:.0f}ms")

    # Performance assertions (for CI/CD)
    p95_latency = stats.total.get_response_time_percentile(0.95)
    failure_rate = stats.total.num_failures / max(stats.total.num_requests, 1)

    if p95_latency > 500:
        print(f"   ⚠️  WARNING: p95 latency ({p95_latency:.0f}ms) exceeds target (500ms)")

    if failure_rate > 0.01:
        print(f"   ⚠️  WARNING: Failure rate ({failure_rate*100:.2f}%) exceeds target (1%)")
