"""
Feature flag service with LaunchDarkly integration and environment variable fallback.

Supports:
- LaunchDarkly for production (enterprise-grade feature flags)
- Environment variable fallback for local development
- Type-safe flag evaluation
- User targeting and segmentation
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """
    Feature flag service supporting LaunchDarkly and environment variable fallback.

    Usage:
        flags = FeatureFlagService()
        if flags.is_enabled("new_decision_engine", user_id="user:123"):
            # Use new decision engine
            pass
    """

    def __init__(self, sdk_key: Optional[str] = None):
        """
        Initialize feature flag service.

        Args:
            sdk_key: LaunchDarkly SDK key. If not provided, falls back to LAUNCHDARKLY_SDK_KEY env var.
        """
        self.sdk_key = sdk_key or os.getenv("LAUNCHDARKLY_SDK_KEY")
        self.client = None
        self._env_fallback = os.getenv("FEATURE_FLAGS_MODE", "env") == "env"

        if self.sdk_key and not self._env_fallback:
            try:
                import ldclient
                from ldclient.config import Config

                config = Config(sdk_key=self.sdk_key)
                ldclient.set_config(config)
                self.client = ldclient.get()

                if self.client.is_initialized():
                    logger.info("LaunchDarkly client initialized successfully")
                else:
                    logger.warning("LaunchDarkly client failed to initialize, using env fallback")
                    self.client = None
            except ImportError:
                logger.warning("LaunchDarkly SDK not installed, using environment variable fallback")
                self.client = None
            except Exception as e:
                logger.error(f"Error initializing LaunchDarkly: {e}, using env fallback")
                self.client = None
        else:
            logger.info("Using environment variable fallback for feature flags")

    def is_enabled(
        self,
        flag_key: str,
        user_id: Optional[str] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        default: bool = False,
    ) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_key: Feature flag key (e.g., "new_decision_engine")
            user_id: User ID for targeting (optional)
            user_attributes: Additional user attributes for targeting (optional)
            default: Default value if flag is not found

        Returns:
            True if feature is enabled, False otherwise
        """
        if self.client:
            try:
                from ldclient import Context

                # Build context for user targeting
                context_dict = {"kind": "user", "key": user_id or "anonymous"}
                if user_attributes:
                    context_dict.update(user_attributes)

                context = Context.builder(user_id or "anonymous").build()
                return self.client.variation(flag_key, context, default)
            except Exception as e:
                logger.error(f"Error evaluating LaunchDarkly flag {flag_key}: {e}")
                return self._get_env_flag(flag_key, default)
        else:
            return self._get_env_flag(flag_key, default)

    def get_string(
        self,
        flag_key: str,
        user_id: Optional[str] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        default: str = "",
    ) -> str:
        """
        Get string value from feature flag.

        Args:
            flag_key: Feature flag key
            user_id: User ID for targeting (optional)
            user_attributes: Additional user attributes for targeting (optional)
            default: Default value if flag is not found

        Returns:
            String value of the feature flag
        """
        if self.client:
            try:
                from ldclient import Context

                context = Context.builder(user_id or "anonymous").build()
                return self.client.variation(flag_key, context, default)
            except Exception as e:
                logger.error(f"Error evaluating LaunchDarkly flag {flag_key}: {e}")
                return self._get_env_flag(flag_key, default)
        else:
            return self._get_env_flag(flag_key, default)

    def get_number(
        self,
        flag_key: str,
        user_id: Optional[str] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        default: float = 0.0,
    ) -> float:
        """
        Get numeric value from feature flag.

        Args:
            flag_key: Feature flag key
            user_id: User ID for targeting (optional)
            user_attributes: Additional user attributes for targeting (optional)
            default: Default value if flag is not found

        Returns:
            Numeric value of the feature flag
        """
        if self.client:
            try:
                from ldclient import Context

                context = Context.builder(user_id or "anonymous").build()
                return self.client.variation(flag_key, context, default)
            except Exception as e:
                logger.error(f"Error evaluating LaunchDarkly flag {flag_key}: {e}")
                return self._get_env_flag(flag_key, default)
        else:
            return self._get_env_flag(flag_key, default)

    def get_json(
        self,
        flag_key: str,
        user_id: Optional[str] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        default: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get JSON value from feature flag.

        Args:
            flag_key: Feature flag key
            user_id: User ID for targeting (optional)
            user_attributes: Additional user attributes for targeting (optional)
            default: Default value if flag is not found

        Returns:
            JSON/dict value of the feature flag
        """
        if default is None:
            default = {}

        if self.client:
            try:
                from ldclient import Context

                context = Context.builder(user_id or "anonymous").build()
                return self.client.variation(flag_key, context, default)
            except Exception as e:
                logger.error(f"Error evaluating LaunchDarkly flag {flag_key}: {e}")
                return self._get_env_flag(flag_key, default)
        else:
            return self._get_env_flag(flag_key, default)

    def _get_env_flag(self, flag_key: str, default: Any) -> Any:
        """
        Get feature flag from environment variable.

        Environment variable format: FEATURE_FLAG_<FLAG_KEY>=true/false/value

        Args:
            flag_key: Feature flag key
            default: Default value if env var not found

        Returns:
            Feature flag value from environment or default
        """
        env_key = f"FEATURE_FLAG_{flag_key.upper()}"
        value = os.getenv(env_key)

        if value is None:
            return default

        # Handle boolean flags
        if isinstance(default, bool):
            return value.lower() in ("true", "1", "yes", "on")

        # Handle numeric flags
        if isinstance(default, (int, float)):
            try:
                return float(value) if isinstance(default, float) else int(value)
            except ValueError:
                logger.warning(f"Invalid numeric value for {env_key}: {value}")
                return default

        # Handle JSON flags
        if isinstance(default, dict):
            try:
                import json

                return json.loads(value)
            except (ValueError, json.JSONDecodeError):
                logger.warning(f"Invalid JSON value for {env_key}: {value}")
                return default

        # Default to string
        return value

    def close(self):
        """Close LaunchDarkly client connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("LaunchDarkly client closed")
            except Exception as e:
                logger.error(f"Error closing LaunchDarkly client: {e}")


# Global feature flag service instance
_feature_flags: Optional[FeatureFlagService] = None


def get_feature_flags() -> FeatureFlagService:
    """
    Get global feature flag service instance.

    Returns:
        Singleton FeatureFlagService instance
    """
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlagService()
    return _feature_flags
