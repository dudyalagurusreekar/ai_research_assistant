"""Unit tests for Browser Rule Engine."""

import unittest
from tools.browser.rules import BrowserRuleEngine


class TestBrowserRuleEngine(unittest.TestCase):
    """Test deterministic rules and retries."""

    def test_rules(self):
        engine = BrowserRuleEngine(max_retries=3)
        self.assertTrue(engine.should_retry("click", 1, "TIMEOUT_ERROR"))
        self.assertFalse(engine.should_retry("click", 3, "TIMEOUT_ERROR"))

        self.assertEqual(engine.get_wait_strategy("navigate"), 3.0)
        self.assertEqual(engine.sanitize_navigation_url("wikipedia.org"), "https://wikipedia.org")


if __name__ == "__main__":
    unittest.main()
