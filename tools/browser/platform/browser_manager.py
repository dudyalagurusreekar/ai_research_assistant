"""Browser Manager for Sprint 11 Browser Automation Platform."""

import logging
import asyncio
from typing import Any, Dict, Optional, List
from tools.browser.platform.models import BrowserConfig

logger = logging.getLogger("Tools.Browser.Platform.BrowserManager")


class BrowserManager:
    """Manages browser instance lifecycles, contexts, health checks, and fallback drivers."""

    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        self.config = config or BrowserConfig()
        self._playwright = None
        self._browser = None
        self._contexts: Dict[str, Any] = {}
        self._active = False
        self._is_mock_mode = False

    async def initialize(self) -> bool:
        """Initialize the browser instance."""
        if self._active and self._browser:
            return True

        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()

            browser_type_name = self.config.browser_type.lower()
            if browser_type_name == "firefox":
                launcher = self._playwright.firefox
            elif browser_type_name == "webkit":
                launcher = self._playwright.webkit
            else:
                launcher = self._playwright.chromium

            launch_kwargs: Dict[str, Any] = {
                "headless": self.config.headless,
            }
            if self.config.slow_mo_ms > 0:
                launch_kwargs["slow_mo"] = self.config.slow_mo_ms

            if self.config.proxy_url:
                launch_kwargs["proxy"] = {"server": self.config.proxy_url}

            self._browser = await launcher.launch(**launch_kwargs)
            self._active = True
            self._is_mock_mode = False
            logger.info(f"BrowserManager initialized with provider '{browser_type_name}' (headless={self.config.headless}).")
            return True
        except Exception as e:
            logger.warning(f"Playwright initialization failed ({e}). Enabling headless mock mode fallback.")
            self._is_mock_mode = True
            self._active = True
            return True

    @property
    def is_mock_mode(self) -> bool:
        """Returns True if running in fallback mock driver mode."""
        return self._is_mock_mode

    @property
    def is_active(self) -> bool:
        """Returns True if browser engine is active."""
        return self._active

    async def create_context(self, context_id: str = "default", user_agent: Optional[str] = None) -> Any:
        """Create an isolated browser context."""
        await self.initialize()

        if len(self._contexts) >= self.config.max_contexts:
            logger.warning(f"Max context limit ({self.config.max_contexts}) reached. Recycling oldest context.")
            oldest_key = next(iter(self._contexts))
            await self.close_context(oldest_key)

        if not self._is_mock_mode and self._browser:
            context_kwargs: Dict[str, Any] = {
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height,
                },
                "accept_downloads": self.config.accept_downloads,
            }
            ua = user_agent or self.config.user_agent
            if ua:
                context_kwargs["user_agent"] = ua

            context = await self._browser.new_context(**context_kwargs)
            self._contexts[context_id] = context
            return context

        # Mock Context Fallback
        mock_ctx = MockBrowserContext(context_id=context_id)
        self._contexts[context_id] = mock_ctx
        return mock_ctx

    def get_context(self, context_id: str = "default") -> Optional[Any]:
        """Get context by ID."""
        return self._contexts.get(context_id)

    async def close_context(self, context_id: str) -> bool:
        """Close context by ID."""
        if context_id in self._contexts:
            ctx = self._contexts.pop(context_id)
            if not self._is_mock_mode and hasattr(ctx, "close"):
                try:
                    await ctx.close()
                except Exception as e:
                    logger.error(f"Error closing context '{context_id}': {e}")
            return True
        return False

    async def check_health(self) -> Dict[str, Any]:
        """Return health status dictionary."""
        return {
            "active": self._active,
            "mock_mode": self._is_mock_mode,
            "active_contexts": len(self._contexts),
            "browser_type": self.config.browser_type,
            "headless": self.config.headless,
        }

    async def shutdown(self) -> None:
        """Shutdown browser manager and free resources."""
        for cid in list(self._contexts.keys()):
            await self.close_context(cid)

        if self._browser and not self._is_mock_mode:
            try:
                await self._browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

        if self._playwright and not self._is_mock_mode:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.error(f"Error stopping playwright: {e}")

        self._browser = None
        self._playwright = None
        self._active = False
        self._contexts.clear()
        logger.info("BrowserManager shutdown complete.")


class MockBrowserContext:
    """Mock context object for fallback execution mode."""

    def __init__(self, context_id: str = "default") -> None:
        self.context_id = context_id
        self._pages: List[Any] = [MockPage()]

    async def new_page() -> Any:
        p = MockPage()
        self._pages.append(p)
        return p

    @property
    def pages() -> List[Any]:
        return self._pages

    async def close() -> None:
        self._pages.clear()


class MockPage:
    """Mock page object for fallback execution mode."""

    def __init__(self) -> None:
        self.url = "about:blank"
        self._content = "<html><body><h1>Mock Page</h1></body></html>"

    async def goto(self, url: str, **kwargs) -> Any:
        self.url = url
        self._content = f"<html><body><h1>Mock Page</h1><p>Loaded {url}</p></body></html>"
        return None

    async def click(self, selector: str, **kwargs) -> None:
        pass

    async def fill(self, selector: str, value: str, **kwargs) -> None:
        pass

    async def content(self) -> str:
        return self._content

    async def close() -> None:
        pass
