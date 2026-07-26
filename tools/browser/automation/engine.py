"""Central High-Level Browser Automation Engine Facade.

This module implements `BrowserAutomationEngine`, acting as the primary Facade for
AI research agents interacting with dynamic JavaScript-heavy websites. Exposes high-level
task-oriented operations, automatically managing lifecycle, context,
sessions, network monitoring, and memory cleanup.
"""

import asyncio
import threading
from typing import Dict, Any, List, Optional, Union
from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType, BrowserAction
from tools.browser.automation.base import AutomationStrategy
from tools.browser.automation.factory import AutomationStrategyFactory
from tools.browser.automation.commands import (
    CommandRunner,
    ClickCommand,
    DoubleClickCommand,
    HoverCommand,
    ClearInputCommand,
    PressKeyCommand,
    CheckCheckboxCommand,
    WaitForNavigationCommand,
    TypeCommand,
    FillInputCommand,
    ScrollCommand,
    WaitForElementCommand,
    ExecuteJSCommand,
    SelectOptionCommand,
    TakeScreenshotCommand,
    WaitForFunctionCommand,
    WaitForUrlCommand,
    WaitForNetworkIdleCommand,
    GetConsoleLogsCommand,
    SubmitFormCommand,
    DownloadCommand,
    UploadCommand,
)
from tools.browser.automation.models import ElementSpec, SessionState
from tools.browser.exceptions import ValidationError
from tools.browser.utils.logging import get_browser_logger


def validate_selector(selector: str) -> str:
    """Validate that selector is a non-empty string."""
    if not selector or not isinstance(selector, str) or not selector.strip():
        raise ValidationError("Selector cannot be empty or non-string.")
    return selector.strip()


class BrowserAutomationEngine:
    """Production Dynamic Browser Automation Engine Facade.

    Coordinates strategy drivers, command invocation, session state, network monitoring,
    and resource disposal following Clean Architecture and SOLID principles.

    Runs all browser actions on a dedicated background event loop thread to guarantee
    thread safety for asynchronous Playwright calls made from synchronous contexts.
    """

    def __init__(
        self,
        config: Optional[BrowserConfig] = None,
        strategy: Optional[AutomationStrategy] = None,
    ) -> None:
        """Initialize BrowserAutomationEngine.

        Args:
            config (Optional[BrowserConfig]): Config container.
            strategy (Optional[AutomationStrategy]): Injected strategy driver instance.
        """
        self.config = config or BrowserConfig(engine_type=BrowserEngineType.PLAYWRIGHT)
        self.config.validate()

        self._logger = get_browser_logger("BrowserAutomationEngine")

        # Start background event loop thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, args=(self._loop,), daemon=True)
        self._thread.start()

        # Instantiate strategy on the background event loop thread
        self.strategy = strategy or self._run_sync(self._create_strategy_async())
        self.runner = CommandRunner()
        self.last_action_result: Optional[Dict[str, Any]] = None

    def _run_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Loop thread target execution."""
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def _create_strategy_async(self) -> AutomationStrategy:
        """Instantiate target driver strategy."""
        return AutomationStrategyFactory.create_strategy(
            engine_type=self.config.engine_type,
            config=self.config,
        )

    def _run_sync(self, coro: Any) -> Any:
        """Run a coroutine synchronously on the background event loop thread."""
        if not self._loop.is_running():
            raise RuntimeError("Background event loop is not running.")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    async def _run_async(self, coro: Any) -> Any:
        """Run a coroutine asynchronously on the background event loop thread."""
        if not self._loop.is_running():
            raise RuntimeError("Background event loop is not running.")
        # Wrap concurrent.futures.Future as an asyncio.Future awaitable in the active loop
        return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coro, self._loop))

    def _process_pipeline_result(self, res: Dict[str, Any]) -> Any:
        """Store pipeline result and return core data value, raising errors if unsuccessful."""
        self.last_action_result = res
        if not res["success"]:
            err_msg = res["errors"][-1] if res["errors"] else "Action failed"
            # Map strings to correct exception class
            if "Selector cannot be empty" in err_msg:
                raise ValidationError(err_msg)
            elif "not exist" in err_msg or "upload" in err_msg.lower():
                from tools.browser.automation.exceptions import UploadError
                raise UploadError(err_msg, selector="")
            elif "download" in err_msg.lower():
                from tools.browser.automation.exceptions import DownloadError
                raise DownloadError(err_msg, selector="")
            elif "not found" in err_msg or "clickable" in err_msg or "reach state" in err_msg or "selector" in err_msg.lower():
                from tools.browser.automation.exceptions import ElementNotFoundError
                raise ElementNotFoundError(err_msg, selector="")
            elif "JavaScript execution failed" in err_msg or "wait_for_function" in err_msg:
                from tools.browser.automation.exceptions import ScriptExecutionError
                raise ScriptExecutionError(err_msg, script="")
            elif "timed out" in err_msg or "timeout" in err_msg:
                from tools.browser.exceptions import TimeoutError as BrowserTimeoutError
                raise BrowserTimeoutError(err_msg, url="")
            else:
                from tools.browser.automation.exceptions import InteractionError
                raise InteractionError(err_msg)
        return res["data"]

    # -------------------------------------------------------------------------
    # High-Level AI Operations (Async & Sync Compatible)
    # -------------------------------------------------------------------------

    async def open_page_async(
        self,
        url: str,
        wait_until: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Navigate to URL and wait for page rendering."""
        coro = self.strategy.navigate(url, wait_until=wait_until, timeout=timeout)
        return await self._run_async(coro)

    def open_page(
        self,
        url: str,
        wait_until: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for open_page_async."""
        return self._run_sync(self.strategy.navigate(url, wait_until=wait_until, timeout=timeout))

    async def click_async(
        self,
        selector: str,
        timeout: Optional[float] = None,
        force: bool = False,
    ) -> bool:
        """Click element matching target selector."""
        sel = validate_selector(selector)
        cmd = ClickCommand(selector=sel, timeout=timeout, force=force)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def click(self, selector: str, timeout: Optional[float] = None, force: bool = False) -> bool:
        """Synchronous wrapper for click_async."""
        sel = validate_selector(selector)
        cmd = ClickCommand(selector=sel, timeout=timeout, force=force)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def double_click_async(
        self,
        selector: str,
        timeout: Optional[float] = None,
        force: bool = False,
    ) -> bool:
        """Double click element matching selector."""
        sel = validate_selector(selector)
        cmd = DoubleClickCommand(selector=sel, timeout=timeout, force=force)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def double_click(self, selector: str, timeout: Optional[float] = None, force: bool = False) -> bool:
        """Synchronous double click."""
        sel = validate_selector(selector)
        cmd = DoubleClickCommand(selector=sel, timeout=timeout, force=force)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def hover_async(
        self,
        selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Hover over element matching selector."""
        sel = validate_selector(selector)
        cmd = HoverCommand(selector=sel, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def hover(self, selector: str, timeout: Optional[float] = None) -> bool:
        """Synchronous hover."""
        sel = validate_selector(selector)
        cmd = HoverCommand(selector=sel, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def clear_input_async(
        self,
        selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Clear text input field matching selector."""
        sel = validate_selector(selector)
        cmd = ClearInputCommand(selector=sel, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def clear_input(self, selector: str, timeout: Optional[float] = None) -> bool:
        """Synchronous clear input."""
        sel = validate_selector(selector)
        cmd = ClearInputCommand(selector=sel, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def press_key_async(
        self,
        selector: str,
        key: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Press key on element matching selector."""
        sel = validate_selector(selector)
        cmd = PressKeyCommand(selector=sel, key=key, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def press_key(self, selector: str, key: str, timeout: Optional[float] = None) -> bool:
        """Synchronous press key."""
        sel = validate_selector(selector)
        cmd = PressKeyCommand(selector=sel, key=key, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def check_checkbox_async(
        self,
        selector: str,
        checked: bool = True,
        timeout: Optional[float] = None,
    ) -> bool:
        """Set checkbox or radio checked state."""
        sel = validate_selector(selector)
        cmd = CheckCheckboxCommand(selector=sel, checked=checked, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def check_checkbox(self, selector: str, checked: bool = True, timeout: Optional[float] = None) -> bool:
        """Synchronous check checkbox."""
        sel = validate_selector(selector)
        cmd = CheckCheckboxCommand(selector=sel, checked=checked, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def wait_for_navigation_async(
        self,
        wait_until: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Wait for navigation to complete."""
        cmd = WaitForNavigationCommand(wait_until=wait_until, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def wait_for_navigation(
        self,
        wait_until: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Synchronous wait for navigation."""
        cmd = WaitForNavigationCommand(wait_until=wait_until, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def fill_form_async(
        self,
        field_values: Dict[str, str],
        submit_selector: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Fill input fields and optionally click submit button."""
        coro = self.strategy.fill_form(field_values, submit_selector=submit_selector, timeout=timeout)
        return await self._run_async(coro)

    def fill_form(
        self,
        field_values: Dict[str, str],
        submit_selector: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Synchronous wrapper for fill_form_async."""
        return self._run_sync(self.strategy.fill_form(field_values, submit_selector=submit_selector, timeout=timeout))

    async def type_text_async(
        self,
        selector: str,
        text: str,
        clear_first: bool = True,
        timeout: Optional[float] = None,
    ) -> bool:
        """Type text character-by-character into input field."""
        sel = validate_selector(selector)
        cmd = TypeCommand(selector=sel, text=text, clear_first=clear_first, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def type_text(
        self,
        selector: str,
        text: str,
        clear_first: bool = True,
        timeout: Optional[float] = None,
    ) -> bool:
        """Synchronous wrapper for type_text_async."""
        sel = validate_selector(selector)
        cmd = TypeCommand(selector=sel, text=text, clear_first=clear_first, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def fill_input_async(
        self,
        selector: str,
        text: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Directly fill text into input field using Playwright's fast fill API."""
        sel = validate_selector(selector)
        cmd = FillInputCommand(selector=sel, text=text, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def fill_input(self, selector: str, text: str, timeout: Optional[float] = None) -> bool:
        """Synchronous wrapper for fill_input_async."""
        sel = validate_selector(selector)
        cmd = FillInputCommand(selector=sel, text=text, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def select_option_async(
        self,
        selector: str,
        value: Union[str, List[str]],
        timeout: Optional[float] = None,
    ) -> bool:
        """Select value in dropdown select element."""
        sel = validate_selector(selector)
        cmd = SelectOptionCommand(selector=sel, value=value, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def select_option(
        self,
        selector: str,
        value: Union[str, List[str]],
        timeout: Optional[float] = None,
    ) -> bool:
        """Synchronous wrapper for select_option_async."""
        sel = validate_selector(selector)
        cmd = SelectOptionCommand(selector=sel, value=value, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def submit_async(self, selector: str, timeout: Optional[float] = None) -> bool:
        """Click submit button or form submit trigger."""
        return await self.submit_form_async(selector, timeout=timeout)

    def submit(self, selector: str, timeout: Optional[float] = None) -> bool:
        """Synchronous wrapper for submit_async."""
        return self.submit_form(selector, timeout=timeout)

    async def submit_form_async(self, selector: str, timeout: Optional[float] = None) -> bool:
        """Submit a form element or submit button."""
        sel = validate_selector(selector)
        cmd = SubmitFormCommand(selector=sel, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def submit_form(self, selector: str, timeout: Optional[float] = None) -> bool:
        """Synchronous wrapper for submit_form_async."""
        sel = validate_selector(selector)
        cmd = SubmitFormCommand(selector=sel, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def scroll_to_async(
        self,
        direction: str = "down",
        selector: Optional[str] = None,
        amount: int = 500,
    ) -> bool:
        """Scroll window or target scroll container."""
        sel = validate_selector(selector) if selector else None
        cmd = ScrollCommand(direction=direction, amount=amount, selector=sel)
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def scroll_to(
        self,
        direction: str = "down",
        selector: Optional[str] = None,
        amount: int = 500,
    ) -> bool:
        """Synchronous wrapper for scroll_to_async."""
        sel = validate_selector(selector) if selector else None
        cmd = ScrollCommand(direction=direction, amount=amount, selector=sel)
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def wait_for_element_async(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[float] = None,
    ) -> ElementSpec:
        """Wait for element selector state."""
        sel = validate_selector(selector)
        cmd = WaitForElementCommand(selector=sel, state=state, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[float] = None,
    ) -> ElementSpec:
        """Synchronous wrapper for wait_for_element_async."""
        sel = validate_selector(selector)
        cmd = WaitForElementCommand(selector=sel, state=state, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy, max_retries=self.config.max_retries))
        return self._process_pipeline_result(res)

    async def wait_for_function_async(
        self,
        script: str,
        arg: Any = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Wait until custom JS function evaluates to truthy value."""
        cmd = WaitForFunctionCommand(script=script, arg=arg, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def wait_for_function(
        self,
        script: str,
        arg: Any = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Synchronous wrapper for wait_for_function_async."""
        cmd = WaitForFunctionCommand(script=script, arg=arg, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def wait_for_url_async(
        self,
        url_pattern: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait until page URL matches target pattern."""
        cmd = WaitForUrlCommand(url_pattern=url_pattern, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def wait_for_url(
        self,
        url_pattern: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Synchronous wrapper for wait_for_url_async."""
        cmd = WaitForUrlCommand(url_pattern=url_pattern, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def wait_for_network_idle_async(
        self,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait until network requests settle to idle state."""
        cmd = WaitForNetworkIdleCommand(timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def wait_for_network_idle(
        self,
        timeout: Optional[float] = None,
    ) -> bool:
        """Synchronous wrapper for wait_for_network_idle_async."""
        cmd = WaitForNetworkIdleCommand(timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def execute_script_async(self, script: str, arg: Any = None) -> Any:
        """Execute custom JavaScript in current document context."""
        cmd = ExecuteJSCommand(script=script, arg=arg)
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def execute_script(self, script: str, arg: Any = None) -> Any:
        """Synchronous wrapper for execute_script_async."""
        cmd = ExecuteJSCommand(script=script, arg=arg)
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def take_screenshot_async(
        self,
        path: Optional[str] = None,
        full_page: bool = False,
        selector: Optional[str] = None,
    ) -> bytes:
        """Capture page or element screenshot."""
        sel = validate_selector(selector) if selector else None
        cmd = TakeScreenshotCommand(path=path, full_page=full_page, selector=sel)
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def take_screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False,
        selector: Optional[str] = None,
    ) -> bytes:
        """Synchronous wrapper for take_screenshot_async."""
        sel = validate_selector(selector) if selector else None
        cmd = TakeScreenshotCommand(path=path, full_page=full_page, selector=sel)
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def download_file_async(
        self,
        trigger_selector: str,
        download_dir: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Click element and download file."""
        sel = validate_selector(trigger_selector)
        cmd = DownloadCommand(selector=sel, download_dir=download_dir, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def download_file(
        self,
        trigger_selector: str,
        download_dir: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for download_file_async."""
        sel = validate_selector(trigger_selector)
        cmd = DownloadCommand(selector=sel, download_dir=download_dir, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def upload_file_async(
        self,
        selector: str,
        files: Union[str, List[str]],
        timeout: Optional[float] = None,
    ) -> bool:
        """Upload file(s) into file input element."""
        sel = validate_selector(selector)
        cmd = UploadCommand(selector=sel, files=files, timeout=timeout)
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def upload_file(
        self,
        selector: str,
        files: Union[str, List[str]],
        timeout: Optional[float] = None,
    ) -> bool:
        """Synchronous wrapper for upload_file_async."""
        sel = validate_selector(selector)
        cmd = UploadCommand(selector=sel, files=files, timeout=timeout)
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def capture_console_logs_async(self) -> List[Dict[str, Any]]:
        """Get console logs from browser observer."""
        cmd = GetConsoleLogsCommand()
        res = await self._run_async(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    def capture_console_logs(self) -> List[Dict[str, Any]]:
        """Synchronous wrapper for capture_console_logs_async."""
        cmd = GetConsoleLogsCommand()
        res = self._run_sync(self.runner.run(cmd, self.strategy))
        return self._process_pipeline_result(res)

    async def capture_network_async(self) -> Dict[str, Any]:
        """Get network observer event log."""
        return await self._run_async(self.strategy.get_network_logs())

    def capture_network(self) -> Dict[str, Any]:
        """Synchronous wrapper for capture_network_async."""
        return self._run_sync(self.strategy.get_network_logs())

    async def login_async(
        self,
        url: str,
        credentials: Dict[str, str],
        submit_selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """High-level automated user login flow."""
        await self.open_page_async(url, timeout=timeout)
        await self.fill_form_async(credentials, submit_selector=submit_selector, timeout=timeout)
        return True

    def login(
        self,
        url: str,
        credentials: Dict[str, str],
        submit_selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Synchronous wrapper for login_async."""
        self.open_page(url, timeout=timeout)
        self.fill_form(credentials, submit_selector=submit_selector, timeout=timeout)
        return True

    async def interact_async(
        self,
        action_type: Union[BrowserAction, str],
        selector: str,
        value: Optional[Any] = None,
    ) -> Any:
        """Generic task-oriented interaction dispatcher."""
        act_str = action_type.value if isinstance(action_type, BrowserAction) else str(action_type).upper()

        if act_str in ("CLICK", "SUBMIT"):
            return await self.click_async(selector)
        elif act_str == "TYPE":
            return await self.type_text_async(selector, str(value or ""))
        elif act_str == "FILL":
            return await self.fill_input_async(selector, str(value or ""))
        elif act_str == "SCROLL":
            return await self.scroll_to_async(direction=str(value or "down"), selector=selector)
        elif act_str == "WAIT_FOR_ELEMENT":
            return await self.wait_for_element_async(selector, state=str(value or "visible"))
        elif act_str == "EXECUTE_SCRIPT":
            return await self.execute_script_async(selector, arg=value)
        else:
            raise ValueError(f"Unsupported interaction action type: '{act_str}'")

    def interact(
        self,
        action_type: Union[BrowserAction, str],
        selector: str,
        value: Optional[Any] = None,
    ) -> Any:
        """Synchronous wrapper for interact_async."""
        act_str = action_type.value if isinstance(action_type, BrowserAction) else str(action_type).upper()

        if act_str in ("CLICK", "SUBMIT"):
            return self.click(selector)
        elif act_str == "TYPE":
            return self.type_text(selector, str(value or ""))
        elif act_str == "FILL":
            return self.fill_input(selector, str(value or ""))
        elif act_str == "SCROLL":
            return self.scroll_to(direction=str(value or "down"), selector=selector)
        elif act_str == "WAIT_FOR_ELEMENT":
            return self.wait_for_element(selector, state=str(value or "visible"))
        elif act_str == "EXECUTE_SCRIPT":
            return self.execute_script(selector, arg=value)
        else:
            raise ValueError(f"Unsupported interaction action type: '{act_str}'")

    # -------------------------------------------------------------------------
    # Page Source & Session State
    # -------------------------------------------------------------------------

    async def get_page_source_async(self) -> str:
        """Get HTML DOM content."""
        return await self._run_async(self.strategy.get_page_source())

    def get_page_source(self) -> str:
        """Synchronous wrapper for get_page_source_async."""
        return self._run_sync(self.strategy.get_page_source())

    async def export_session_async(self, path: Optional[str] = None) -> SessionState:
        """Export state to JSON file or DTO."""
        return await self._run_async(self.strategy.export_storage_state(path=path))

    def export_session(self, path: Optional[str] = None) -> SessionState:
        """Synchronous wrapper for export_session_async."""
        return self._run_sync(self.strategy.export_storage_state(path=path))

    async def import_session_async(self, state: Union[str, Dict[str, Any], SessionState]) -> None:
        """Import authentication state."""
        await self._run_async(self.strategy.import_storage_state(state))

    def import_session(self, state: Union[str, Dict[str, Any], SessionState]) -> None:
        """Synchronous wrapper for import_session_async."""
        self._run_sync(self.strategy.import_storage_state(state))

    # -------------------------------------------------------------------------
    # Lifecycle & Cleanup
    # -------------------------------------------------------------------------

    async def aclose(self) -> None:
        """Close browser resources asynchronously."""
        if self._loop and self._loop.is_running():
            try:
                await self._run_async(self.strategy.close())
            except Exception:
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)

    def close(self) -> None:
        """Close browser resources synchronously."""
        if self._loop and self._loop.is_running():
            try:
                self._run_sync(self.strategy.close())
            except Exception:
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=2.0)

    async def __aenter__(self) -> "BrowserAutomationEngine":
        await self._run_async(self.strategy.initialize())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    def __enter__(self) -> "BrowserAutomationEngine":
        self._run_sync(self.strategy.initialize())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
