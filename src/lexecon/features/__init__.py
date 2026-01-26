"""
Feature flag management for Lexecon.

Supports LaunchDarkly for production and environment variable fallback for local development.
"""

from lexecon.features.flags import DEFAULT_FLAGS, FeatureFlag
from lexecon.features.service import FeatureFlagService, get_feature_flags

__all__ = ["FeatureFlagService", "get_feature_flags", "FeatureFlag", "DEFAULT_FLAGS"]
