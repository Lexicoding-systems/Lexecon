#!/usr/bin/env python3
"""Migration: Add MFA (Multi-Factor Authentication) support.

Adds MFA columns to users table and creates mfa_challenges table for
TOTP-based two-factor authentication.

Run: python migrations/001_add_mfa_support.py [db_path]
"""

import sqlite3
import sys


def migrate(db_path="lexecon_auth.db"):
    """Apply MFA migration to database.

    Args:
        db_path: Path to authentication database
    """
    print(f"Applying MFA migration to {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add MFA columns to users table
        print("\n[1/3] Adding MFA columns to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN mfa_enabled INTEGER DEFAULT 0")
            print("  ✓ Added mfa_enabled column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  ⊘ mfa_enabled column already exists")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN mfa_secret TEXT")
            print("  ✓ Added mfa_secret column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  ⊘ mfa_secret column already exists")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN mfa_backup_codes TEXT")
            print("  ✓ Added mfa_backup_codes column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  ⊘ mfa_backup_codes column already exists")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN mfa_enrolled_at TEXT")
            print("  ✓ Added mfa_enrolled_at column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  ⊘ mfa_enrolled_at column already exists")
            else:
                raise

        # Create mfa_challenges table
        print("\n[2/3] Creating mfa_challenges table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mfa_challenges (
                challenge_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_token TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                verified INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        print("  ✓ Created mfa_challenges table")

        # Create index for efficient challenge lookups and cleanup
        print("\n[3/3] Creating index on mfa_challenges...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mfa_challenges_expires
            ON mfa_challenges(expires_at)
        """)
        print("  ✓ Created index idx_mfa_challenges_expires")

        # Commit all changes
        conn.commit()

        print("\n" + "=" * 60)
        print("✓ MFA migration completed successfully!")
        print("=" * 60)
        print("\nDatabase changes:")
        print("  • Added mfa_enabled column to users")
        print("  • Added mfa_secret column to users")
        print("  • Added mfa_backup_codes column to users")
        print("  • Added mfa_enrolled_at column to users")
        print("  • Created mfa_challenges table")
        print("  • Created index on mfa_challenges")
        print("\nMFA features now available:")
        print("  • TOTP-based two-factor authentication")
        print("  • QR code generation for authenticator apps")
        print("  • Backup recovery codes")
        print("  • Time-limited MFA challenges (5 min)")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        raise

    finally:
        conn.close()


def verify_migration(db_path="lexecon_auth.db"):
    """Verify migration was applied successfully.

    Args:
        db_path: Path to authentication database
    """
    print("\nVerifying migration...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check users table columns
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {
            "mfa_enabled",
            "mfa_secret",
            "mfa_backup_codes",
            "mfa_enrolled_at",
        }

        if required_columns.issubset(columns):
            print("  ✓ Users table has all required MFA columns")
        else:
            missing = required_columns - columns
            print(f"  ✗ Users table missing columns: {missing}")
            return False

        # Check mfa_challenges table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='mfa_challenges'
        """)
        if cursor.fetchone():
            print("  ✓ mfa_challenges table exists")
        else:
            print("  ✗ mfa_challenges table does not exist")
            return False

        # Check index exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_mfa_challenges_expires'
        """)
        if cursor.fetchone():
            print("  ✓ mfa_challenges index exists")
        else:
            print("  ✗ mfa_challenges index does not exist")
            return False

        # Check data
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE mfa_enabled = 1")
        mfa_enabled_count = cursor.fetchone()[0]

        print(f"  ✓ Database has {user_count} users")
        print(f"  ✓ {mfa_enabled_count} users have MFA enabled")

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
