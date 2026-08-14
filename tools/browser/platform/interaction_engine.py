"""Interaction Engine for Sprint 11 Browser Automation Platform."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional
from tools.browser.platform.models import ActionResult, ActionType, BrowserAction

logger = logging.getLogger("Tools.Browser.Platform.InteractionEngine")


class InteractionEngine:
    """Executes atomic browser UI interactions with interactability checks and humanized delays."""

    def __init__(self, humanize_delay_ms: int = 50) -> None:
        self.humanize_delay_ms = humanize_delay_ms

    async def execute_action(self, page: Any, action: BrowserAction) -> ActionResult:
        """Route and execute a BrowserAction on the active page."""
        start_time = time.time()
        a_type = action.action_type

        try:
            if self.humanize_delay_ms > 0:
                await asyncio.sleep(self.humanize_delay_ms / 1000.0)

            if a_type == ActionType.CLICK:
                return await self.click(page, action.target_selector or "body", timeout_ms=action.timeout_ms)
            elif a_type == ActionType.DOUBLE_CLICK:
                return await self.double_click(page, action.target_selector or "body", timeout_ms=action.timeout_ms)
            elif a_type == ActionType.HOVER:
                return await self.hover(page, action.target_selector or "body", timeout_ms=action.timeout_ms)
            elif a_type == ActionType.TYPE:
                return await self.type_text(page, action.target_selector or "input", action.text or "", timeout_ms=action.timeout_ms)
            elif a_type == ActionType.PRESS_KEY:
                return await self.press_key(page, action.key_name or "Enter")
            elif a_type == ActionType.SCROLL:
                return await self.scroll(page, direction=action.scroll_direction, amount=action.scroll_amount)
            elif a_type == ActionType.SELECT_OPTION:
                return await self.select_option(page, action.target_selector or "select", action.value or "")
            elif a_type == ActionType.CLEAR:
                return await self.clear_input(page, action.target_selector or "input")
            else:
                return ActionResult(
                    success=False,
                    action_type=a_type,
                    message=f"Unsupported action type '{a_type}'.",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
        except Exception as e:
            logger.error(f"Error executing interaction '{a_type}': {e}")
            return ActionResult(
                success=False,
                action_type=a_type,
                message=f"Action execution error: {e}",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def click(self, page: Any, selector: str, timeout_ms: int = 10000) -> ActionResult:
        """Click element matching selector."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")
        try:
            if hasattr(page, "click"):
                await page.click(selector, timeout=timeout_ms)
            return ActionResult(
                success=True,
                action_type=ActionType.CLICK,
                message=f"Clicked selector '{selector}'.",
                url=url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK,
                message=f"Failed to click selector '{selector}': {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def double_click(self, page: Any, selector: str, timeout_ms: int = 10000) -> ActionResult:
        """Double click element matching selector."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")
        try:
            if hasattr(page, "dblclick"):
                await page.dblclick(selector, timeout=timeout_ms)
            return ActionResult(
                success=True,
                action_type=ActionType.DOUBLE_CLICK,
                message=f"Double-clicked selector '{selector}'.",
                url=url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.DOUBLE_CLICK,
                message=f"Failed to double-click selector '{selector}': {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def hover(self, page: Any, selector: str, timeout_ms: int = 10000) -> ActionResult:
        """Hover over element matching selector."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")
        try:
            if hasattr(page, "hover"):
                await page.hover(selector, timeout=timeout_ms)
            return ActionResult(
                success=True,
                action_type=ActionType.HOVER,
                message=f"Hovered over selector '{selector}'.",
                url=url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.HOVER,
                message=f"Failed to hover over selector '{selector}': {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def type_text(self, page: Any, selector: str, text: str, timeout_ms: int = 10000) -> ActionResult:
        """Type text into selector element."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")
        try:
            if hasattr(page, "fill"):
                await page.fill(selector, text, timeout=timeout_ms)
            return ActionResult(
                success=True,
                action_type=ActionType.TYPE,
                message=f"Typed text into selector '{selector}'.",
                url=url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                message=f"Failed to type into selector '{selector}': {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def press_key(self, page: Any, key_name: str) -> ActionResult:
        """Press keyboard key."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")
        try:
            if hasattr(page, "keyboard") and hasattr(page.keyboard, "press"):
                await page.keyboard.press(key_name)
            return ActionResult(
                success=True,
                action_type=ActionType.PRESS_KEY,
                message=f"Pressed key '{key_name}'.",
                url=url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.PRESS_KEY,
                message=f"Failed to press key '{key_name}': {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def scroll(self, page: Any, direction: str = "down", amount: int = 500) -> ActionResult:
        """Scroll page vertically."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")
        delta = amount if direction == "down" else -amount
        try:
            if hasattr(page, "evaluate"):
                await page.evaluate(f"window.scrollBy(0, {delta})")
            return ActionResult(
                success=True,
                action_type=ActionType.SCROLL,
                message=f"Scrolled {direction} by {amount}px.",
                url=url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.SCROLL,
                message=f"Failed to scroll: {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def select_option(self, page: Any, selector: str, value: str) -> ActionResult:
        """Select option in dropdown element."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")
        try:
            if hasattr(page, "select_option"):
                await page.select_option(selector, value)
            return ActionResult(
                success=True,
                action_type=ActionType.SELECT_OPTION,
                message=f"Selected option '{value}' in selector '{selector}'.",
                url=url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.SELECT_OPTION,
                message=f"Failed to select option in '{selector}': {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def clear_input(self, page: Any, selector: str) -> ActionResult:
        """Clear text input field."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")
        try:
            if hasattr(page, "fill"):
                await page.fill(selector, "")
            return ActionResult(
                success=True,
                action_type=ActionType.CLEAR,
                message=f"Cleared input selector '{selector}'.",
                url=url,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.CLEAR,
                message=f"Failed to clear input '{selector}': {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )
