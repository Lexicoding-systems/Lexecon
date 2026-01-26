"""
Common feature flags used throughout Lexecon.

Centralized flag definitions for easy reference and documentation.
"""

from enum import Enum


class FeatureFlag(str, Enum):
    """
    Common feature flags.

    Usage:
        from lexecon.features import get_feature_flags, FeatureFlag

        flags = get_feature_flags()
        if flags.is_enabled(FeatureFlag.NEW_DECISION_ENGINE):
            # Use new decision engine
            pass
    """

    # Security & Authentication
    MFA_REQUIRED = "mfa_required"
    MFA_ENROLLMENT_MANDATORY = "mfa_enrollment_mandatory"
    PASSWORD_EXPIRATION_ENABLED = "password_expiration_enabled"
    SESSION_TIMEOUT_STRICT = "session_timeout_strict"

    # Rate Limiting
    RATE_LIMITING_STRICT = "rate_limiting_strict"
    RATE_LIMIT_PER_USER = "rate_limit_per_user"
    RATE_LIMIT_GLOBAL = "rate_limit_global"

    # Decision Engine
    NEW_DECISION_ENGINE = "new_decision_engine"
    DECISION_CACHING_ENABLED = "decision_caching_enabled"
    DECISION_ASYNC_EVALUATION = "decision_async_evaluation"
    DECISION_BATCH_PROCESSING = "decision_batch_processing"

    # Ledger & Audit
    LEDGER_COMPRESSION_ENABLED = "ledger_compression_enabled"
    LEDGER_ENCRYPTION_ENABLED = "ledger_encryption_enabled"
    AUDIT_LOG_RETENTION_DAYS = "audit_log_retention_days"

    # API Features
    API_VERSIONING_ENABLED = "api_versioning_enabled"
    API_DEPRECATION_WARNINGS = "api_deprecation_warnings"
    GRAPHQL_ENABLED = "graphql_enabled"
    WEBHOOKS_ENABLED = "webhooks_enabled"

    # Observability
    METRICS_DETAILED = "metrics_detailed"
    TRACING_ENABLED = "tracing_enabled"
    PERFORMANCE_PROFILING = "performance_profiling"

    # Compliance
    GDPR_MODE_ENABLED = "gdpr_mode_enabled"
    HIPAA_MODE_ENABLED = "hipaa_mode_enabled"
    DATA_RESIDENCY_ENFORCEMENT = "data_residency_enforcement"

    # Experimental
    EXPERIMENTAL_FEATURES = "experimental_features"
    BETA_FEATURES = "beta_features"


# Default flag values (used for environment variable fallback)
DEFAULT_FLAGS = {
    # Security defaults (production-safe)
    FeatureFlag.MFA_REQUIRED: False,
    FeatureFlag.MFA_ENROLLMENT_MANDATORY: False,
    FeatureFlag.PASSWORD_EXPIRATION_ENABLED: True,
    FeatureFlag.SESSION_TIMEOUT_STRICT: True,
    # Rate limiting defaults
    FeatureFlag.RATE_LIMITING_STRICT: True,
    FeatureFlag.RATE_LIMIT_PER_USER: 100,  # requests per minute
    FeatureFlag.RATE_LIMIT_GLOBAL: 10000,  # requests per minute
    # Decision engine defaults
    FeatureFlag.NEW_DECISION_ENGINE: False,
    FeatureFlag.DECISION_CACHING_ENABLED: True,
    FeatureFlag.DECISION_ASYNC_EVALUATION: False,
    FeatureFlag.DECISION_BATCH_PROCESSING: False,
    # Ledger defaults
    FeatureFlag.LEDGER_COMPRESSION_ENABLED: True,
    FeatureFlag.LEDGER_ENCRYPTION_ENABLED: True,
    FeatureFlag.AUDIT_LOG_RETENTION_DAYS: 90,
    # API defaults
    FeatureFlag.API_VERSIONING_ENABLED: True,
    FeatureFlag.API_DEPRECATION_WARNINGS: True,
    FeatureFlag.GRAPHQL_ENABLED: False,
    FeatureFlag.WEBHOOKS_ENABLED: False,
    # Observability defaults
    FeatureFlag.METRICS_DETAILED: True,
    FeatureFlag.TRACING_ENABLED: False,
    FeatureFlag.PERFORMANCE_PROFILING: False,
    # Compliance defaults
    FeatureFlag.GDPR_MODE_ENABLED: False,
    FeatureFlag.HIPAA_MODE_ENABLED: False,
    FeatureFlag.DATA_RESIDENCY_ENFORCEMENT: False,
    # Experimental defaults (off by default)
    FeatureFlag.EXPERIMENTAL_FEATURES: False,
    FeatureFlag.BETA_FEATURES: False,
}
