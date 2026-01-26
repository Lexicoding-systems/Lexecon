"""
Examples of feature flag usage throughout Lexecon.

These examples demonstrate how to integrate feature flags into your application code.
"""

from lexecon.features import FeatureFlag, get_feature_flags


def example_decision_engine_routing():
    """Example: Route to new or old decision engine based on feature flag."""
    flags = get_feature_flags()

    actor = "user:alice"
    action = "read"
    resource = "document:123"

    if flags.is_enabled(FeatureFlag.NEW_DECISION_ENGINE, user_id=actor):
        # Use new optimized decision engine
        result = _evaluate_with_new_engine(actor, action, resource)
    else:
        # Use stable legacy decision engine
        result = _evaluate_with_legacy_engine(actor, action, resource)

    return result


def example_mfa_enforcement():
    """Example: Enforce MFA based on feature flag."""
    flags = get_feature_flags()

    user_id = "user:bob"
    user_has_mfa = False  # Check from database

    # Check if MFA is required for this user
    if flags.is_enabled(
        FeatureFlag.MFA_REQUIRED, user_id=user_id, user_attributes={"role": "admin"}
    ):
        if not user_has_mfa:
            raise PermissionError("MFA required for this operation")


def example_rate_limiting():
    """Example: Configure rate limiting based on feature flags."""
    flags = get_feature_flags()

    # Get dynamic rate limits from feature flags
    per_user_limit = flags.get_number(FeatureFlag.RATE_LIMIT_PER_USER, default=100)
    global_limit = flags.get_number(FeatureFlag.RATE_LIMIT_GLOBAL, default=10000)

    # Apply rate limiting with configured values
    rate_limiter.configure(per_user=per_user_limit, global_limit=global_limit)


def example_conditional_caching():
    """Example: Enable/disable caching based on feature flag."""
    flags = get_feature_flags()

    if flags.is_enabled(FeatureFlag.DECISION_CACHING_ENABLED):
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

    # Compute result
    result = expensive_computation()

    # Cache if enabled
    if flags.is_enabled(FeatureFlag.DECISION_CACHING_ENABLED):
        cache.set(cache_key, result, ttl=300)

    return result


def example_compliance_mode():
    """Example: Enable GDPR/HIPAA features based on flags."""
    flags = get_feature_flags()

    gdpr_enabled = flags.is_enabled(FeatureFlag.GDPR_MODE_ENABLED)
    hipaa_enabled = flags.is_enabled(FeatureFlag.HIPAA_MODE_ENABLED)

    if gdpr_enabled:
        # Add GDPR-specific headers, logging, data handling
        response.headers["X-GDPR-Compliant"] = "true"
        log_gdpr_access(user_id, resource_id)

    if hipaa_enabled:
        # Enable HIPAA audit logging, encryption requirements
        enable_hipaa_audit_log()
        enforce_phi_encryption()


def example_json_configuration():
    """Example: Get complex configuration from JSON feature flag."""
    flags = get_feature_flags()

    # Get experimental features config
    experimental_config = flags.get_json(
        "experimental_config",
        default={
            "batch_size": 100,
            "timeout_ms": 5000,
            "retry_count": 3,
        },
    )

    batch_processor.configure(
        batch_size=experimental_config["batch_size"],
        timeout=experimental_config["timeout_ms"] / 1000,
        retries=experimental_config["retry_count"],
    )


def example_gradual_rollout():
    """Example: Gradually roll out feature to users based on targeting."""
    flags = get_feature_flags()

    user_id = "user:charlie"
    user_email = "charlie@example.com"

    # LaunchDarkly can target users based on attributes
    # For example: "Roll out to 10% of users" or "Beta testers only"
    if flags.is_enabled(
        FeatureFlag.BETA_FEATURES,
        user_id=user_id,
        user_attributes={
            "email": user_email,
            "signup_date": "2024-01-01",
            "plan": "enterprise",
        },
    ):
        # User gets access to beta features
        show_beta_ui()
    else:
        # User sees stable features only
        show_stable_ui()


# Placeholder functions for examples
def _evaluate_with_new_engine(actor, action, resource):
    return {"allowed": True, "engine": "new"}


def _evaluate_with_legacy_engine(actor, action, resource):
    return {"allowed": True, "engine": "legacy"}


class rate_limiter:
    @staticmethod
    def configure(per_user, global_limit):
        pass


class cache:
    @staticmethod
    def get(key):
        return None

    @staticmethod
    def set(key, value, ttl):
        pass


def expensive_computation():
    return {"result": "computed"}


def log_gdpr_access(user_id, resource_id):
    pass


def enable_hipaa_audit_log():
    pass


def enforce_phi_encryption():
    pass


class batch_processor:
    @staticmethod
    def configure(batch_size, timeout, retries):
        pass


def show_beta_ui():
    pass


def show_stable_ui():
    pass


cache_key = "example_key"
response = type("Response", (), {"headers": {}})()
