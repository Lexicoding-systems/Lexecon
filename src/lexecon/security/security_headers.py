"""Security Headers Middleware for FastAPI.

Adds comprehensive security headers to all HTTP responses to protect against
common web vulnerabilities:
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME type sniffing
- Information leakage
- Protocol downgrade attacks

Implements OWASP security best practices.
"""

import os
from typing import Callable, Dict, Optional

from fastapi import Request, Response


class SecurityHeadersMiddleware:
    """FastAPI middleware that adds security headers to all responses.

    Headers added:
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer-Policy
    - Permissions-Policy
    - X-XSS-Protection (legacy browsers)
    - Cache-Control (for sensitive pages)
    """

    def __init__(self, config: Optional[Dict[str, str]] = None):
        """Initialize security headers middleware.

        Args:
            config: Optional custom header configuration
        """
        self.env = os.getenv("LEXECON_ENV", "development")
        self.config = config or self._default_headers()

    def _default_headers(self) -> Dict[str, str]:
        """Get default security headers configuration.

        Returns:
            Dictionary of header name to value
        """
        headers = {}

        # HSTS: Force HTTPS for 1 year (only in production)
        if self.env == "production":
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # CSP: Restrict content sources
        # Note: 'unsafe-inline' allowed for scripts/styles in login.html
        # In production, consider using nonces for inline scripts
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # X-Frame-Options: Prevent clickjacking
        headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevent MIME sniffing
        headers["X-Content-Type-Options"] = "nosniff"

        # Referrer-Policy: Control referrer information
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Restrict browser features
        headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # X-XSS-Protection: Legacy XSS protection (for older browsers)
        headers["X-XSS-Protection"] = "1; mode=block"

        # X-DNS-Prefetch-Control: Disable DNS prefetching
        headers["X-DNS-Prefetch-Control"] = "off"

        # X-Download-Options: Prevent untrusted downloads
        headers["X-Download-Options"] = "noopen"

        # X-Permitted-Cross-Domain-Policies: Restrict cross-domain policies
        headers["X-Permitted-Cross-Domain-Policies"] = "none"

        return headers

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers to response.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response with security headers
        """
        # Process request
        response = await call_next(request)

        # Add security headers to response
        for header, value in self.config.items():
            response.headers[header] = value

        # Add cache control headers for sensitive pages
        if self._is_sensitive_page(request):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    def _is_sensitive_page(self, request: Request) -> bool:
        """Check if request is for a sensitive page that should not be cached.

        Args:
            request: FastAPI request object

        Returns:
            True if page is sensitive
        """
        path = request.url.path

        # Authentication pages
        if path.startswith("/auth/"):
            return True

        # User management pages
        if "/users" in path:
            return True

        # Admin pages
        if "/admin" in path:
            return True

        # API endpoints with personal data
        if path.startswith("/api/") and any(
            sensitive in path
            for sensitive in ["user", "profile", "session", "mfa", "password"]
        ):
            return True

        # Export and audit pages
        return bool(any(word in path for word in ["export", "audit", "evidence"]))


def create_security_headers_middleware(
    config: Optional[Dict[str, str]] = None,
) -> SecurityHeadersMiddleware:
    """Create security headers middleware instance.

    Args:
        config: Optional custom header configuration

    Returns:
        Configured SecurityHeadersMiddleware
    """
    return SecurityHeadersMiddleware(config)


def get_recommended_csp_for_environment(env: str = "production") -> str:
    """Get recommended Content-Security-Policy for environment.

    Args:
        env: Environment name (development, production)

    Returns:
        CSP header value
    """
    if env == "development":
        # More permissive for development
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https: http:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )
    # Strict for production
    return (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "upgrade-insecure-requests"
    )
