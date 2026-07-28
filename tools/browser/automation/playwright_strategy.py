"""Playwright Concrete Strategy Implementation for Dynamic Browser Automation.

This module implements `PlaywrightStrategy`, wrapping the `playwright.async_api` engine.
Follows SOLID principles, Adapter Pattern, and Strategy Pattern to expose full-featured
browser manipulation, DOM rendering, network interception, dialog handling, and session state.
"""

import os
import re
import json
import pathlib
from typing import Dict, Any, List, Optional, Union
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

from tools.browser.config import BrowserConfig
from tools.browser.automation.base import AutomationStrategy
from tools.browser.automation.models import ElementSpec, SessionState, NetworkRequestLog, NetworkResponseLog, DialogLog
from tools.browser.automation.observer import NetworkObserver
from tools.browser.automation.exceptions import (
    AutomationError,
    ElementNotFoundError,
    InteractionError,
    ScriptExecutionError,
    SessionError,
    DownloadError,
    UploadError,
)
from tools.browser.exceptions import TimeoutError as BrowserTimeoutError
from tools.browser.constants import DEFAULT_SCREENSHOT_TIMEOUT_MS
from tools.browser.utils.logging import get_browser_logger


class PlaywrightStrategy(AutomationStrategy):
    """Playwright rendering engine strategy implementation using async_api."""

    def __init__(self, config: BrowserConfig) -> None:
        """Initialize strategy with configuration container."""
        super().__init__(config)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self.observer = NetworkObserver()
        self._logger = get_browser_logger("PlaywrightStrategy")

    async def initialize(self) -> None:
        """Launch Playwright browser process, initialize context and active page."""
        if self._page and not self._page.is_closed():
            return

        try:
            self._logger.info(f"Initializing Playwright engine ({self.config.playwright_browser_type}, headless={self.config.headless})")
            self._playwright = await async_playwright().start()

            browser_type_name = self.config.playwright_browser_type.lower()
            if hasattr(self._playwright, browser_type_name):
                browser_type = getattr(self._playwright, browser_type_name)
            else:
                browser_type = self._playwright.chromium

            launch_kwargs: Dict[str, Any] = {
                "headless": self.config.headless,
                "args": self.config.playwright_launch_args,
            }

            self._browser = await browser_type.launch(**launch_kwargs)

            # Build context parameters
            context_kwargs: Dict[str, Any] = {
                "user_agent": self.config.user_agent,
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height,
                },
                "ignore_https_errors": self.config.ignore_https_errors,
                "accept_downloads": True,
            }

            if self.config.storage_state_path and os.path.exists(self.config.storage_state_path):
                context_kwargs["storage_state"] = self.config.storage_state_path
                self._logger.info(f"Loaded storage state from '{self.config.storage_state_path}'")

            self._context = await self._browser.new_context(**context_kwargs)
            self._page = await self._context.new_page()

            # Attach observers
            self._attach_listeners(self._page)

        except Exception as e:
            self._logger.error(f"Failed to initialize Playwright browser engine: {e}")
            await self.close()
            raise AutomationError(f"Failed to initialize Playwright engine: {e}")

    def _attach_listeners(self, page: Page) -> None:
        """Attach network, console, error, and dialog observers to page instance."""
        page.on("request", lambda req: self.observer.record_request(
            NetworkRequestLog(
                url=req.url,
                method=req.method,
                headers=dict(req.headers),
                resource_type=req.resource_type,
            )
        ))

        page.on("response", lambda res: self.observer.record_response(
            NetworkResponseLog(
                url=res.url,
                status=res.status,
                headers=dict(res.headers),
                mime_type=res.headers.get("content-type", "unknown"),
            )
        ))

        page.on("dialog", lambda dialog: self._handle_dialog(dialog))
        page.on("console", lambda msg: self.observer.record_console(msg.type, msg.text, str(msg.location)))
        page.on("pageerror", lambda err: self.observer.record_page_error(str(err)))

    async def _handle_dialog(self, dialog: Any) -> None:
        """Handle JavaScript dialog windows (alerts, confirms, prompts)."""
        dialog_type = dialog.type
        msg = dialog.message
        default_val = dialog.default_value
        action_taken = "dismissed"

        try:
            # Auto-accept alerts, confirm dialogs, and prompts
            await dialog.accept()
            action_taken = "accepted"
        except Exception:
            try:
                await dialog.dismiss()
                action_taken = "dismissed"
            except Exception:
                pass

        self.observer.record_dialog(
            DialogLog(
                type=dialog_type,
                message=msg,
                default_value=default_val,
                action_taken=action_taken,
            )
        )

    async def navigate(
        self,
        url: str,
        wait_until: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Navigate to URL in page."""
        await self.initialize()
        assert self._page is not None

        wait_cond = wait_until or self.config.wait_until
        timeout_ms = (timeout or self.config.navigation_timeout_seconds) * 1000.0

        try:
            self._logger.info(f"Navigating to '{url}' (wait_until={wait_cond}, timeout={timeout_ms}ms)")
            response = await self._page.goto(url, wait_until=wait_cond, timeout=timeout_ms)
            status_code = response.status if response else 200
            page_title = await self._page.title()
            current_url = self._page.url

            return {
                "url": current_url,
                "status_code": status_code,
                "title": page_title,
                "success": status_code < 400,
            }
        except PlaywrightTimeoutError as e:
            self._logger.error(f"Navigation to '{url}' timed out: {e}")
            raise BrowserTimeoutError(f"Navigation timed out after {timeout_ms/1000.0}s for '{url}'", url=url)
        except PlaywrightError as e:
            self._logger.error(f"Navigation failed for '{url}': {e}")
            raise AutomationError(f"Navigation failed: {e}", url=url)

    async def click(
        self,
        selector: str,
        timeout: Optional[float] = None,
        force: bool = False,
    ) -> bool:
        """Click element matching selector."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            await self._page.click(selector, timeout=timeout_ms, force=force)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Element selector '{selector}' not found or clickable within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Click failed on selector '{selector}': {e}", selector=selector)

    async def double_click(
        self,
        selector: str,
        timeout: Optional[float] = None,
        force: bool = False,
    ) -> bool:
        """Double click element matching selector."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            await self._page.dblclick(selector, timeout=timeout_ms, force=force)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Element selector '{selector}' not found or double-clickable within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Double click failed on selector '{selector}': {e}", selector=selector)

    async def hover(
        self,
        selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Hover over element matching selector."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            await self._page.hover(selector, timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Element selector '{selector}' not found or hoverable within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Hover failed on selector '{selector}': {e}", selector=selector)

    async def clear_input(
        self,
        selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Clear text input field matching selector."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            await self._page.locator(selector).clear(timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Element selector '{selector}' not found within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Clear failed on selector '{selector}': {e}", selector=selector)

    async def press_key(
        self,
        selector: str,
        key: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Simulate pressing a key on element matching selector."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            await self._page.press(selector, key, timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Element selector '{selector}' not found within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Press key '{key}' failed on selector '{selector}': {e}", selector=selector)

    async def check_checkbox(
        self,
        selector: str,
        checked: bool = True,
        timeout: Optional[float] = None,
    ) -> bool:
        """Set checkbox or radio button checked state, obeying HTML standards for radios."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            loc = self._page.locator(selector).first
            is_radio = await loc.evaluate("el => el.type === 'radio'")
            if is_radio and not checked:
                self._logger.warning(f"Attempting to uncheck a radio button on selector '{selector}', which is not supported in HTML.")
                return True
            await loc.set_checked(checked, timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Element selector '{selector}' not found within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Check checkbox failed on selector '{selector}': {e}", selector=selector)

    async def wait_for_navigation(
        self,
        wait_until: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Wait for navigation to complete."""
        await self.initialize()
        assert self._page is not None

        wait_cond = wait_until or self.config.wait_until
        timeout_ms = (timeout or self.config.navigation_timeout_seconds) * 1000.0
        try:
            self._logger.info(f"Waiting for navigation (wait_until={wait_cond}, timeout={timeout_ms}ms)")
            if hasattr(self._page, "wait_for_navigation"):
                response = await self._page.wait_for_navigation(wait_until=wait_cond, timeout=timeout_ms)
                status_code = response.status if response else 200
            else:
                wait_cond_state = "load" if wait_cond == "commit" else wait_cond
                await self._page.wait_for_load_state(state=wait_cond_state, timeout=timeout_ms)
                status_code = 200
            page_title = await self._page.title()
            current_url = self._page.url

            return {
                "url": current_url,
                "status_code": status_code,
                "title": page_title,
                "success": status_code < 400,
            }
        except PlaywrightTimeoutError:
            raise BrowserTimeoutError(f"Navigation wait timed out after {timeout_ms/1000.0}s", url=self._page.url)
        except PlaywrightError as e:
            raise AutomationError(f"Navigation wait failed: {e}")

    async def type_text(
        self,
        selector: str,
        text: str,
        clear_first: bool = True,
        timeout: Optional[float] = None,
    ) -> bool:
        """Type text into input element simulating character-by-character keyboard entries."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            loc = self._page.locator(selector).first
            if clear_first:
                await loc.clear(timeout=timeout_ms)
            
            # Simulate key presses character by character to trigger keyboard event listeners
            if hasattr(loc, "press_sequentially"):
                await loc.press_sequentially(text, timeout=timeout_ms)
            else:
                await loc.type(text, timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Target input element '{selector}' not found within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Failed typing text into '{selector}': {e}", selector=selector)

    async def fill_input(
        self,
        selector: str,
        text: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Directly fill text into input field using Playwright's fast fill API."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            await self._page.locator(selector).first.fill(text, timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Target input element '{selector}' not found within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Failed filling text into '{selector}': {e}", selector=selector)

    async def fill_form(
        self,
        field_values: Dict[str, str],
        submit_selector: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Fill multiple fields and optionally click submit."""
        await self.initialize()
        for sel, val in field_values.items():
            await self.fill_input(sel, val, timeout=timeout)

        if submit_selector:
            await self.click(submit_selector, timeout=timeout)
        return True

    async def select_option(
        self,
        selector: str,
        value: Union[str, List[str]],
        timeout: Optional[float] = None,
    ) -> bool:
        """Select value, index, label, or multiple options in a dropdown select element."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        
        # Normalize to list of values/labels/indices
        values = [value] if isinstance(value, str) else value
        option_specs = []
        for val in values:
            if isinstance(val, str) and val.startswith("label:"):
                option_specs.append({"label": val[6:]})
            elif isinstance(val, str) and val.startswith("index:"):
                option_specs.append({"index": int(val[6:])})
            else:
                option_specs.append({"value": val})

        try:
            loc = self._page.locator(selector).first
            if len(option_specs) == 1:
                spec = option_specs[0]
                if "label" in spec:
                    await loc.select_option(label=spec["label"], timeout=timeout_ms)
                elif "index" in spec:
                    await loc.select_option(index=spec["index"], timeout=timeout_ms)
                else:
                    try:
                        await loc.select_option(value=spec["value"], timeout=timeout_ms)
                    except PlaywrightError:
                        await loc.select_option(label=spec["value"], timeout=timeout_ms)
            else:
                await loc.select_option(option_specs, timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Select element '{selector}' not found within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Selecting option(s) '{value}' in '{selector}' failed: {e}", selector=selector)

    async def take_screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False,
        selector: Optional[str] = None,
    ) -> bytes:
        """Take PNG screenshot of viewport, full document height, or specific cropped element."""
        await self.initialize()
        assert self._page is not None

        import time as py_time
        out_path = path or os.path.join(self.config.screenshot_dir, f"screenshot_{int(py_time.time())}.png")
        pathlib.Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)

        if selector:
            try:
                img_bytes = await self._page.locator(selector).first.screenshot(path=out_path, timeout=DEFAULT_SCREENSHOT_TIMEOUT_MS)
            except PlaywrightTimeoutError:
                raise ElementNotFoundError(f"Element '{selector}' not found for screenshot", selector=selector)
            except PlaywrightError as e:
                raise InteractionError(f"Element screenshot failed for '{selector}': {e}", selector=selector)
        else:
            try:
                img_bytes = await self._page.screenshot(path=out_path, full_page=full_page, timeout=DEFAULT_SCREENSHOT_TIMEOUT_MS)
            except (PlaywrightTimeoutError, PlaywrightError) as e:
                if full_page:
                    self._logger.warning(f"Full-page screenshot failed: {e}. Retrying with viewport-only screenshot.")
                    try:
                        img_bytes = await self._page.screenshot(path=out_path, full_page=False, timeout=DEFAULT_SCREENSHOT_TIMEOUT_MS)
                    except PlaywrightError as e2:
                        raise InteractionError(f"Fallback viewport screenshot also failed: {e2}")
                else:
                    raise InteractionError(f"Screenshot failed: {e}")

        self._logger.info(f"Saved screenshot to '{out_path}'")
        return img_bytes

    async def wait_for_function(
        self,
        script: str,
        arg: Any = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Wait until custom JavaScript function/expression evaluates to truthy value."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            handle = await self._page.wait_for_function(script, arg=arg, timeout=timeout_ms)
            return await handle.json_value()
        except PlaywrightTimeoutError:
            raise BrowserTimeoutError(f"wait_for_function timed out after {timeout_ms/1000.0}s for script: '{script}'", url=self._page.url)
        except PlaywrightError as e:
            raise ScriptExecutionError(f"wait_for_function failed: {e}", script=script)

    async def wait_for_url(
        self,
        url_pattern: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait until page URL matches target pattern string."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            if isinstance(url_pattern, str):
                if url_pattern.startswith("http://") or url_pattern.startswith("https://"):
                    pattern = url_pattern
                else:
                    pattern = re.compile(f".*{re.escape(url_pattern)}.*")
            else:
                pattern = url_pattern
            await self._page.wait_for_url(pattern, timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise BrowserTimeoutError(f"wait_for_url timed out waiting for '{url_pattern}' after {timeout_ms/1000.0}s", url=self._page.url)
        except PlaywrightError as e:
            raise AutomationError(f"wait_for_url failed: {e}")

    async def wait_for_network_idle(
        self,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait until network requests settle to idle state."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            await self._page.wait_for_load_state(state="networkidle", timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise BrowserTimeoutError(f"wait_for_network_idle timed out after {timeout_ms/1000.0}s", url=self._page.url)
        except PlaywrightError as e:
            raise AutomationError(f"wait_for_network_idle failed: {e}")

    async def get_console_logs(self) -> List[Dict[str, Any]]:
        """Retrieve recorded browser console messages log."""
        summary = self.observer.get_summary()
        return summary.get("console_logs", [])

    async def submit_form(
        self,
        selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Submit a form element or click form submit button."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            loc = self._page.locator(selector).first
            tag_name = await loc.evaluate("el => el.tagName.toLowerCase()")
            if tag_name == "form":
                await loc.evaluate("form => form.requestSubmit ? form.requestSubmit() : form.submit()")
            else:
                await loc.click(timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Form element '{selector}' not found within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise InteractionError(f"Submit form failed on '{selector}': {e}", selector=selector)

    async def scroll(
        self,
        direction: str = "down",
        amount: int = 500,
        selector: Optional[str] = None,
    ) -> bool:
        """Scroll page window or container element."""
        return await self.scroll_to(direction=direction, amount=amount, selector=selector)

    async def scroll_to(
        self,
        direction: str = "down",
        amount: int = 500,
        selector: Optional[str] = None,
    ) -> bool:
        """Scroll page viewport or scrollable container element/scroll element into view."""
        await self.initialize()
        assert self._page is not None
        try:
            direction_lower = direction.strip().lower()
            if direction_lower == "into_view":
                if not selector:
                    from tools.browser.exceptions import ValidationError
                    raise ValidationError("Selector is required to scroll an element into view.")
                await self._page.locator(selector).first.scroll_into_view_if_needed()
                return True

            if selector:
                loc = self._page.locator(selector).first
                if direction_lower == "down":
                    await loc.evaluate(f"el => el.scrollTop += {amount}")
                elif direction_lower == "up":
                    await loc.evaluate(f"el => el.scrollTop -= {amount}")
                elif direction_lower == "left":
                    await loc.evaluate(f"el => el.scrollLeft -= {amount}")
                elif direction_lower == "right":
                    await loc.evaluate(f"el => el.scrollLeft += {amount}")
                elif direction_lower == "top":
                    await loc.evaluate("el => el.scrollTop = 0")
                elif direction_lower == "bottom":
                    await loc.evaluate("el => el.scrollTop = el.scrollHeight")
            else:
                if direction_lower == "down":
                    await self._page.evaluate(f"window.scrollBy(0, {amount})")
                elif direction_lower == "up":
                    await self._page.evaluate(f"window.scrollBy(0, -{amount})")
                elif direction_lower == "left":
                    await self._page.evaluate(f"window.scrollBy(-{amount}, 0)")
                elif direction_lower == "right":
                    await self._page.evaluate(f"window.scrollBy({amount}, 0)")
                elif direction_lower == "top":
                    await self._page.evaluate("window.scrollTo(0, 0)")
                elif direction_lower == "bottom":
                    await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            return True
        except PlaywrightError as e:
            raise InteractionError(f"Scroll action failed: {e}")

    async def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[float] = None,
    ) -> ElementSpec:
        """Wait for element matching selector to reach state."""
        await self.initialize()
        assert self._page is not None

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            loc = self._page.locator(selector).first
            await loc.wait_for(state=state, timeout=timeout_ms)
            is_vis = await loc.is_visible()
            tag_name = await loc.evaluate("el => el.tagName.toLowerCase()")
            return ElementSpec(selector=selector, tag_name=tag_name, is_visible=is_vis)
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"Element selector '{selector}' did not reach state '{state}' within {timeout_ms/1000.0}s", selector=selector)
        except PlaywrightError as e:
            raise AutomationError(f"wait_for_element failed for selector '{selector}': {e}")

    async def execute_js(self, script: str, arg: Any = None) -> Any:
        """Execute custom JS in page context."""
        return await self.execute_script(script, arg=arg)

    async def execute_script(self, script: str, arg: Any = None) -> Any:
        """Execute custom JS in page context."""
        await self.initialize()
        assert self._page is not None
        try:
            return await self._page.evaluate(script, arg)
        except PlaywrightError as e:
            raise ScriptExecutionError(f"JavaScript execution failed: {e}", script=script)

    async def capture_pdf(self, path: Optional[str] = None) -> bytes:
        """Capture page view as PDF document."""
        await self.initialize()
        assert self._page is not None
        out_path = path or os.path.join(self.config.screenshot_dir, f"page_{int(os.times().elapsed)}.pdf")
        pathlib.Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
        try:
            pdf_bytes = await self._page.pdf(path=out_path)
            return pdf_bytes
        except PlaywrightError as e:
            raise AutomationError(f"PDF capture failed: {e}")

    async def download_file(
        self,
        trigger_selector: str,
        download_dir: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Click element triggering file download, save locally, and verify size and presence on disk."""
        await self.initialize()
        assert self._page is not None

        target_dir = download_dir or self.config.download_dir
        pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0

        try:
            async with self._page.expect_download(timeout=timeout_ms) as download_info:
                await self._page.click(trigger_selector, timeout=timeout_ms)
            download = await download_info.value
            file_name = download.suggested_filename
            save_path = os.path.abspath(os.path.join(target_dir, file_name))
            await download.save_as(save_path)

            # Success Verification: check if file exists and has content
            if not os.path.exists(save_path):
                raise DownloadError(f"Downloaded file was not saved to destination: '{save_path}'", selector=trigger_selector)
            
            file_size = os.path.getsize(save_path)
            if file_size == 0:
                raise DownloadError(f"Downloaded file at '{save_path}' is empty (0 bytes).", selector=trigger_selector)

            return {
                "suggested_filename": file_name,
                "path": save_path,
                "url": download.url,
                "size_bytes": file_size,
            }
        except PlaywrightTimeoutError:
            raise BrowserTimeoutError(f"Download timed out after {timeout_ms/1000.0}s on '{trigger_selector}'", url=self._page.url)
        except PlaywrightError as e:
            raise InteractionError(f"Download failed on '{trigger_selector}': {e}", selector=trigger_selector)

    async def upload_file(
        self,
        selector: str,
        files: Union[str, List[str]],
        timeout: Optional[float] = None,
    ) -> bool:
        """Upload local file(s) into file input element, resolving to absolute paths."""
        await self.initialize()
        assert self._page is not None

        file_list = [files] if isinstance(files, str) else files
        resolved_files = []
        for fpath in file_list:
            abs_path = os.path.abspath(fpath)
            if not os.path.exists(abs_path):
                raise UploadError(f"Local file to upload does not exist: '{abs_path}'", selector=selector)
            resolved_files.append(abs_path)

        # Convert back to original parameter shape (string or list of strings)
        upload_input = resolved_files if not isinstance(files, str) else resolved_files[0]

        timeout_ms = (timeout or self.config.timeout_seconds) * 1000.0
        try:
            await self._page.set_input_files(selector, upload_input, timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            raise ElementNotFoundError(f"File input '{selector}' not found for upload", selector=selector)
        except PlaywrightError as e:
            raise UploadError(f"File upload failed for '{selector}': {e}", selector=selector)

    async def get_page_source(self) -> str:
        """Retrieve rendered HTML DOM source."""
        await self.initialize()
        assert self._page is not None
        return await self._page.content()

    async def get_url(self) -> str:
        """Retrieve page URL."""
        await self.initialize()
        assert self._page is not None
        return self._page.url

    async def get_title(self) -> str:
        """Retrieve page title."""
        await self.initialize()
        assert self._page is not None
        return await self._page.title()

    async def get_cookies(self) -> List[Dict[str, Any]]:
        """Get context cookies."""
        await self.initialize()
        assert self._context is not None
        return await self._context.cookies()

    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Set context cookies."""
        await self.initialize()
        assert self._context is not None
        await self._context.add_cookies(cookies)

    async def export_storage_state(self, path: Optional[str] = None) -> SessionState:
        """Export state to file or SessionState DTO."""
        await self.initialize()
        assert self._context is not None

        out_path = path or self.config.storage_state_path
        raw_state = await self._context.storage_state(path=out_path)

        state_dto = SessionState(
            cookies=raw_state.get("cookies", []),
            origins=raw_state.get("origins", []),
        )

        if out_path:
            self._logger.info(f"Exported session storage state to '{out_path}'")
        return state_dto

    async def import_storage_state(self, state: Union[str, Dict[str, Any], SessionState]) -> None:
        """Import storage state into context."""
        await self.initialize()

        if isinstance(state, str):
            if os.path.exists(state):
                with open(state, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                raise SessionError(f"State file '{state}' does not exist.")
        elif isinstance(state, SessionState):
            data = {"cookies": state.cookies, "origins": state.origins}
        else:
            data = state

        if "cookies" in data:
            await self.set_cookies(data["cookies"])

    async def get_network_logs(self) -> Dict[str, Any]:
        """Get recorded network observer summary."""
        return self.observer.get_summary()

    async def close(self) -> None:
        """Shut down Playwright page, context, browser, and process resources."""
        self._logger.info("Closing Playwright strategy resources...")
        if self._page and not self._page.is_closed():
            try:
                await self._page.close()
            except Exception:
                pass
            self._page = None

        if self._context:
            try:
                if self.config.save_state_on_close and self.config.storage_state_path:
                    await self._context.storage_state(path=self.config.storage_state_path)
                await self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
