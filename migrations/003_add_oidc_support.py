#!/usr/bin/env python3
"""
Migration: Add OIDC OAuth support.

Creates tables for OpenID Connect authentication:
- oidc_states: CSRF protection for OAuth flow
- oidc_users: Provider mappings for users

Run: python migrations/003_add_oidc_support.py [db_path]
"""

import sqlite3
import sys
from datetime import datetime, timezone


def migrate(db_path="lexecon_auth.db"):
    """
    Apply OIDC migration to database.

    Args:
        db_path: Path to authentication database
    """
    print(f"Applying OIDC migration to {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create oidc_states table for CSRF protection
        print("\n[1/3] Creating oidc_states table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oidc_states (
                state TEXT PRIMARY KEY,
                nonce TEXT NOT NULL,
                provider_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        print("  ✓ Created oidc_states table")

        # Create oidc_users table for provider mappings
        print("\n[2/3] Creating oidc_users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oidc_users (
                mapping_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider_name TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                provider_email TEXT,
                linked_at TEXT NOT NULL,
                last_login TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(provider_name, provider_user_id)
            )
        """)
        print("  ✓ Created oidc_users table")

        # Create index for efficient lookups
        print("\n[3/3] Creating index on oidc_users...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oidc_users_lookup
            ON oidc_users(provider_name, provider_user_id)
        """)
        print("  ✓ Created index idx_oidc_users_lookup")

        # Commit all changes
        conn.commit()

        print("\n" + "=" * 60)
        print("✓ OIDC migration completed successfully!")
        print("=" * 60)
        print("\nDatabase changes:")
        print("  • Created oidc_states table")
        print("  • Created oidc_users table")
        print("  • Created index on oidc_users")
        print("\nOIDC features now available:")
        print("  • Generic OIDC provider support")
        print("  • Authorization code flow with PKCE")
        print("  • ID token verification with JWKS")
        print("  • Automatic user provisioning")
        print("  • Account linking by email")
        print("\nSupported providers:")
        print("  • Google")
        print("  • Azure AD / Microsoft")
        print("  • Okta")
        print("  • Auth0")
        print("  • Any OIDC-compliant provider")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        raise

    finally:
        conn.close()


def verify_migration(db_path="lexecon_auth.db"):
    """
    Verify migration was applied successfully.

    Args:
        db_path: Path to authentication database
    """
    print("\nVerifying migration...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check oidc_states table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='oidc_states'
        """)
        if cursor.fetchone():
            print("  ✓ oidc_states table exists")
        else:
            print("  ✗ oidc_states table does not exist")
            return False

        # Check oidc_users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='oidc_users'
        """)
        if cursor.fetchone():
            print("  ✓ oidc_users table exists")
        else:
            print("  ✗ oidc_users table does not exist")
            return False

        # Check index exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_oidc_users_lookup'
        """)
        if cursor.fetchone():
            print("  ✓ oidc_users index exists")
        else:
            print("  ✗ oidc_users index does not exist")
            return False

        # Check data
        cursor.execute("SELECT COUNT(*) FROM oidc_users")
        mapping_count = cursor.fetchone()[0]

        print(f"  ✓ Database has {mapping_count} OIDC mappings")

        print("\n✓ Migration verification passed!")
        return True

    finally:
        conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "lexecon_auth.db"

    try:
        migrate(db_path)
        verify_migration(db_path)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
