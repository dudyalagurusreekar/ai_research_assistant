"""Navigation Engine for Sprint 11 Browser Automation Platform."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from tools.browser.platform.models import ActionResult, ActionType, WaitStrategy

logger = logging.getLogger("Tools.Browser.Platform.NavigationEngine")


class NavigationEngine:
    """Handles smart navigation, waiting strategies, tab management, infinite scroll, and retry loops."""

    def __init__(self, retries: int = 3, backoff_factor: float = 1.5) -> None:
        self.retries = retries
        self.backoff_factor = backoff_factor

    async def navigate(
        self,
        page: Any,
        url: str,
        wait_strategy: WaitStrategy = WaitStrategy.NETWORK_IDLE,
        timeout_ms: int = 30000,
    ) -> ActionResult:
        """Navigate to URL with retry logic and waiting strategy."""
        start_time = time.time()
        last_error = None

        for attempt in range(1, self.retries + 1):
            try:
                if hasattr(page, "goto"):
                    wait_until = "networkidle"
                    if wait_strategy == WaitStrategy.DOM_CONTENT_LOADED:
                        wait_until = "domcontentloaded"
                    elif wait_strategy == WaitStrategy.LOAD:
                        wait_until = "load"

                    await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                    current_url = getattr(page, "url", url)
                    exec_time = (time.time() - start_time) * 1000
                    return ActionResult(
                        success=True,
                        action_type=ActionType.NAVIGATE,
                        message=f"Successfully navigated to {current_url}",
                        url=current_url,
                        execution_time_ms=exec_time,
                        retry_count=attempt - 1,
                    )
                else:
                    # Mock mode page navigation
                    if hasattr(page, "url"):
                        page.url = url
                    exec_time = (time.time() - start_time) * 1000
                    return ActionResult(
                        success=True,
                        action_type=ActionType.NAVIGATE,
                        message=f"Mock navigated to {url}",
                        url=url,
                        execution_time_ms=exec_time,
                        retry_count=0,
                    )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Navigation attempt {attempt}/{self.retries} failed for '{url}': {e}")
                if attempt < self.retries:
                    sleep_time = (self.backoff_factor ** attempt) * 0.5
                    await asyncio.sleep(sleep_time)

        exec_time = (time.time() - start_time) * 1000
        return ActionResult(
            success=False,
            action_type=ActionType.NAVIGATE,
            message=f"Failed to navigate to {url} after {self.retries} attempts.",
            url=url,
            error=last_error,
            execution_time_ms=exec_time,
            retry_count=self.retries,
        )

    async def reload(self, page: Any, timeout_ms: int = 15000) -> ActionResult:
        """Reload active page."""
        start_time = time.time()
        try:
            if hasattr(page, "reload"):
                await page.reload(timeout=timeout_ms)
            current_url = getattr(page, "url", "about:blank")
            return ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                message="Page reloaded successfully.",
                url=current_url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                message=f"Failed to reload page: {e}",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def go_back(self, page: Any) -> ActionResult:
        """Navigate back in history."""
        start_time = time.time()
        try:
            if hasattr(page, "go_back"):
                await page.go_back()
            current_url = getattr(page, "url", "about:blank")
            return ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                message="Navigated back in browser history.",
                url=current_url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                message=f"Failed to navigate back: {e}",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def handle_infinite_scroll(self, page: Any, max_scrolls: int = 5, distance_px: int = 800) -> ActionResult:
        """Scroll page iteratively to load dynamic infinite-scroll content."""
        start_time = time.time()
        try:
            for i in range(max_scrolls):
                if hasattr(page, "evaluate"):
                    await page.evaluate(f"window.scrollBy(0, {distance_px})")
                await asyncio.sleep(0.5)

            current_url = getattr(page, "url", "about:blank")
            return ActionResult(
                success=True,
                action_type=ActionType.SCROLL,
                message=f"Completed {max_scrolls} infinite scroll sweeps.",
                url=current_url,
                execution_time_ms=(time.time() - start_time) * 1000,
                data={"max_scrolls": max_scrolls, "distance_px": distance_px},
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.SCROLL,
                message=f"Infinite scroll failed: {e}",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def wait_for_selector(self, page: Any, selector: str, timeout_ms: int = 10000) -> ActionResult:
        """Wait for selector presence/visibility."""
        start_time = time.time()
        try:
            if hasattr(page, "wait_for_selector"):
                await page.wait_for_selector(selector, timeout=timeout_ms)
            current_url = getattr(page, "url", "about:blank")
            return ActionResult(
                success=True,
                action_type=ActionType.WAIT_FOR_SELECTOR,
                message=f"Selector '{selector}' became visible.",
                url=current_url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.WAIT_FOR_SELECTOR,
                message=f"Timed out waiting for selector '{selector}'.",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )
