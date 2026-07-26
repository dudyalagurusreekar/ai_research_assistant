"""Playwright Network Fetcher Adapter for the Browser Tool Subsystem.

Following the Adapter and Strategy engineering patterns, this fetcher wraps the
`BrowserAutomationEngine` to provide a `BaseFetcher`-compatible interface, rendering
JavaScript-rich dynamic SPA web pages and returning a `FetchResult` for Content Routing.
"""

import time
from typing import Optional
from tools.browser.config import BrowserConfig
from tools.browser.core.base_fetcher import BaseFetcher
from tools.browser.models.request import NavigationParams
from tools.browser.models.response import FetchResult
from tools.browser.automation.engine import BrowserAutomationEngine
from tools.browser.automation.exceptions import AutomationError
from tools.browser.exceptions import FetchError, TimeoutError as BrowserTimeoutError
from tools.browser.utils.logging import get_browser_logger


class PlaywrightFetcher(BaseFetcher):
    """Network fetcher adapter utilizing Playwright browser engine rendering."""

    def __init__(
        self,
        config: BrowserConfig,
        automation_engine: Optional[BrowserAutomationEngine] = None,
    ) -> None:
        """Initialize PlaywrightFetcher adapter.

        Args:
            config (BrowserConfig): Central browser configuration container.
            automation_engine (Optional[BrowserAutomationEngine]): Injected automation engine.
        """
        super().__init__(config)
        self.automation_engine = automation_engine or BrowserAutomationEngine(config=config)
        self._logger = get_browser_logger("PlaywrightFetcher")

    def fetch(self, params: NavigationParams) -> FetchResult:
        """Fetch and render page content synchronously.

        Args:
            params (NavigationParams): Navigation details.

        Returns:
            FetchResult: Rendered HTML content encapsulated in FetchResult.
        """
        start_time = time.time()
        try:
            nav_info = self.automation_engine.open_page(
                url=params.url,
                timeout=params.timeout or self.config.timeout_seconds,
            )
            html_source = self.automation_engine.get_page_source()
            content_bytes = html_source.encode("utf-8")
            elapsed_ms = (time.time() - start_time) * 1000.0

            return FetchResult(
                url=nav_info.get("url", params.url),
                status_code=nav_info.get("status_code", 200),
                headers={"content-type": "text/html; charset=utf-8"},
                content=content_bytes,
                encoding="utf-8",
                mime_type="text/html",
                response_time_ms=elapsed_ms,
                success=nav_info.get("success", True),
            )
        except BrowserTimeoutError as e:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return FetchResult(
                url=params.url,
                status_code=408,
                content=b"",
                mime_type="text/html",
                response_time_ms=elapsed_ms,
                success=False,
                error_message=str(e),
            )
        except (AutomationError, Exception) as e:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return FetchResult(
                url=params.url,
                status_code=500,
                content=b"",
                mime_type="text/html",
                response_time_ms=elapsed_ms,
                success=False,
                error_message=f"Playwright rendering failed: {e}",
            )

    async def fetch_async(self, params: NavigationParams) -> FetchResult:
        """Fetch and render page content asynchronously.

        Args:
            params (NavigationParams): Navigation details.

        Returns:
            FetchResult: Rendered HTML content encapsulated in FetchResult.
        """
        start_time = time.time()
        try:
            nav_info = await self.automation_engine.open_page_async(
                url=params.url,
                timeout=params.timeout or self.config.timeout_seconds,
            )
            html_source = await self.automation_engine.get_page_source_async()
            content_bytes = html_source.encode("utf-8")
            elapsed_ms = (time.time() - start_time) * 1000.0

            return FetchResult(
                url=nav_info.get("url", params.url),
                status_code=nav_info.get("status_code", 200),
                headers={"content-type": "text/html; charset=utf-8"},
                content=content_bytes,
                encoding="utf-8",
                mime_type="text/html",
                response_time_ms=elapsed_ms,
                success=nav_info.get("success", True),
            )
        except BrowserTimeoutError as e:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return FetchResult(
                url=params.url,
                status_code=408,
                content=b"",
                mime_type="text/html",
                response_time_ms=elapsed_ms,
                success=False,
                error_message=str(e),
            )
        except (AutomationError, Exception) as e:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return FetchResult(
                url=params.url,
                status_code=500,
                content=b"",
                mime_type="text/html",
                response_time_ms=elapsed_ms,
                success=False,
                error_message=f"Playwright rendering failed: {e}",
            )

    def close(self) -> None:
        """Close automation engine resources."""
        if self.automation_engine:
            self.automation_engine.close()

    async def aclose(self) -> None:
        """Close automation engine resources asynchronously."""
        if self.automation_engine:
            await self.automation_engine.aclose()
