"""
Tests for security headers middleware.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from lexecon.security.middleware import SecurityHeadersMiddleware
from lexecon.security.rate_limiter import RateLimiter, RateLimitConfig


class TestSecurityHeadersMiddleware:
    """Tests for security headers middleware."""

    def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        app = FastAPI()
        app.middleware("http")(SecurityHeadersMiddleware())

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

    def test_csp_header_enabled(self):
        """Test Content Security Policy header when enabled."""
        app = FastAPI()
        app.middleware("http")(SecurityHeadersMiddleware(enable_csp=True))

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_csp_header_disabled(self):
        """Test Content Security Policy header when disabled."""
        app = FastAPI()
        app.middleware("http")(SecurityHeadersMiddleware(enable_csp=False))

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        assert "Content-Security-Policy" not in response.headers

    def test_hsts_not_added_for_http(self):
        """Test HSTS header not added for HTTP requests."""
        app = FastAPI()
        app.middleware("http")(SecurityHeadersMiddleware())

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # HSTS should not be present for HTTP
        assert "Strict-Transport-Security" not in response.headers

    def test_headers_on_http_error_responses(self):
        """Test security headers are added on HTTP error responses."""
        from fastapi import HTTPException

        app = FastAPI()
        app.middleware("http")(SecurityHeadersMiddleware())

        @app.get("/error")
        async def error_endpoint():
            raise HTTPException(status_code=400, detail="Bad request")

        client = TestClient(app)
        response = client.get("/error")

        # Should still have security headers on 4xx responses
        assert response.status_code == 400
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_headers_on_different_routes(self):
        """Test security headers added to all routes."""
        app = FastAPI()
        app.middleware("http")(SecurityHeadersMiddleware())

        @app.get("/route1")
        async def route1():
            return {"route": "1"}

        @app.post("/route2")
        async def route2():
            return {"route": "2"}

        client = TestClient(app)

        # Test GET
        response1 = client.get("/route1")
        assert "X-Frame-Options" in response1.headers

        # Test POST
        response2 = client.post("/route2")
        assert "X-Frame-Options" in response2.headers


class TestRateLimitMiddleware:
    """Tests for rate limit middleware."""

    def test_rate_limit_within_limits(self):
        """Test requests within rate limits are allowed."""
        from lexecon.security.middleware import RateLimitMiddleware

        app = FastAPI()
        rate_limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=10, burst_size=5)
        )
        app.middleware("http")(RateLimitMiddleware(rate_limiter))

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)

        # Should allow first few requests
        for i in range(3):
            response = client.get("/test")
            assert response.status_code == 200
            assert "X-RateLimit-Limit-Minute" in response.headers

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded returns 429."""
        from lexecon.security.middleware import RateLimitMiddleware

        app = FastAPI()
        rate_limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=10, burst_size=2)
        )
        app.middleware("http")(RateLimitMiddleware(rate_limiter))

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)

        # Exhaust rate limit
        client.get("/test")
        client.get("/test")

        # Should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert "retry_after_seconds" in response.json()
        assert "Retry-After" in response.headers

    def test_health_endpoint_bypasses_rate_limit(self):
        """Test health endpoint bypasses rate limiting."""
        from lexecon.security.middleware import RateLimitMiddleware

        app = FastAPI()
        rate_limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=10, burst_size=1)
        )
        app.middleware("http")(RateLimitMiddleware(rate_limiter))

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)

        # Exhaust regular limit
        client.get("/test")
        response = client.get("/test")
        assert response.status_code == 429

        # Health endpoint should still work
        health_response = client.get("/health")
        assert health_response.status_code == 200

    def test_rate_limit_headers_present(self):
        """Test rate limit headers are added to responses."""
        from lexecon.security.middleware import RateLimitMiddleware

        app = FastAPI()
        rate_limiter = RateLimiter()
        app.middleware("http")(RateLimitMiddleware(rate_limiter))

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Limit-Hour" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers

    def test_rate_limit_per_ip(self):
        """Test rate limiting is applied per IP address."""
        from lexecon.security.middleware import RateLimitMiddleware

        app = FastAPI()
        rate_limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=10, burst_size=1)
        )
        app.middleware("http")(RateLimitMiddleware(rate_limiter))

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)

        # First request should succeed
        response1 = client.get("/test")
        assert response1.status_code == 200

        # Second request should fail
        response2 = client.get("/test")
        assert response2.status_code == 429


class TestCombinedMiddleware:
    """Test security headers and rate limiting together."""

    def test_both_middleware_applied(self):
        """Test both middleware are applied correctly."""
        from lexecon.security.middleware import (
            RateLimitMiddleware,
            SecurityHeadersMiddleware,
        )

        app = FastAPI()
        rate_limiter = RateLimiter()
        app.middleware("http")(RateLimitMiddleware(rate_limiter))
        app.middleware("http")(SecurityHeadersMiddleware())

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # Should have both security headers and rate limit headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "X-RateLimit-Limit-Minute" in response.headers


class TestAuthMiddleware:
    """Tests for authentication middleware."""

    def test_public_endpoints_bypass_auth(self):
        """Test public endpoints bypass authentication."""
        from lexecon.security.middleware import AuthMiddleware
        from lexecon.security.auth_service import AuthService

        app = FastAPI()
        auth_service = AuthService()
        app.middleware("http")(AuthMiddleware(auth_service))

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        @app.get("/docs")
        async def docs():
            return {"docs": "here"}

        client = TestClient(app)

        # Health should be accessible without auth
        response = client.get("/health")
        assert response.status_code == 200

    def test_protected_endpoint_requires_auth(self):
        """Test protected endpoints require authentication."""
        from lexecon.security.middleware import AuthMiddleware
        from lexecon.security.auth_service import AuthService

        app = FastAPI()
        auth_service = AuthService()
        app.middleware("http")(AuthMiddleware(auth_service))

        @app.get("/api/protected")
        async def protected():
            return {"secret": "data"}

        client = TestClient(app)

        # Should return 401 without auth
        response = client.get("/api/protected")
        assert response.status_code == 401
        assert "error" in response.json()

    def test_protected_endpoint_with_invalid_session(self):
        """Test protected endpoints reject invalid sessions."""
        from lexecon.security.middleware import AuthMiddleware
        from lexecon.security.auth_service import AuthService

        app = FastAPI()
        auth_service = AuthService()
        app.middleware("http")(AuthMiddleware(auth_service))

        @app.get("/api/protected")
        async def protected():
            return {"secret": "data"}

        client = TestClient(app)

        # Should return 401 with invalid session
        response = client.get(
            "/api/protected",
            headers={"Authorization": "Bearer invalid_session_id"}
        )
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_session(self):
        """Test protected endpoints accept valid sessions."""
        import uuid
        from lexecon.security.middleware import AuthMiddleware
        from lexecon.security.auth_service import AuthService, Role

        app = FastAPI()
        auth_service = AuthService()
        app.middleware("http")(AuthMiddleware(auth_service))

        # Create a unique test user and authenticate
        unique_id = uuid.uuid4().hex[:8]
        username = f"testuser_{unique_id}"
        email = f"test_{unique_id}@example.com"

        auth_service.create_user(
            username=username,
            password="TestPass123!",
            email=email,
            full_name="Test User",
            role=Role.VIEWER
        )

        # Authenticate and get session
        user, error = auth_service.authenticate(username, "TestPass123!")
        assert user is not None, f"Authentication failed: {error}"
        session = auth_service.create_session(user)
        session_id = session.session_id

        @app.get("/api/protected")
        async def protected(request: Request):
            return {"user": request.state.username}

        client = TestClient(app)

        # Should succeed with valid session
        response = client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {session_id}"}
        )
        assert response.status_code == 200
        assert response.json()["user"] == username


class TestGetCurrentUser:
    """Tests for get_current_user helper."""

    def test_get_current_user_no_session(self):
        """Test get_current_user returns None without session."""
        from lexecon.security.middleware import get_current_user
        from unittest.mock import MagicMock

        request = MagicMock()
        del request.state.session

        result = get_current_user(request)
        assert result is None

    def test_get_current_user_with_session(self):
        """Test get_current_user returns user info with session."""
        from lexecon.security.middleware import get_current_user
        from lexecon.security.auth_service import Role
        from unittest.mock import MagicMock

        request = MagicMock()
        request.state.session = True
        request.state.user_id = "user123"
        request.state.username = "testuser"
        request.state.role = Role.ADMIN

        result = get_current_user(request)
        assert result["user_id"] == "user123"
        assert result["username"] == "testuser"
        assert result["role"] == "admin"
