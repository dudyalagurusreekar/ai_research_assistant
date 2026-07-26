"""Unit tests for Step 1: Browser Tool Architectural Foundation.

Tests configuration, custom exceptions, DTO models, helper functions,
abstract interfaces, Browser engine orchestrator skeleton, and ToolRegistry integration.
"""

import unittest
from unittest.mock import MagicMock, patch

from tools.browser.constants import (
    HttpMethod,
    BrowserAction,
    PageStatus,
    BrowserEngineType,
)
from tools.browser.exceptions import (
    BrowserError,
    ConfigurationError,
    ValidationError,
    FetchError,
)
from tools.browser.config import BrowserConfig
from tools.browser.models import (
    BrowserRequest,
    NavigationParams,
    ActionParams,
    BrowserResponse,
    PageMetadata,
    PageState,
    FetchResult,
)
from tools.browser.utils.helpers import (
    validate_url,
    sanitize_url,
    extract_domain,
    clean_text,
    generate_request_id,
)
from tools.browser.core.browser import Browser
from tools.browser.tool import BrowserTool
from tools.registry import registry


class TestBrowserFoundation(unittest.TestCase):
    """Test suite verifying Step 1 architectural foundation components."""

    def test_browser_config_defaults_and_validation(self):
        """Test default BrowserConfig values and validation logic."""
        config = BrowserConfig()
        self.assertEqual(config.engine_type, BrowserEngineType.HTTP_BASIC)
        self.assertGreater(config.timeout_seconds, 0)
        self.assertTrue(config.validate())

        # Invalid config should raise ConfigurationError
        invalid_config = BrowserConfig(timeout_seconds=-5.0)
        with self.assertRaises(ConfigurationError):
            invalid_config.validate()

    def test_custom_exception_hierarchy(self):
        """Test BrowserError exception hierarchy and context formatting."""
        err = FetchError("Failed to fetch", url="https://example.com", status_code=404)
        self.assertIsInstance(err, BrowserError)
        self.assertEqual(err.url, "https://example.com")
        self.assertEqual(err.status_code, 404)
        self.assertIn("status_code=404", str(err))

    def test_helpers_url_validation_and_cleaning(self):
        """Test URL validation, sanitization, and text cleaning helpers."""
        url = "https://EXAMPLE.COM/path/to/page#fragment  "
        sanitized = sanitize_url(url)
        self.assertEqual(sanitized, "https://example.com/path/to/page")

        self.assertTrue(validate_url("https://python.org"))
        with self.assertRaises(ValidationError):
            validate_url("invalid-scheme://foo")

        self.assertEqual(extract_domain("https://docs.python.org:8080/3/library"), "docs.python.org")
        self.assertEqual(clean_text("  hello   world \n\t new  line  "), "hello world new line")
        self.assertTrue(generate_request_id("test").startswith("test-"))

    def test_data_models_validation(self):
        """Test request and response DTO validation."""
        nav = NavigationParams(url="https://ai.google")
        self.assertTrue(nav.validate())

        action = ActionParams(action=BrowserAction.CLICK, selector="#submit-btn")
        self.assertTrue(action.validate())

        req = BrowserRequest(request_id="req-123", navigation=nav)
        self.assertTrue(req.validate())

        response = BrowserResponse(
            request_id="req-123",
            url="https://ai.google",
            status=PageStatus.LOADED,
            status_code=200,
            extracted_text="Sample text content",
        )
        res_dict = response.to_dict()
        self.assertEqual(res_dict["request_id"], "req-123")
        self.assertEqual(res_dict["status_code"], 200)

    @patch("httpx.Client.stream")
    def test_browser_orchestrator_skeleton_navigation(self, mock_stream):
        """Test Browser orchestrator skeleton navigation and state recording."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.iter_bytes.return_value = [b"Research Page Content"]
        mock_response.encoding = "utf-8"
        mock_response.history = []
        mock_response.url = "https://example.org/research"
        mock_stream.return_value.__enter__.return_value = mock_response

        browser = Browser()
        url = "https://example.org/research"

        response = browser.navigate(url)
        self.assertIsInstance(response, BrowserResponse)
        self.assertEqual(response.url, "https://example.org/research")
        self.assertIn(response.status, (PageStatus.LOADED, PageStatus.PARSED))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(browser.history), 1)
        self.assertEqual(browser.history[0], "https://example.org/research")

        browser.close()

    @patch("httpx.Client.stream")
    def test_browser_tool_integration_with_registry(self, mock_stream):
        """Test BrowserTool smolagents wrapper and global tool registry inclusion."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.iter_bytes.return_value = [b"Example Domain Content"]
        mock_response.encoding = "utf-8"
        mock_response.history = []
        mock_response.url = "https://example.com"
        mock_stream.return_value.__enter__.return_value = mock_response

        config = BrowserConfig(engine_type=BrowserEngineType.HTTP_BASIC)
        tool = BrowserTool(config=config)
        self.assertEqual(tool.name, "browser_tool")

        result = tool.forward("https://example.com")
        self.assertIn("Example Domain Content", result)

        # Check registered tools in ToolRegistry
        registered_names = registry.list_tools()
        self.assertIn("browser_tool", registered_names)


if __name__ == "__main__":
    unittest.main()
