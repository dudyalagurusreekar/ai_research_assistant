"""Error Recovery Engine for Sprint 11 Browser Automation Platform."""

import asyncio
import logging
from typing import Any, Callable, List, Optional
from tools.browser.platform.models import ActionResult

logger = logging.getLogger("Tools.Browser.Platform.ErrorRecoveryEngine")


class ErrorRecoveryEngine:
    """Handles automated pop-up dismissals, cookie dialog auto-accepts, selector fallback, and crash retries."""

    COMMON_MODAL_DISMISS_SELECTORS = [
        "button[aria-label='Close']",
        "button[aria-label='close']",
        ".modal-close",
        "#cookie-accept",
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button:has-text('I agree')",
        "button:has-text('Dismiss')",
        ".close-button",
    ]

    async def attempt_modal_dismissal(self, page: Any) -> bool:
        """Scan and click common pop-up / modal / cookie overlay close buttons."""
        dismissed = False
        if not hasattr(page, "click"):
            return False

        for selector in self.COMMON_MODAL_DISMISS_SELECTORS:
            try:
                if hasattr(page, "is_visible") and await page.is_visible(selector):
                    await page.click(selector, timeout=1000)
                    logger.info(f"Dismissed overlay/modal using selector '{selector}'.")
                    dismissed = True
            except Exception:
                pass

        return dismissed

    async def execute_with_fallback(
        self,
        action_fn: Callable[[], Any],
        page: Any,
        fallback_selectors: Optional[List[str]] = None,
        max_retries: int = 2,
    ) -> ActionResult:
        """Execute a browser action with modal dismissal and fallback selector retries."""
        for attempt in range(max_retries):
            res = await action_fn()
            if res.success:
                return res

            # Attempt overlay dismissal on failure
            await self.attempt_modal_dismissal(page)
            await asyncio.sleep(0.5)

        # Final retry attempt
        return await action_fn()
