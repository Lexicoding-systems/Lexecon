"""Rate Limiting Middleware for FastAPI.

Provides HTTP-level rate limiting with automatic 429 responses.
Integrates with RateLimiter for token bucket-based rate limiting.

Features:
- Global per-IP rate limiting
- Endpoint-specific rate limits
- Automatic Retry-After headers
- Graceful bypass for internal endpoints
"""

from typing import Callable, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from lexecon.security.rate_limiter import get_rate_limiter


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting.

    Applies rate limits based on client IP and request endpoint.
    Returns HTTP 429 with Retry-After header when limits exceeded.
    """

    def __init__(self):
        """Initialize rate limiting middleware."""
        self.rate_limiter = get_rate_limiter()

        # Endpoints that bypass rate limiting
        self.bypass_endpoints = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
        }

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response (may be 429 if rate limited)
        """
        # Get client IP
        ip_address = self._get_client_ip(request)

        # Check if endpoint should bypass rate limiting
        if self._should_bypass(request):
            return await call_next(request)

        # Apply global per-IP rate limit
        allowed, retry_after = self.rate_limiter.check_rate_limit(
            f"ip:{ip_address}",
            "global_per_ip",
        )

        if not allowed:
            return self._rate_limit_response(
                "Too many requests from your IP address",
                retry_after,
            )

        # Apply endpoint-specific rate limits
        endpoint_limit_type = self._get_endpoint_limit_type(request)

        if endpoint_limit_type:
            key = self._get_rate_limit_key(request, endpoint_limit_type)

            allowed, retry_after = self.rate_limiter.check_rate_limit(
                key,
                endpoint_limit_type,
            )

            if not allowed:
                return self._rate_limit_response(
                    f"Too many requests to {request.url.path}",
                    retry_after,
                )

            # Consume token for this endpoint
            self.rate_limiter.consume(key, endpoint_limit_type)

        # Consume token for global limit
        self.rate_limiter.consume(f"ip:{ip_address}", "global_per_ip")

        # Add rate limit headers to response
        response = await call_next(request)
        self._add_rate_limit_headers(response, ip_address, endpoint_limit_type)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.

        Handles X-Forwarded-For and X-Real-IP headers for proxied requests.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (load balancers, proxies)
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # Take first IP in list (original client)
            return x_forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip.strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _should_bypass(self, request: Request) -> bool:
        """Check if endpoint should bypass rate limiting.

        Args:
            request: FastAPI request object

        Returns:
            True if should bypass rate limiting
        """
        path = request.url.path

        # Check exact match
        if path in self.bypass_endpoints:
            return True

        # Check prefix match
        return any(path.startswith(bypass_path) for bypass_path in self.bypass_endpoints)

    def _get_endpoint_limit_type(self, request: Request) -> Optional[str]:
        """Determine rate limit type based on endpoint.

        Args:
            request: FastAPI request object

        Returns:
            Rate limit type key or None
        """
        path = request.url.path
        method = request.method

        # Authentication endpoints
        if path == "/auth/login":
            return "auth_login_per_ip"

        if path.startswith("/auth/mfa/") and "verify" in path:
            return "auth_mfa_per_challenge"

        if path == "/auth/users" and method == "POST":
            return "auth_register_per_ip"

        # Password management
        if path == "/auth/change-password":
            return "password_change_per_user"

        if path.startswith("/auth/password-reset"):
            return "password_reset_per_email"

        # Export endpoints
        if "/export" in path or "/audit-export" in path:
            return "api_export_per_user"

        # No specific endpoint limit
        return None

    def _get_rate_limit_key(self, request: Request, limit_type: str) -> str:
        """Generate rate limit key for request.

        Args:
            request: FastAPI request object
            limit_type: Type of rate limit

        Returns:
            Unique rate limit key
        """
        ip_address = self._get_client_ip(request)
        path = request.url.path

        # Per-user limits require authentication
        if "_per_user" in limit_type:
            # Try to get user from request state (set by AuthMiddleware)
            if hasattr(request.state, "user_id"):
                return f"user:{request.state.user_id}"
            # Fall back to IP if user not authenticated
            return f"ip:{ip_address}"

        # Per-challenge limits (MFA)
        if "per_challenge" in limit_type:
            # Extract challenge_id from request body or query params
            # For now, use IP + endpoint
            return f"ip:{ip_address}:{path}"

        # Per-email limits (password reset)
        if "per_email" in limit_type:
            # Would need to extract email from request
            # For now, use IP + endpoint
            return f"ip:{ip_address}:{path}"

        # Default: IP + endpoint
        return f"ip:{ip_address}:{path}"

    def _rate_limit_response(self, message: str, retry_after: Optional[int]) -> JSONResponse:
        """Create rate limit error response.

        Args:
            message: Error message
            retry_after: Seconds until retry allowed

        Returns:
            JSON response with 429 status
        """
        retry_after = retry_after or 60

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": message,
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    def _add_rate_limit_headers(
        self,
        response: Response,
        ip_address: str,
        endpoint_limit_type: Optional[str],
    ) -> None:
        """Add rate limit information to response headers.

        Args:
            response: FastAPI response object
            ip_address: Client IP address
            endpoint_limit_type: Type of endpoint-specific limit (if any)
        """
        # Add global rate limit headers
        remaining = self.rate_limiter.get_remaining(
            f"ip:{ip_address}",
            "global_per_ip",
        )

        if remaining >= 0:
            response.headers["X-RateLimit-Limit"] = "100"
            response.headers["X-RateLimit-Remaining"] = str(remaining)

        # Add endpoint-specific headers if applicable
        if endpoint_limit_type:
            capacity, _ = self.rate_limiter.limits.get(endpoint_limit_type, (0, 0))
            if capacity > 0:
                response.headers["X-RateLimit-Endpoint-Limit"] = str(capacity)


def create_rate_limit_middleware() -> RateLimitMiddleware:
    """Create rate limiting middleware instance.

    Returns:
        Configured RateLimitMiddleware
    """
    return RateLimitMiddleware()
