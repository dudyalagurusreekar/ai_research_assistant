"""Feature Flags system for runtime capability toggles."""

import os
from typing import Dict, Optional


class FeatureFlags:
    """Manages feature flags loaded from environment variables and runtime overrides."""

    def __init__(self, defaults: Optional[Dict[str, bool]] = None) -> None:
        self._flags: Dict[str, bool] = defaults or {}

    def is_enabled(self, feature_name: str, default: bool = False) -> bool:
        """Check if a feature flag is enabled.

        Environment variable `FF_<FEATURE_NAME>` takes precedence over in-memory values.

        Args:
            feature_name: Feature flag key (e.g., 'enable_tool_router').
            default: Default state if not defined.

        Returns:
            True if enabled, else False.
        """
        env_key = f"FF_{feature_name.upper()}"
        if env_key in os.environ:
            return os.environ[env_key].lower() in ("true", "1", "yes")

        return self._flags.get(feature_name, default)

    def set_flag(self, feature_name: str, enabled: bool) -> None:
        """Dynamically override a feature flag in memory."""
        self._flags[feature_name] = enabled

    def get_all_flags(self) -> Dict[str, bool]:
        """Return all active feature flags."""
        return dict(self._flags)
