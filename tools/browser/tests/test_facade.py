"""Unit tests for Browser Tool Facade."""

import unittest
from tools.browser.facade import BrowserToolFacade
from core.models import ToolResult


class TestBrowserToolFacade(unittest.IsolatedAsyncioTestCase):
    """Test facade initialization, metadata, and execution workflow."""

    async def test_facade_execution(self):
        facade = BrowserToolFacade(headless=True)
        self.assertEqual(facade.metadata.name, "browser_tool")

        result = await facade.execute({"action": "navigate", "url": "https://example.com"})
        self.assertIsInstance(result, ToolResult)
        self.assertTrue(result.success)
        self.assertEqual(result.tool_name, "browser_tool")
        self.assertEqual(len(result.artifacts), 1)

        await facade.close()


if __name__ == "__main__":
    unittest.main()
