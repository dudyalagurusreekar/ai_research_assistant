import unittest
from config.settings import settings

class TestSettings(unittest.TestCase):
    def test_settings(self):
        self.assertIsNotNone(settings.APP_NAME)
        self.assertIsNotNone(settings.ENVIRONMENT)
        self.assertEqual(settings.APP_VERSION, "1.0.0")

if __name__ == '__main__':
    unittest.main()