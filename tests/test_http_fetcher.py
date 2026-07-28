"""Unit tests for Step 2: Fetcher Layer (HTTPFetcher & FetcherFactory).

Tests synchronous and asynchronous resource retrieval, connection pooling, header merging,
timeout handling, URL validation, size capping, exponential backoff retries, custom exception mapping,
Strategy Pattern factory instantiation, and Browser integration.
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

import httpx

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.core.base_fetcher import BaseFetcher
from tools.browser.core.browser import Browser
from tools.browser.exceptions import (
    FetchError,
    TimeoutError,
    NetworkError,
    ValidationError,
    UnsupportedEngineError,
)
from tools.browser.fetchers import HTTPFetcher, FetcherFactory
from tools.browser.models import NavigationParams, FetchResult, BrowserResponse


class DummyMockFetcher(BaseFetcher):
    """Mock Fetcher strategy for strategy pattern testing."""

    def fetch(self, params: NavigationParams) -> FetchResult:
        return FetchResult(
            url=params.url,
            status_code=200,
            content=b"<html><body>Dummy Strategy Response</body></html>",
            encoding="utf-8",
            mime_type="text/html",
        )

    async def fetch_async(self, params: NavigationParams) -> FetchResult:
        return self.fetch(params)

    def close(self) -> None:
        pass


class TestHTTPFetcher(unittest.TestCase):
    """Test suite for Step 2 HTTPFetcher and FetcherFactory architecture."""

    def setUp(self):
        self.config = BrowserConfig(
            timeout_seconds=5.0,
            max_retries=3,
            backoff_factor=0.01,  # Fast backoff for test speed
            max_page_size_bytes=1024,  # 1 KB limit for tests
        )
        self.fetcher = HTTPFetcher(self.config)

    def tearDown(self):
        self.fetcher.close()

    def test_url_validation_and_sanitization(self):
        """Test URL validation and sanitization prior to networking."""
        params_invalid_scheme = NavigationParams(url="ftp://example.com/file")
        with self.assertRaises(ValidationError):
            self.fetcher.fetch(params_invalid_scheme)

        params_missing_domain = NavigationParams(url="http://")
        with self.assertRaises(ValidationError):
            self.fetcher.fetch(params_missing_domain)

    @patch("httpx.Client.stream")
    def test_sync_fetch_success(self, mock_stream):
        """Test successful synchronous HTTP fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = httpx.Headers({"content-type": "text/html; charset=utf-8"})
        mock_response.iter_bytes.return_value = [b"<h1>Hello World</h1>"]
        mock_response.encoding = "utf-8"
        mock_response.history = []
        mock_response.url = "https://example.com"

        mock_stream.return_value.__enter__.return_value = mock_response

        params = NavigationParams(url="https://example.com")
        result = self.fetcher.fetch(params)

        self.assertIsInstance(result, FetchResult)
        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.text, "<h1>Hello World</h1>")
        self.assertEqual(result.mime_type, "text/html")
        self.assertTrue(result.success)
        self.assertEqual(result.redirect_count, 0)
        self.assertGreater(result.response_time_ms, 0)

    @patch("httpx.Client.stream")
    def test_timeout_exception_mapping(self, mock_stream):
        """Test mapping of httpx.ConnectTimeout to custom TimeoutError."""
        mock_stream.side_effect = httpx.ConnectTimeout("Connection timed out")

        params = NavigationParams(url="https://timeout-domain.com")
        with self.assertRaises(TimeoutError) as ctx:
            self.fetcher.fetch(params)

        self.assertIn("timed out", str(ctx.exception))
        self.assertEqual(ctx.exception.url, "https://timeout-domain.com")

    @patch("httpx.Client.stream")
    def test_network_error_exception_mapping(self, mock_stream):
        """Test mapping of httpx.ConnectError to custom NetworkError."""
        mock_stream.side_effect = httpx.ConnectError("Failed to resolve host")

        params = NavigationParams(url="https://unresolved-domain.com")
        with self.assertRaises(NetworkError) as ctx:
            self.fetcher.fetch(params)

        self.assertIn("Network socket failure", str(ctx.exception))
        self.assertEqual(ctx.exception.url, "https://unresolved-domain.com")

    @patch("httpx.Client.stream")
    def test_content_length_header_limit_exceeded(self, mock_stream):
        """Test early abort when Content-Length header exceeds max_page_size_bytes."""
        mock_response = MagicMock()
        mock_response.headers = httpx.Headers({"content-length": "2048"})  # 2 KB > 1 KB limit
        mock_stream.return_value.__enter__.return_value = mock_response

        params = NavigationParams(url="https://huge-file.com")
        with self.assertRaises(FetchError) as ctx:
            self.fetcher.fetch(params)

        self.assertIn("exceeds maximum payload limit", str(ctx.exception))

    @patch("httpx.Client.stream")
    def test_streamed_content_limit_exceeded(self, mock_stream):
        """Test dynamic abort when streamed payload bytes exceed limit."""
        mock_response = MagicMock()
        mock_response.headers = httpx.Headers({})
        # Stream chunks total 2048 bytes > 1024 bytes limit
        mock_response.iter_bytes.return_value = [b"a" * 600, b"b" * 600]
        mock_stream.return_value.__enter__.return_value = mock_response

        params = NavigationParams(url="https://stream-overflow.com")
        with self.assertRaises(FetchError) as ctx:
            self.fetcher.fetch(params)

        self.assertIn("exceeded maximum size limit", str(ctx.exception))

    @patch("httpx.Client.stream")
    def test_retry_on_transient_503_error(self, mock_stream):
        """Test exponential backoff retries when encountering transient 503 status code."""
        # 1st call returns 503, 2nd call returns 200 OK
        mock_res_503 = MagicMock()
        mock_res_503.status_code = 503

        mock_res_200 = MagicMock()
        mock_res_200.status_code = 200
        mock_res_200.headers = httpx.Headers({"content-type": "text/html"})
        mock_res_200.iter_bytes.return_value = [b"Success after retry"]
        mock_res_200.encoding = "utf-8"
        mock_res_200.history = []
        mock_res_200.url = "https://retry-domain.com"

        ctx_503 = MagicMock()
        ctx_503.__enter__.return_value = mock_res_503

        ctx_200 = MagicMock()
        ctx_200.__enter__.return_value = mock_res_200

        mock_stream.side_effect = [ctx_503, ctx_200]

        params = NavigationParams(url="https://retry-domain.com")
        result = self.fetcher.fetch(params)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.text, "Success after retry")
        self.assertEqual(mock_stream.call_count, 2)

    def test_async_fetch_success(self):
        """Test async fetch functionality."""
        async def run_async_test():
            with patch("httpx.AsyncClient.stream") as mock_async_stream:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.headers = httpx.Headers({"content-type": "application/json"})
                
                async def mock_aiter(*args, **kwargs):
                    yield b'{"status": "ok"}'
                
                mock_response.aiter_bytes = mock_aiter
                mock_response.encoding = "utf-8"
                mock_response.history = []
                mock_response.url = "https://api.example.com/data"

                async_ctx = MagicMock()
                async_ctx.__aenter__.return_value = mock_response
                mock_async_stream.return_value = async_ctx

                params = NavigationParams(url="https://api.example.com/data")
                result = await self.fetcher.fetch_async(params)

                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.text, '{"status": "ok"}')
                self.assertEqual(result.mime_type, "application/json")

        asyncio.run(run_async_test())

    def test_fetcher_factory_strategy_pattern(self):
        """Test FetcherFactory strategy instantiation and custom strategy registration."""
        # Standard HTTP_BASIC strategy creation
        fetcher = FetcherFactory.create_fetcher(BrowserEngineType.HTTP_BASIC, self.config)
        self.assertIsInstance(fetcher, HTTPFetcher)

        # Register custom strategy
        FetcherFactory.register_fetcher("MOCK_CUSTOM", DummyMockFetcher)
        custom_fetcher = FetcherFactory.create_fetcher("MOCK_CUSTOM", self.config)
        self.assertIsInstance(custom_fetcher, DummyMockFetcher)

        res = custom_fetcher.fetch(NavigationParams(url="https://dummy.org"))
        self.assertIn("Dummy Strategy Response", res.text)

        # Unregistered strategy raises UnsupportedEngineError
        with self.assertRaises(UnsupportedEngineError):
            FetcherFactory.create_fetcher("UNKNOWN_STRATEGY")

    @patch("httpx.Client.stream")
    def test_browser_orchestrator_integration_with_http_fetcher(self, mock_stream):
        """Test end-to-end integration between Browser orchestrator and HTTPFetcher."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = httpx.Headers({"content-type": "text/html"})
        mock_response.iter_bytes.return_value = [b"<!DOCTYPE html><html><body>Integration Test</body></html>"]
        mock_response.encoding = "utf-8"
        mock_response.history = []
        mock_response.url = "https://integration.org"

        mock_stream.return_value.__enter__.return_value = mock_response

        # Instantiate Browser without explicit fetcher (auto-wires HTTPFetcher via FetcherFactory)
        browser = Browser(config=self.config)
        self.assertIsInstance(browser.fetcher, HTTPFetcher)

        response = browser.navigate("https://integration.org", keep_raw_html=True)

        self.assertIsInstance(response, BrowserResponse)
        self.assertEqual(response.url, "https://integration.org")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Integration Test", response.extracted_text)
        self.assertEqual(response.raw_html, "<!DOCTYPE html><html><body>Integration Test</body></html>")
        self.assertGreater(response.metrics.fetch_duration_ms, 0)

        browser.close()


if __name__ == "__main__":
    unittest.main()
