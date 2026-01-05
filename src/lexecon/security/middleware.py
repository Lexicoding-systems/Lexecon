"""
FastAPI middleware for authentication and authorization.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Callable
from functools import wraps

from lexecon.security.auth_service import AuthService, Permission, Session


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
