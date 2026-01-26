"""
Feature flag management for Lexecon.

Supports LaunchDarkly for production and environment variable fallback for local development.
"""

from lexecon.features.service import FeatureFlagService, get_feature_flags

__all__ = ["FeatureFlagService", "get_feature_flags"]
