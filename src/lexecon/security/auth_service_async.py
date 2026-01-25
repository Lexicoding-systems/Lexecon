"""Async wrappers for AuthService database operations.

Provides async versions of blocking auth operations to prevent
blocking the event loop in async endpoints.

Uses asyncio.to_thread() to run blocking I/O in thread pool,
allowing concurrent request handling.
"""

import asyncio
from typing import List, Optional, Tuple

from .auth_service import AuthService, Permission, Role, Session, User


class AsyncAuthService:
    """Async wrapper around synchronous AuthService.

    All database operations run in thread pool to avoid blocking event loop.
    """

    def __init__(self, auth_service: AuthService):
        """Initialize with sync auth service instance.

        Args:
            auth_service: Sync AuthService instance to wrap
        """
        self.auth_service = auth_service

    async def authenticate(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """Async wrapper for authenticate.

        Args:
            username: Username
            password: Password
            ip_address: Client IP address

        Returns:
            Tuple of (User, error_message) or (None, error_message)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.authenticate,
            username,
            password,
            ip_address,
        )

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: Role,
        full_name: str,
    ) -> Tuple[Optional[User], Optional[str]]:
        """Async wrapper for create_user.

        Args:
            username: Username
            email: Email address
            password: Password
            role: User role
            full_name: Full name

        Returns:
            Tuple of (User, error_message) or (None, error_message)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.create_user,
            username,
            email,
            password,
            role,
            full_name,
        )

    async def create_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Session:
        """Async wrapper for create_session.

        Args:
            user: User object
            ip_address: Client IP address

        Returns:
            Session object
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.create_session,
            user,
            ip_address,
        )

    async def validate_session(
        self,
        session_id: str,
    ) -> Tuple[Optional[Session], Optional[str]]:
        """Async wrapper for validate_session.

        Args:
            session_id: Session ID to validate

        Returns:
            Tuple of (Session, error_message) or (None, error_message)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.validate_session,
            session_id,
        )

    async def revoke_session(self, session_id: str) -> None:
        """Async wrapper for revoke_session.

        Args:
            session_id: Session ID to revoke
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.auth_service.revoke_session,
            session_id,
        )

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Async wrapper for get_user_by_id.

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.get_user_by_id,
            user_id,
        )

    async def list_users(self) -> List[User]:
        """Async wrapper for list_users.

        Args:

        Returns:
            List of User objects
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.list_users,
        )

    async def get_active_sessions(
        self,
        user_id: Optional[str] = None,
    ) -> List[Session]:
        """Async wrapper for get_active_sessions.

        Args:
            user_id: Optional user ID filter

        Returns:
            List of active Session objects
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.get_active_sessions,
            user_id,
        )

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> Tuple[bool, Optional[str]]:
        """Async wrapper for change_password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            Tuple of (success, error_message)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.change_password,
            user_id,
            old_password,
            new_password,
        )

    async def get_password_status(self, user_id: str) -> dict:
        """Async wrapper for get_password_status.

        Args:
            user_id: User ID

        Returns:
            Password status dict
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.get_password_status,
            user_id,
        )

    async def get_user_mfa_status(self, user_id: str) -> dict:
        """Async wrapper for get_user_mfa_status.

        Args:
            user_id: User ID

        Returns:
            MFA status dict
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.get_user_mfa_status,
            user_id,
        )

    async def complete_mfa_login(
        self,
        user_id: str,
        totp_code: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[Optional[Session], Optional[str]]:
        """Async wrapper for complete_mfa_login.

        Args:
            user_id: User ID
            totp_code: TOTP code
            ip_address: Client IP address

        Returns:
            Tuple of (Session, error_message) or (None, error_message)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.auth_service.complete_mfa_login,
            user_id,
            totp_code,
            ip_address,
        )

    # Sync-only methods (no I/O blocking)
    def has_permission(self, role: Role, permission: Permission) -> bool:
        """Check if role has permission (sync, non-blocking).

        Args:
            role: User role
            permission: Permission to check

        Returns:
            True if role has permission
        """
        return self.auth_service.has_permission(role, permission)
