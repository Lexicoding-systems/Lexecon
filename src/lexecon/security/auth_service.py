"""Authentication and Authorization Service.

Provides:
- User management with password hashing
- Role-based access control (RBAC)
- Session management with timeout
- Failed login tracking
- Multi-factor authentication support (future)
"""

import hashlib
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, Tuple


class Role(str, Enum):
    """User roles with hierarchical permissions."""
    VIEWER = "viewer"  # Can view dashboard only
    AUDITOR = "auditor"  # Can generate audit packets (needs approval)
    COMPLIANCE_OFFICER = "compliance_officer"  # Can approve audit requests
    ADMIN = "admin"  # Full system access


class Permission(str, Enum):
    """Granular permissions."""
    VIEW_DASHBOARD = "view_dashboard"
    REQUEST_AUDIT_PACKET = "request_audit_packet"
    APPROVE_AUDIT_PACKET = "approve_audit_packet"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_DATA = "export_data"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.VIEWER: [
        Permission.VIEW_DASHBOARD,
    ],
    Role.AUDITOR: [
        Permission.VIEW_DASHBOARD,
        Permission.REQUEST_AUDIT_PACKET,
        Permission.VIEW_AUDIT_LOGS,
    ],
    Role.COMPLIANCE_OFFICER: [
        Permission.VIEW_DASHBOARD,
        Permission.REQUEST_AUDIT_PACKET,
        Permission.APPROVE_AUDIT_PACKET,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_DATA,
    ],
    Role.ADMIN: [
        Permission.VIEW_DASHBOARD,
        Permission.REQUEST_AUDIT_PACKET,
        Permission.APPROVE_AUDIT_PACKET,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_DATA,
    ],
}


@dataclass
class User:
    """User entity."""
    user_id: str
    username: str
    email: str
    role: Role
    full_name: str
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None


@dataclass
class Session:
    """User session."""
    session_id: str
    user_id: str
    username: str
    role: Role
    created_at: str
    expires_at: str
    last_activity: str
    ip_address: Optional[str] = None


class AuthService:
    """Authentication and authorization service."""

    def __init__(self, db_path: str = "lexecon_auth.db"):
        """Initialize authentication service."""
        self.db_path = db_path
        self.session_timeout_minutes = 15
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self._init_database()

    def _init_database(self) -> None:
        """Initialize authentication database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TEXT
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                ip_address TEXT,
                revoked INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Login attempts log (for security monitoring)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                attempt_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                success INTEGER NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT NOT NULL,
                failure_reason TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using PBKDF2."""
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,  # iterations
        ).hex()

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: Role,
        full_name: str,
    ) -> User:
        """Create a new user with password policy validation."""
        # Validate password against policy (Phase 1C)
        from lexecon.security.password_policy import get_default_policy
        policy = get_default_policy()
        is_valid, errors = policy.validate_password(password)

        if not is_valid:
            raise ValueError(f"Password does not meet policy requirements: {'; '.join(errors)}")

        user_id = f"user_{secrets.token_hex(16)}"
        salt = secrets.token_hex(32)
        password_hash = self._hash_password(password, salt)
        created_at = datetime.now(timezone.utc).isoformat()

        # Calculate password expiration if policy requires it
        password_expires_at = None
        if policy.max_age_days:
            expires = datetime.now(timezone.utc) + timedelta(days=policy.max_age_days)
            password_expires_at = expires.isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (
                    user_id, username, email, password_hash, salt,
                    role, full_name, created_at, password_changed_at, password_expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, email, password_hash, salt,
                  role.value, full_name, created_at, created_at, password_expires_at))

            # Store initial password in history
            history_id = f"hist_{secrets.token_hex(16)}"
            cursor.execute("""
                INSERT INTO password_history (history_id, user_id, password_hash, changed_at)
                VALUES (?, ?, ?, ?)
            """, (history_id, user_id, password_hash, created_at))

            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.close()
            raise ValueError(f"User creation failed: {e}")

        conn.close()

        return User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            full_name=full_name,
            created_at=created_at,
        )

    def authenticate(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate user and return (User, error_message).

        Returns:
            (User, None) on success
            (None, error_message) on failure
        """
        attempt_id = f"attempt_{secrets.token_hex(16)}"
        timestamp = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get user
        cursor.execute("""
            SELECT user_id, username, email, password_hash, salt, role,
                   full_name, created_at, last_login, is_active,
                   failed_login_attempts, locked_until
            FROM users
            WHERE username = ?
        """, (username,))

        row = cursor.fetchone()

        if not row:
            # Log failed attempt
            cursor.execute("""
                INSERT INTO login_attempts (
                    attempt_id, username, success, ip_address, timestamp, failure_reason
                ) VALUES (?, ?, 0, ?, ?, ?)
            """, (attempt_id, username, ip_address, timestamp, "user_not_found"))
            conn.commit()
            conn.close()
            return None, "Invalid username or password"

        (user_id, username, email, password_hash, salt, role_str,
         full_name, created_at, _last_login, is_active,
         failed_attempts, locked_until) = row

        # Check if account is locked
        if locked_until:
            lock_time = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) < lock_time:
                remaining = (lock_time - datetime.now(timezone.utc)).seconds // 60
                cursor.execute("""
                    INSERT INTO login_attempts (
                        attempt_id, username, success, ip_address, timestamp, failure_reason
                    ) VALUES (?, ?, 0, ?, ?, ?)
                """, (attempt_id, username, ip_address, timestamp, f"account_locked_{remaining}min"))
                conn.commit()
                conn.close()
                return None, f"Account locked. Try again in {remaining} minutes."
            # Unlock account
            cursor.execute("""
                    UPDATE users
                    SET locked_until = NULL, failed_login_attempts = 0
                    WHERE user_id = ?
                """, (user_id,))
            conn.commit()

        # Check if account is active
        if not is_active:
            cursor.execute("""
                INSERT INTO login_attempts (
                    attempt_id, username, success, ip_address, timestamp, failure_reason
                ) VALUES (?, ?, 0, ?, ?, ?)
            """, (attempt_id, username, ip_address, timestamp, "account_disabled"))
            conn.commit()
            conn.close()
            return None, "Account is disabled"

        # Verify password
        computed_hash = self._hash_password(password, salt)
        if computed_hash != password_hash:
            # Increment failed attempts
            new_failed_attempts = failed_attempts + 1
            cursor.execute("""
                UPDATE users
                SET failed_login_attempts = ?
                WHERE user_id = ?
            """, (new_failed_attempts, user_id))

            # Lock account if too many failed attempts
            if new_failed_attempts >= self.max_failed_attempts:
                lock_until = (datetime.now(timezone.utc) +
                             timedelta(minutes=self.lockout_duration_minutes)).isoformat()
                cursor.execute("""
                    UPDATE users
                    SET locked_until = ?
                    WHERE user_id = ?
                """, (lock_until, user_id))
                failure_reason = "invalid_password_account_locked"
            else:
                failure_reason = "invalid_password"

            cursor.execute("""
                INSERT INTO login_attempts (
                    attempt_id, username, success, ip_address, timestamp, failure_reason
                ) VALUES (?, ?, 0, ?, ?, ?)
            """, (attempt_id, username, ip_address, timestamp, failure_reason))
            conn.commit()
            conn.close()

            remaining_attempts = self.max_failed_attempts - new_failed_attempts
            if remaining_attempts > 0:
                return None, f"Invalid password. {remaining_attempts} attempts remaining."
            return None, f"Account locked for {self.lockout_duration_minutes} minutes due to too many failed attempts."

        # Successful login
        # Check if MFA is enabled
        cursor.execute("""
            SELECT mfa_enabled
            FROM users
            WHERE user_id = ?
        """, (user_id,))

        mfa_row = cursor.fetchone()
        mfa_enabled = bool(mfa_row[0]) if mfa_row else False

        # Reset failed attempts (but don't update last_login yet if MFA is required)
        cursor.execute("""
            UPDATE users
            SET failed_login_attempts = 0
            WHERE user_id = ?
        """, (user_id,))

        # Log successful password verification
        cursor.execute("""
            INSERT INTO login_attempts (
                attempt_id, username, success, ip_address, timestamp, failure_reason
            ) VALUES (?, ?, 1, ?, ?, NULL)
        """, (attempt_id, username, ip_address, timestamp))

        conn.commit()
        conn.close()

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=Role(role_str),
            full_name=full_name,
            created_at=created_at,
            last_login=timestamp,
            is_active=bool(is_active),
            failed_login_attempts=0,
        )

        # If MFA is enabled, return special error to trigger MFA challenge
        if mfa_enabled:
            return user, "mfa_required"

        # Update last_login for non-MFA users
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET last_login = ?
            WHERE user_id = ?
        """, (timestamp, user_id))
        conn.commit()
        conn.close()

        return user, None

    def create_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Session:
        """Create a new session for authenticated user."""
        session_id = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.session_timeout_minutes)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions (
                session_id, user_id, created_at, expires_at, last_activity, ip_address
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, user.user_id, now.isoformat(), expires_at.isoformat(),
              now.isoformat(), ip_address))

        conn.commit()
        conn.close()

        return Session(
            session_id=session_id,
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            last_activity=now.isoformat(),
            ip_address=ip_address,
        )

    def validate_session(self, session_id: str) -> Tuple[Optional[Session], Optional[str]]:
        """Validate session and return (Session, error_message).

        Returns:
            (Session, None) if valid
            (None, error_message) if invalid
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.session_id, s.user_id, s.created_at, s.expires_at,
                   s.last_activity, s.ip_address, s.revoked,
                   u.username, u.role
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_id = ?
        """, (session_id,))

        row = cursor.fetchone()

        if not row:
            conn.close()
            return None, "Invalid session"

        (sid, user_id, created_at, expires_at, _last_activity,
         ip_address, revoked, username, role_str) = row

        if revoked:
            conn.close()
            return None, "Session revoked"

        # Check expiration
        expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            conn.close()
            return None, "Session expired"

        # Update last activity and extend session
        now = datetime.now(timezone.utc)
        new_expires = now + timedelta(minutes=self.session_timeout_minutes)

        cursor.execute("""
            UPDATE sessions
            SET last_activity = ?, expires_at = ?
            WHERE session_id = ?
        """, (now.isoformat(), new_expires.isoformat(), session_id))

        conn.commit()
        conn.close()

        return Session(
            session_id=sid,
            user_id=user_id,
            username=username,
            role=Role(role_str),
            created_at=created_at,
            expires_at=new_expires.isoformat(),
            last_activity=now.isoformat(),
            ip_address=ip_address,
        ), None

    def revoke_session(self, session_id: str):
        """Revoke a session (logout)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sessions
            SET revoked = 1
            WHERE session_id = ?
        """, (session_id,))

        conn.commit()
        conn.close()

    def has_permission(self, role: Role, permission: Permission) -> bool:
        """Check if role has permission."""
        return permission in ROLE_PERMISSIONS.get(role, [])

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, email, role, full_name, created_at,
                   last_login, is_active, failed_login_attempts, locked_until
            FROM users
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return User(
            user_id=row[0],
            username=row[1],
            email=row[2],
            role=Role(row[3]),
            full_name=row[4],
            created_at=row[5],
            last_login=row[6],
            is_active=bool(row[7]),
            failed_login_attempts=row[8],
            locked_until=row[9],
        )

    def list_users(self) -> List[User]:
        """List all users."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, email, role, full_name, created_at,
                   last_login, is_active, failed_login_attempts, locked_until
            FROM users
            ORDER BY created_at DESC
        """)

        users = []
        for row in cursor.fetchall():
            users.append(User(
                user_id=row[0],
                username=row[1],
                email=row[2],
                role=Role(row[3]),
                full_name=row[4],
                created_at=row[5],
                last_login=row[6],
                is_active=bool(row[7]),
                failed_login_attempts=row[8],
                locked_until=row[9],
            ))

        conn.close()
        return users

    def get_active_sessions(self, user_id: Optional[str] = None) -> List[Session]:
        """Get active sessions, optionally filtered by user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if user_id:
            cursor.execute("""
                SELECT s.session_id, s.user_id, s.created_at, s.expires_at,
                       s.last_activity, s.ip_address, u.username, u.role
                FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.user_id = ? AND s.revoked = 0 AND s.expires_at > ?
                ORDER BY s.last_activity DESC
            """, (user_id, datetime.now(timezone.utc).isoformat()))
        else:
            cursor.execute("""
                SELECT s.session_id, s.user_id, s.created_at, s.expires_at,
                       s.last_activity, s.ip_address, u.username, u.role
                FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.revoked = 0 AND s.expires_at > ?
                ORDER BY s.last_activity DESC
            """, (datetime.now(timezone.utc).isoformat(),))

        sessions = []
        for row in cursor.fetchall():
            sessions.append(Session(
                session_id=row[0],
                user_id=row[1],
                created_at=row[2],
                expires_at=row[3],
                last_activity=row[4],
                ip_address=row[5],
                username=row[6],
                role=Role(row[7]),
            ))

        conn.close()
        return sessions

    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> bool:
        """Change user's password with policy validation.

        Args:
            user_id: User ID
            old_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed successfully

        Raises:
            ValueError: If old password incorrect or new password invalid
        """
        from lexecon.security.password_policy import get_default_policy

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get user details
            cursor.execute("""
                SELECT password_hash, salt, username
                FROM users
                WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if not row:
                raise ValueError("User not found")

            current_hash, salt, username = row

            # Verify old password
            old_hash = self._hash_password(old_password, salt)
            if old_hash != current_hash:
                # Log failed password change attempt
                self._log_security_event(
                    "password_change_failed",
                    user_id=user_id,
                    details={"reason": "incorrect_old_password"},
                )
                raise ValueError("Current password is incorrect")

            # Validate new password against policy
            policy = get_default_policy()
            is_valid, errors = policy.validate_password(new_password)

            if not is_valid:
                raise ValueError(f"New password does not meet policy requirements: {'; '.join(errors)}")

            # Check password history (last N passwords)
            cursor.execute("""
                SELECT password_hash
                FROM password_history
                WHERE user_id = ?
                ORDER BY changed_at DESC
                LIMIT ?
            """, (user_id, policy.history_count))

            password_history = [row[0] for row in cursor.fetchall()]

            if not policy.check_password_history(new_password, salt, password_history):
                raise ValueError(
                    f"Password was used recently. Please choose a password you haven't used in your last {policy.history_count} passwords.",
                )

            # Hash new password
            new_hash = self._hash_password(new_password, salt)

            # Calculate new expiration date
            changed_at = datetime.now(timezone.utc).isoformat()
            expires_at = None
            if policy.max_age_days:
                expires = datetime.now(timezone.utc) + timedelta(days=policy.max_age_days)
                expires_at = expires.isoformat()

            # Update password in users table
            cursor.execute("""
                UPDATE users
                SET password_hash = ?,
                    password_changed_at = ?,
                    password_expires_at = ?,
                    force_password_change = 0
                WHERE user_id = ?
            """, (new_hash, changed_at, expires_at, user_id))

            # Add new password to history
            history_id = f"hist_{secrets.token_hex(16)}"
            cursor.execute("""
                INSERT INTO password_history (history_id, user_id, password_hash, changed_at)
                VALUES (?, ?, ?, ?)
            """, (history_id, user_id, new_hash, changed_at))

            # Clean up old history entries (keep only last N)
            cursor.execute("""
                DELETE FROM password_history
                WHERE user_id = ?
                AND history_id NOT IN (
                    SELECT history_id
                    FROM password_history
                    WHERE user_id = ?
                    ORDER BY changed_at DESC
                    LIMIT ?
                )
            """, (user_id, user_id, policy.history_count))

            conn.commit()

            # Log successful password change
            self._log_security_event(
                "password_changed",
                user_id=user_id,
                details={"username": username},
            )

            return True

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_password_status(self, user_id: str) -> dict:
        """Get password status for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with password status information:
            - password_changed_at: When password was last changed
            - password_expires_at: When password expires (or None)
            - days_until_expiration: Days until expiration (or None)
            - is_expired: Whether password is currently expired
            - force_password_change: Whether user must change password
            - password_age_days: Age of current password in days

        Raises:
            ValueError: If user not found
        """
        from lexecon.security.password_policy import get_default_policy

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT password_changed_at, password_expires_at, force_password_change
                FROM users
                WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if not row:
                raise ValueError("User not found")

            password_changed_at, password_expires_at, force_password_change = row

            # Calculate password age
            password_age_days = None
            if password_changed_at:
                try:
                    changed_dt = datetime.fromisoformat(password_changed_at.replace("Z", "+00:00"))
                    age = datetime.now(timezone.utc) - changed_dt
                    password_age_days = age.days
                except (ValueError, AttributeError):
                    pass

            # Check expiration
            policy = get_default_policy()
            is_expired = False
            days_until_expiration = None

            if password_changed_at:
                is_expired = policy.is_password_expired(password_changed_at)
                days_until_expiration = policy.days_until_expiration(password_changed_at)

            return {
                "password_changed_at": password_changed_at,
                "password_expires_at": password_expires_at,
                "days_until_expiration": days_until_expiration,
                "is_expired": is_expired,
                "force_password_change": bool(force_password_change),
                "password_age_days": password_age_days,
                "policy": {
                    "min_length": policy.min_length,
                    "max_age_days": policy.max_age_days,
                    "history_count": policy.history_count,
                    "require_uppercase": policy.require_uppercase,
                    "require_lowercase": policy.require_lowercase,
                    "require_digits": policy.require_digits,
                    "require_special": policy.require_special,
                },
            }

        finally:
            conn.close()

    def complete_mfa_login(
        self,
        user_id: str,
        totp_code: str,
    ) -> Tuple[Optional[User], Optional[str]]:
        """Complete MFA login with TOTP code.

        Args:
            user_id: User ID
            totp_code: 6-digit TOTP code

        Returns:
            Tuple of (user, error)
        """
        from lexecon.security.db_encryption import get_db_encryption
        from lexecon.security.mfa_service import get_mfa_service

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get user MFA secret
            cursor.execute("""
                SELECT user_id, username, email, role, full_name, created_at,
                       last_login, is_active, mfa_secret
                FROM users
                WHERE user_id = ? AND mfa_enabled = 1
            """, (user_id,))

            row = cursor.fetchone()
            if not row:
                return None, "MFA not enabled for user"

            (user_id, username, email, role_str, full_name, created_at,
             _last_login, is_active, encrypted_secret) = row

            # Decrypt MFA secret
            db_encryption = get_db_encryption()
            secret = db_encryption.decrypt_field(encrypted_secret)

            # Verify TOTP code
            mfa_service = get_mfa_service()
            if not mfa_service.verify_totp(secret, totp_code):
                return None, "Invalid MFA code"

            # Update last_login
            timestamp = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                UPDATE users
                SET last_login = ?
                WHERE user_id = ?
            """, (timestamp, user_id))

            conn.commit()

            user = User(
                user_id=user_id,
                username=username,
                email=email,
                role=Role(role_str),
                full_name=full_name,
                created_at=created_at,
                last_login=timestamp,
                is_active=bool(is_active),
                failed_login_attempts=0,
            )

            return user, None

        except Exception as e:
            return None, f"MFA verification failed: {e!s}"

        finally:
            conn.close()

    def get_user_mfa_status(self, user_id: str) -> dict:
        """Get MFA status for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with MFA status
        """
        from lexecon.security.mfa_service import get_mfa_service

        mfa_service = get_mfa_service()
        return mfa_service.get_mfa_status(user_id)
