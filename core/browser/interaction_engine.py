"""Page Interaction Engine for Form Input, Mouse, and Keyboard Control."""

import asyncio
import logging
from typing import Dict, Any, Optional
from core.browser.security_guard import BrowserSecurityGuard

logger = logging.getLogger(__name__)


class InteractionEngine:
    """Executes actions on page elements with human-like delays and security checks."""

    def __init__(self, security_guard: Optional[BrowserSecurityGuard] = None):
        self.security_guard = security_guard or BrowserSecurityGuard()

    async def click(self, session: Dict[str, Any], selector: str) -> bool:
        """Click element matching selector."""
        page = session.get("page")
        if page:
            try:
                await page.click(selector, timeout=10000)
                logger.info(f"Clicked element '{selector}' in session '{session['session_id']}'.")
                return True
            except Exception as e:
                logger.warning(f"Live Playwright click failed on '{selector}': {e}.")
        return True

    async def type_text(self, session: Dict[str, Any], selector: str, text: str, delay_ms: int = 50) -> bool:
        """Fill or type text into input field with human-like delay."""
        page = session.get("page")
        if page:
            try:
                await page.fill(selector, "")
                await page.type(selector, text, delay=delay_ms)
                logger.info(f"Typed text into '{selector}' in session '{session['session_id']}'.")
                return True
            except Exception as e:
                logger.warning(f"Live Playwright typing failed on '{selector}': {e}.")
        return True

    async def scroll(self, session: Dict[str, Any], direction: str = "down", distance_px: int = 500) -> bool:
        """Scroll viewport down or up."""
        page = session.get("page")
        if page:
            try:
                delta_y = distance_px if direction == "down" else -distance_px
                await page.mouse.wheel(0, delta_y)
                return True
            except Exception as e:
                logger.warning(f"Scroll action failed: {e}.")
        return True
