"""Database schema version tracking."""

CURRENT_SCHEMA_VERSION = 2
SCHEMA_HISTORY = {
    1: "Initial schema with users, sessions, login_attempts",
    2: "Add missing columns: password_changed_at, password_expires_at, mfa_enabled, mfa_secret, password_history table",
}
