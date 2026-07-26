"""Unit tests for Browser Executor."""

import unittest
from tools.browser.driver import PlaywrightDriver
from tools.browser.executor import BrowserExecutor


class TestBrowserExecutor(unittest.IsolatedAsyncioTestCase):
    """Test deterministic action execution."""

    async def test_execute_actions(self):
        driver = PlaywrightDriver(headless=True)
        executor = BrowserExecutor(driver)

        nav_res = await executor.execute_action("navigate", {"url": "https://example.com"})
        self.assertTrue(nav_res["success"])

        scroll_res = await executor.execute_action("scroll", {"direction": "down", "amount": 300})
        self.assertTrue(scroll_res["success"])
        self.assertEqual(executor.state.scroll_y, 300)

        await driver.close()


if __name__ == "__main__":
    unittest.main()
