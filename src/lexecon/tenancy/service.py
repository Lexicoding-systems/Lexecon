"""Multi-tenancy Service - Minimum viable tenant isolation.

Features:
- Tenant table with metadata
- Tenant-user membership table
- Row-level isolation via tenant_id columns
- Middleware validates user membership in tenant
"""

import sqlite3
from typing import List, Optional, Tuple


class TenancyService:
    """Manages tenant isolation and membership."""

    def __init__(self, db_path: str = "lexecon_auth.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self) -> None:
        """Initialize tenancy tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Tenants table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tenant-users membership table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_users (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT DEFAULT 'member',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, user_id),
                    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
                )
            """)
            
            # Create default tenant if not exists
            conn.execute("""
                INSERT OR IGNORE INTO tenants (tenant_id, name)
                VALUES ('default', 'Default Tenant')
            """)
            
            conn.commit()

    def create_tenant(self, tenant_id: str, name: str) -> bool:
        """Create a new tenant."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO tenants (tenant_id, name) VALUES (?, ?)",
                    (tenant_id, name)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def add_user_to_tenant(self, tenant_id: str, user_id: str, role: str = "member") -> bool:
        """Add a user to a tenant."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO tenant_users (tenant_id, user_id, role) VALUES (?, ?, ?)",
                    (tenant_id, user_id, role)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def is_user_in_tenant(self, user_id: str, tenant_id: str) -> bool:
        """Check if user is a member of the tenant."""
        # Default tenant allows all users
        if tenant_id == "default":
            return True
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM tenant_users WHERE tenant_id = ? AND user_id = ?",
                (tenant_id, user_id)
            )
            return cursor.fetchone() is not None

    def get_user_tenants(self, user_id: str) -> List[dict]:
        """Get all tenants a user belongs to."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT t.tenant_id, t.name, tu.role
                FROM tenants t
                JOIN tenant_users tu ON t.tenant_id = tu.tenant_id
                WHERE tu.user_id = ?
                """,
                (user_id,)
            )
            rows = cursor.fetchall()
            return [
                {"tenant_id": r[0], "name": r[1], "role": r[2]}
                for r in rows
            ]

    def get_tenant_users(self, tenant_id: str) -> List[dict]:
        """Get all users in a tenant."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT user_id, role FROM tenant_users WHERE tenant_id = ?",
                (tenant_id,)
            )
            rows = cursor.fetchall()
            return [
                {"user_id": r[0], "role": r[1]}
                for r in rows
            ]

    def ensure_default_tenant_membership(self, user_id: str) -> None:
        """Ensure user is member of default tenant (for migration)."""
        self.add_user_to_tenant("default", user_id, "member")
