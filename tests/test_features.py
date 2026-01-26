"""
Tests for feature flag service.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from lexecon.features import FeatureFlag, FeatureFlagService, get_feature_flags
from lexecon.features.flags import DEFAULT_FLAGS


class TestFeatureFlagService:
    """Test feature flag service functionality."""

    def test_init_without_sdk(self):
        """Test initialization without LaunchDarkly SDK."""
        service = FeatureFlagService()
        assert service.client is None

    def test_is_enabled_env_fallback_true(self, monkeypatch):
        """Test is_enabled with environment variable fallback (true)."""
        monkeypatch.setenv("FEATURE_FLAG_NEW_DECISION_ENGINE", "true")
        service = FeatureFlagService()

        assert service.is_enabled("new_decision_engine") is True

    def test_is_enabled_env_fallback_false(self, monkeypatch):
        """Test is_enabled with environment variable fallback (false)."""
        monkeypatch.setenv("FEATURE_FLAG_NEW_DECISION_ENGINE", "false")
        service = FeatureFlagService()

        assert service.is_enabled("new_decision_engine") is False

    def test_is_enabled_env_fallback_default(self):
        """Test is_enabled with default value when env var not set."""
        service = FeatureFlagService()

        assert service.is_enabled("nonexistent_flag", default=True) is True
        assert service.is_enabled("nonexistent_flag", default=False) is False

    def test_get_string_env_fallback(self, monkeypatch):
        """Test get_string with environment variable fallback."""
        monkeypatch.setenv("FEATURE_FLAG_API_VERSION", "v2")
        service = FeatureFlagService()

        assert service.get_string("api_version", default="v1") == "v2"

    def test_get_number_env_fallback(self, monkeypatch):
        """Test get_number with environment variable fallback."""
        monkeypatch.setenv("FEATURE_FLAG_RATE_LIMIT", "500")
        service = FeatureFlagService()

        assert service.get_number("rate_limit", default=100.0) == 500.0

    def test_get_number_invalid_fallback(self, monkeypatch):
        """Test get_number with invalid value falls back to default."""
        monkeypatch.setenv("FEATURE_FLAG_RATE_LIMIT", "invalid")
        service = FeatureFlagService()

        assert service.get_number("rate_limit", default=100.0) == 100.0

    def test_get_json_env_fallback(self, monkeypatch):
        """Test get_json with environment variable fallback."""
        monkeypatch.setenv('FEATURE_FLAG_CONFIG', '{"key": "value", "count": 42}')
        service = FeatureFlagService()

        result = service.get_json("config", default={})
        assert result == {"key": "value", "count": 42}

    def test_get_json_invalid_fallback(self, monkeypatch):
        """Test get_json with invalid JSON falls back to default."""
        monkeypatch.setenv("FEATURE_FLAG_CONFIG", "not-json")
        service = FeatureFlagService()

        assert service.get_json("config", default={"default": "value"}) == {
            "default": "value"
        }

    def test_boolean_env_variations(self, monkeypatch):
        """Test different boolean representations in env vars."""
        service = FeatureFlagService()

        for true_val in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
            monkeypatch.setenv("FEATURE_FLAG_TEST", true_val)
            assert service.is_enabled("test", default=False) is True

        for false_val in ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF"]:
            monkeypatch.setenv("FEATURE_FLAG_TEST", false_val)
            assert service.is_enabled("test", default=True) is False

    def test_launchdarkly_integration(self, monkeypatch):
        """Test LaunchDarkly integration when SDK is available."""
        monkeypatch.setenv("LAUNCHDARKLY_SDK_KEY", "sdk-test-key")
        monkeypatch.setenv("FEATURE_FLAGS_MODE", "launchdarkly")

        # Try to import LaunchDarkly SDK
        try:
            import ldclient

            # Skip test if SDK not installed (optional dependency)
            pytest.skip("LaunchDarkly SDK not installed (optional dependency)")
        except ImportError:
            # Expected when SDK not installed - service should fall back to env vars
            service = FeatureFlagService()
            assert service.client is None

            # Even without SDK, environment variable fallback should work
            monkeypatch.setenv("FEATURE_FLAG_TEST_FLAG", "true")
            result = service.is_enabled("test_flag", user_id="user:123")
            assert result is True

    def test_close(self):
        """Test closing the service."""
        service = FeatureFlagService()
        service.close()  # Should not raise any errors

    def test_singleton_instance(self):
        """Test get_feature_flags returns singleton instance."""
        instance1 = get_feature_flags()
        instance2 = get_feature_flags()

        assert instance1 is instance2


class TestFeatureFlags:
    """Test feature flag enum and defaults."""

    def test_feature_flag_enum(self):
        """Test FeatureFlag enum values."""
        assert FeatureFlag.NEW_DECISION_ENGINE == "new_decision_engine"
        assert FeatureFlag.MFA_REQUIRED == "mfa_required"
        assert FeatureFlag.RATE_LIMITING_STRICT == "rate_limiting_strict"

    def test_default_flags_exist(self):
        """Test all flags have default values."""
        for flag in FeatureFlag:
            assert flag in DEFAULT_FLAGS, f"Missing default for {flag}"

    def test_default_flag_types(self):
        """Test default flag value types are correct."""
        assert isinstance(DEFAULT_FLAGS[FeatureFlag.MFA_REQUIRED], bool)
        assert isinstance(DEFAULT_FLAGS[FeatureFlag.RATE_LIMIT_PER_USER], (int, float))
        assert isinstance(DEFAULT_FLAGS[FeatureFlag.AUDIT_LOG_RETENTION_DAYS], (int, float))

    def test_production_safe_defaults(self):
        """Test defaults are production-safe (secure by default)."""
        # Security features should default to enabled
        assert DEFAULT_FLAGS[FeatureFlag.SESSION_TIMEOUT_STRICT] is True
        assert DEFAULT_FLAGS[FeatureFlag.PASSWORD_EXPIRATION_ENABLED] is True

        # Rate limiting should be enabled
        assert DEFAULT_FLAGS[FeatureFlag.RATE_LIMITING_STRICT] is True

        # Encryption should be enabled
        assert DEFAULT_FLAGS[FeatureFlag.LEDGER_ENCRYPTION_ENABLED] is True

        # Experimental features should be disabled
        assert DEFAULT_FLAGS[FeatureFlag.EXPERIMENTAL_FEATURES] is False
        assert DEFAULT_FLAGS[FeatureFlag.BETA_FEATURES] is False


class TestFeatureFlagIntegration:
    """Integration tests for feature flags in application context."""

    def test_rate_limiting_configuration(self, monkeypatch):
        """Test configuring rate limits from feature flags."""
        monkeypatch.setenv("FEATURE_FLAG_RATE_LIMIT_PER_USER", "200")
        monkeypatch.setenv("FEATURE_FLAG_RATE_LIMIT_GLOBAL", "20000")

        flags = FeatureFlagService()
        per_user = flags.get_number(FeatureFlag.RATE_LIMIT_PER_USER, default=100)
        global_limit = flags.get_number(FeatureFlag.RATE_LIMIT_GLOBAL, default=10000)

        assert per_user == 200
        assert global_limit == 20000

    def test_mfa_requirement_check(self, monkeypatch):
        """Test MFA requirement based on feature flag."""
        monkeypatch.setenv("FEATURE_FLAG_MFA_REQUIRED", "true")

        flags = FeatureFlagService()
        assert flags.is_enabled(FeatureFlag.MFA_REQUIRED) is True

    def test_decision_engine_routing(self, monkeypatch):
        """Test routing between old and new decision engines."""
        # Enable new engine
        monkeypatch.setenv("FEATURE_FLAG_NEW_DECISION_ENGINE", "true")

        flags = FeatureFlagService()
        use_new_engine = flags.is_enabled(
            FeatureFlag.NEW_DECISION_ENGINE, user_id="user:alice"
        )

        assert use_new_engine is True

    def test_compliance_mode_flags(self, monkeypatch):
        """Test compliance mode feature flags."""
        monkeypatch.setenv("FEATURE_FLAG_GDPR_MODE_ENABLED", "true")
        monkeypatch.setenv("FEATURE_FLAG_HIPAA_MODE_ENABLED", "false")

        flags = FeatureFlagService()

        assert flags.is_enabled(FeatureFlag.GDPR_MODE_ENABLED) is True
        assert flags.is_enabled(FeatureFlag.HIPAA_MODE_ENABLED) is False
