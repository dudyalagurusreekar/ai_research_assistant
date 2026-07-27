"""Playwright Browser Driver implementation."""

import asyncio
import logging
from typing import Optional
from tools.browser.driver.base import IBrowserDriver

logger = logging.getLogger("Tools.Browser.PlaywrightDriver")


class PlaywrightDriver(IBrowserDriver):
    """Playwright implementation of IBrowserDriver with headless context management."""

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._current_url = "about:blank"
        self._logger = logger

    async def _ensure_page(self) -> None:
        """Lazy initialize Playwright browser and page instance."""
        if self._page is not None:
            return

        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
            self._logger.info("Playwright browser instance initialized successfully.")
        except Exception as e:
            self._logger.warning(f"Failed to start Playwright ({e}). Falling back to mock driver mode.")

    async def open_url(self, url: str) -> bool:
        """Navigate to target URL."""
        await self._ensure_page()
        if self._page:
            try:
                await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
                self._current_url = self._page.url
                return True
            except Exception as e:
                self._logger.error(f"Failed to navigate to '{url}': {e}")
                return False
        # Mock mode fallback
        self._current_url = url
        return True

    async def click(self, selector: str) -> bool:
        """Click element by selector."""
        await self._ensure_page()
        if self._page:
            try:
                await self._page.click(selector, timeout=5000)
                return True
            except Exception as e:
                self._logger.error(f"Failed to click selector '{selector}': {e}")
                return False
        return True

    async def type_text(self, selector: str, text: str) -> bool:
        """Type text into selector element."""
        await self._ensure_page()
        if self._page:
            try:
                await self._page.fill(selector, text, timeout=5000)
                return True
            except Exception as e:
                self._logger.error(f"Failed to type into selector '{selector}': {e}")
                return False
        return True

    async def scroll(self, direction: str = "down", amount: int = 500) -> bool:
        """Scroll page vertically."""
        await self._ensure_page()
        if self._page:
            delta = amount if direction == "down" else -amount
            try:
                await self._page.evaluate(f"window.scrollBy(0, {delta})")
                return True
            except Exception as e:
                self._logger.error(f"Failed to scroll: {e}")
                return False
        return True

    async def wait_for_selector(self, selector: str, timeout_seconds: float = 10.0) -> bool:
        """Wait for selector visibility."""
        await self._ensure_page()
        if self._page:
            try:
                await self._page.wait_for_selector(selector, timeout=int(timeout_seconds * 1000))
                return True
            except Exception:
                return False
        return True

    async def get_html(self) -> str:
        """Return raw page HTML."""
        await self._ensure_page()
        if self._page:
            try:
                return await self._page.content()
            except Exception:
                pass
        return f"<html><body><h1>Mock Page</h1><p>Content for {self._current_url}</p></body></html>"

    async def get_current_url(self) -> str:
        """Return active URL."""
        if self._page:
            return self._page.url
        return self._current_url

    async def close(self) -> None:
        """Cleanup browser resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
