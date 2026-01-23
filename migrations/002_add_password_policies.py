#!/usr/bin/env python3
"""Migration: Add password policy support.

Adds password history tracking, expiration, and force change columns to the users table.
Creates password_history table for tracking previous passwords.

Run: python migrations/002_add_password_policies.py [db_path]
"""

import secrets
import sqlite3
import sys
from datetime import datetime, timezone


def migrate(db_path="lexecon_auth.db"):
    """Apply password policy migration to database.

    Args:
        db_path: Path to authentication database
    """
    print(f"Applying password policy migration to {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add password policy columns to users table
        print("\n[1/5] Adding password policy columns to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password_changed_at TEXT")
            print("  ✓ Added password_changed_at column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  ⊘ password_changed_at column already exists")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password_expires_at TEXT")
            print("  ✓ Added password_expires_at column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  ⊘ password_expires_at column already exists")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN force_password_change INTEGER DEFAULT 0")
            print("  ✓ Added force_password_change column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  ⊘ force_password_change column already exists")
            else:
                raise

        # Initialize password_changed_at for existing users
        print("\n[2/5] Initializing password_changed_at for existing users...")
        cursor.execute("""
            UPDATE users
            SET password_changed_at = COALESCE(password_changed_at, created_at, ?)
            WHERE password_changed_at IS NULL
        """, (datetime.now(timezone.utc).isoformat(),))
        updated_count = cursor.rowcount
        print(f"  ✓ Updated {updated_count} existing users")

        # Create password_history table
        print("\n[3/5] Creating password_history table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_history (
                history_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        print("  ✓ Created password_history table")

        # Create index for efficient history lookups
        print("\n[4/5] Creating index on password_history...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_password_history_user
            ON password_history(user_id, changed_at DESC)
        """)
        print("  ✓ Created index idx_password_history_user")

        # Populate password_history with current passwords for existing users
        print("\n[5/5] Initializing password history for existing users...")
        cursor.execute("""
            SELECT user_id, password_hash,
                   COALESCE(password_changed_at, created_at, ?) as changed_at
            FROM users
        """, (datetime.now(timezone.utc).isoformat(),))

        users = cursor.fetchall()
        history_count = 0

        for user_id, password_hash, changed_at in users:
            # Check if history entry already exists
            cursor.execute("""
                SELECT COUNT(*) FROM password_history
                WHERE user_id = ? AND password_hash = ?
            """, (user_id, password_hash))

            if cursor.fetchone()[0] == 0:
                # Insert initial password into history
                history_id = f"hist_{secrets.token_hex(16)}"
                cursor.execute("""
                    INSERT INTO password_history (history_id, user_id, password_hash, changed_at)
                    VALUES (?, ?, ?, ?)
                """, (history_id, user_id, password_hash, changed_at))
                history_count += 1

        print(f"  ✓ Initialized password history for {history_count} users")

        # Commit all changes
        conn.commit()

        print("\n" + "=" * 60)
        print("✓ Password policy migration completed successfully!")
        print("=" * 60)
        print("\nDatabase changes:")
        print("  • Added password_changed_at column to users")
        print("  • Added password_expires_at column to users")
        print("  • Added force_password_change column to users")
        print("  • Created password_history table")
        print("  • Created index on password_history")
        print(f"  • Initialized history for {history_count} existing users")
        print("\nPassword policy features now available:")
        print("  • Password complexity validation")
        print("  • Password history (prevent reuse)")
        print("  • Password expiration (90 days default)")
        print("  • Force password change capability")

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
            "password_changed_at",
            "password_expires_at",
            "force_password_change",
        }

        if required_columns.issubset(columns):
            print("  ✓ Users table has all required columns")
        else:
            missing = required_columns - columns
            print(f"  ✗ Users table missing columns: {missing}")
            return False

        # Check password_history table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='password_history'
        """)
        if cursor.fetchone():
            print("  ✓ password_history table exists")
        else:
            print("  ✗ password_history table does not exist")
            return False

        # Check index exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_password_history_user'
        """)
        if cursor.fetchone():
            print("  ✓ password_history index exists")
        else:
            print("  ✗ password_history index does not exist")
            return False

        # Check data
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM password_history")
        history_count = cursor.fetchone()[0]

        print(f"  ✓ Database has {user_count} users")
        print(f"  ✓ Password history has {history_count} entries")

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
