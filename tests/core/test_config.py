"""Unit tests for Configuration System and Feature Flags."""

import os
import unittest
from core.config import ConfigLoader, FeatureFlags, AppConfig


class TestConfig(unittest.TestCase):
    """Test configuration loading and feature flag overrides."""

    def test_config_loader_defaults(self):
        config = ConfigLoader.load_from_env()
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.environment, "development")
        self.assertEqual(config.events.max_queue_size, 1000)

    def test_feature_flags(self):
        ff = FeatureFlags(defaults={"new_ui": True, "beta_tool": False})
        self.assertTrue(ff.is_enabled("new_ui"))
        self.assertFalse(ff.is_enabled("beta_tool"))

        # Test runtime override
        ff.set_flag("beta_tool", True)
        self.assertTrue(ff.is_enabled("beta_tool"))

        # Test env variable override
        os.environ["FF_ENV_FEATURE"] = "true"
        self.assertTrue(ff.is_enabled("env_feature"))
        del os.environ["FF_ENV_FEATURE"]


if __name__ == "__main__":
    unittest.main()
