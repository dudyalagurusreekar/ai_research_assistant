"""Unit tests for Security Manager."""

import unittest
from infrastructure.security import SecurityManager


class TestSecurityManager(unittest.TestCase):
    """Test secrets, sanitization, and permissions."""

    def test_secrets_and_sanitization(self):
        sec = SecurityManager()
        sec.set_secret("API_KEY", "secret_key_12345")

        self.assertEqual(sec.get_secret("API_KEY"), "secret_key_12345")

        # Test input sanitization
        dirty_input = "Hello <script>alert(1)</script> World!\x00"
        clean_input = sec.sanitize_input(dirty_input)
        self.assertEqual(clean_input, "Hello  World!")

        # Test output sanitization
        raw_output = "Connected using secret_key_12345 API key."
        clean_output = sec.sanitize_output(raw_output)
        self.assertIn("***REDACTED***", clean_output)
        self.assertNotIn("secret_key_12345", clean_output)

    def test_permissions(self):
        sec = SecurityManager(allowed_permissions={"read"})
        self.assertTrue(sec.check_permission("read"))
        self.assertFalse(sec.check_permission("admin"))

        sec.grant_permission("admin")
        self.assertTrue(sec.check_permission("admin"))

        sec.revoke_permission("admin")
        self.assertFalse(sec.check_permission("admin"))


if __name__ == "__main__":
    unittest.main()
