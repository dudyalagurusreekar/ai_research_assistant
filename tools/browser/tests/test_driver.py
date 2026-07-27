"""Unit tests for Browser Driver abstraction."""

import unittest
from tools.browser.driver import PlaywrightDriver


class TestBrowserDriver(unittest.IsolatedAsyncioTestCase):
    """Test driver operations and navigation state."""

    async def test_driver_open_url_and_content(self):
        driver = PlaywrightDriver(headless=True)
        success = await driver.open_url("https://en.wikipedia.org/wiki/Main_Page")
        self.assertTrue(success)

        url = await driver.get_current_url()
        self.assertIn("wikipedia.org", url)

        html = await driver.get_html()
        self.assertIsInstance(html, str)
        await driver.close()


if __name__ == "__main__":
    unittest.main()
