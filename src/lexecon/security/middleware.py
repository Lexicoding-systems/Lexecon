"""
FastAPI middleware for authentication, authorization, rate limiting, and security headers.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Callable
from functools import wraps
import time

from lexecon.security.auth_service import AuthService, Permission, Session
from lexecon.security.rate_limiter import RateLimiter, RateLimitConfig


class AuthMiddleware:
    """Authentication middleware for FastAPI."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def __call__(self, request: Request, call_next):
        """Middleware to validate session on protected endpoints."""
        # Skip authentication for public endpoints
        public_endpoints = [
            "/health",
            "/login",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]

        if any(request.url.path.startswith(endpoint) for endpoint in public_endpoints):
            return await call_next(request)

        # Get session token from cookie or header
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not session_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Not authenticated", "message": "No session token provided"}
            )

        # Validate session
        session, error = self.auth_service.validate_session(session_id)
        if not session:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid session", "message": error}
            )

        # Attach session to request state
        request.state.session = session
        request.state.user_id = session.user_id
        request.state.username = session.username
        request.state.role = session.role

        return await call_next(request)


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission for an endpoint.

    Usage:
        @require_permission(Permission.EXPORT_DATA)
        async def some_endpoint(request: Request):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not hasattr(request.state, "session"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )

            session: Session = request.state.session
            auth_service = request.app.state.auth_service

            if not auth_service.has_permission(session.role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission.value}"
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_current_user(request: Request) -> Optional[dict]:
    """Helper to get current user from request."""
    if not hasattr(request.state, "session"):
        return None

    return {
        "user_id": request.state.user_id,
        "username": request.state.username,
        "role": request.state.role.value if hasattr(request.state.role, 'value') else str(request.state.role)
    }


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.

    Implements OWASP recommended security headers for enterprise applications.
    """

    def __init__(self, enable_csp: bool = True):
        self.enable_csp = enable_csp

    async def __call__(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy for privacy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (Feature-Policy successor)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # HSTS (HTTP Strict Transport Security) - only in production
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        if self.enable_csp:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline'",  # Allow inline scripts for dashboard
                "style-src 'self' 'unsafe-inline'",  # Allow inline styles
                "img-src 'self' data:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        return response


class RateLimitMiddleware:
    """
    Middleware to implement rate limiting on API endpoints.

    Protects against abuse and ensures fair resource usage.
    """

    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter

    async def __call__(self, request: Request, call_next):
        """Check rate limits before processing request."""
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        # Get client identifier (prefer user ID, fallback to IP)
        if hasattr(request.state, "user_id"):
            client_id = f"user:{request.state.user_id}"
        else:
            client_id = f"ip:{request.client.host}"

        # Check rate limit
        allowed, info = self.rate_limiter.check_rate_limit(client_id)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after_seconds": info.get("retry_after_seconds"),
                    "limit_minute": info["limit_minute"],
                    "limit_hour": info["limit_hour"],
                },
                headers={
                    "Retry-After": str(info.get("retry_after_seconds", 60)),
                    "X-RateLimit-Limit-Minute": str(info["limit_minute"]),
                    "X-RateLimit-Limit-Hour": str(info["limit_hour"]),
                    "X-RateLimit-Remaining-Minute": str(info["remaining_minute"]),
                    "X-RateLimit-Remaining-Hour": str(info["remaining_hour"]),
                }
            )

        # Add rate limit info to response headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit-Minute"] = str(info["limit_minute"])
        response.headers["X-RateLimit-Limit-Hour"] = str(info["limit_hour"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(info["remaining_minute"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(info["remaining_hour"])

        return response
