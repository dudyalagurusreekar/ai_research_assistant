import unittest
from config.settings import settings

class TestSettings(unittest.TestCase):
    def test_settings(self):
        self.assertIsNotNone(settings.USER_AGENT)
        self.assertGreater(settings.PAGE_CHAR_LIMIT, 0)

if __name__ == '__main__':
    unittest.main()