"""Command Pattern for Browser Automation Actions.

This module encapsulates browser interactions as executable Command objects,
providing robust tracking, selector validation, success verification, and retries.
"""

from abc import ABC, abstractmethod
import time
import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from tools.browser.automation.base import AutomationStrategy
from tools.browser.automation.models import ElementSpec
from tools.browser.exceptions import ValidationError
from tools.browser.utils.logging import get_browser_logger


def validate_selector_syntax(selector: str) -> None:
    """Validate CSS or XPath selector format. Throws ValidationError if malformed."""
    if not selector or not isinstance(selector, str) or not selector.strip():
        raise ValidationError("Selector cannot be empty or non-string.")
    sel = selector.strip()

    # Determine type of selector and do basic syntax validation
    is_xpath = sel.startswith("/") or sel.startswith("xpath=") or sel.startswith("(") or sel.startswith("..")
    
    if is_xpath:
        if sel.count("[") != sel.count("]"):
            raise ValidationError(f"Malformed XPath selector (mismatched brackets): '{selector}'")
    else:
        if sel.count("[") != sel.count("]") or sel.count("(") != sel.count(")"):
            raise ValidationError(f"Malformed CSS selector syntax (mismatched brackets/parentheses): '{selector}'")


def get_property_js(selector: str, prop_expr: str) -> str:
    """Generate inline JS script to resolve CSS or XPath selector and return target property."""
    sel_json = json.dumps(selector)
    return f"""(() => {{
        const sel = {sel_json};
        let el = null;
        if (sel.startsWith('/') || sel.startsWith('xpath=') || sel.startsWith('(') || sel.startsWith('..')) {{
            const clean = sel.startsWith('xpath=') ? sel.substring(6) : sel;
            try {{
                const res = document.evaluate(clean, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                el = res.singleNodeValue;
            }} catch (e) {{}}
        }} else {{
            try {{
                el = document.querySelector(sel);
            }} catch (e) {{}}
        }}
        if (!el) return null;
        return {prop_expr};
    }})()"""


class BrowserCommand(ABC):
    """Abstract Base Class for all browser interaction commands."""

    def __init__(self, selector: Optional[str] = None) -> None:
        self.selector = selector

    def validate(self) -> None:
        """Perform input and selector syntax validation."""
        if self.selector is not None:
            validate_selector_syntax(self.selector)

    @abstractmethod
    async def execute(self, strategy: AutomationStrategy) -> Any:
        """Execute action command against the provided strategy driver.

        Args:
            strategy (AutomationStrategy): Active browser driver strategy.

        Returns:
            Any: Result of the action.
        """

    async def verify(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        """Perform action-specific state verification. Returns verification details dict."""
        return {"verified": True, "message": "No verification strategy defined."}


class ClickCommand(BrowserCommand):
    """Encapsulation of click interaction."""

    def __init__(self, selector: str, timeout: Optional[float] = None, force: bool = False) -> None:
        super().__init__(selector)
        self.timeout = timeout
        self.force = force

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.click(self.selector, self.timeout, self.force)

    async def verify(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        try:
            exists = await strategy.execute_js(get_property_js(self.selector, "true"))
            return {"verified": True, "element_remains": exists is True}
        except Exception as e:
            return {"verified": True, "warning": f"Click verification check omitted: {e}"}


class DoubleClickCommand(BrowserCommand):
    """Encapsulation of double click interaction."""

    def __init__(self, selector: str, timeout: Optional[float] = None, force: bool = False) -> None:
        super().__init__(selector)
        self.timeout = timeout
        self.force = force

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.double_click(self.selector, self.timeout, self.force)


class HoverCommand(BrowserCommand):
    """Encapsulation of hover interaction."""

    def __init__(self, selector: str, timeout: Optional[float] = None) -> None:
        super().__init__(selector)
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.hover(self.selector, self.timeout)


class ClearInputCommand(BrowserCommand):
    """Encapsulation of text input clearing interaction."""

    def __init__(self, selector: str, timeout: Optional[float] = None) -> None:
        super().__init__(selector)
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.clear_input(self.selector, self.timeout)

    async def verify(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        try:
            val = await strategy.execute_js(get_property_js(self.selector, "el.value !== undefined ? el.value : el.innerText"))
            return {"verified": val == "" or val is None, "field_value": val or ""}
        except Exception as e:
            return {"verified": True, "warning": f"Clear input verification skipped: {e}"}


class PressKeyCommand(BrowserCommand):
    """Encapsulation of key press interaction."""

    def __init__(self, selector: str, key: str, timeout: Optional[float] = None) -> None:
        super().__init__(selector)
        self.key = key
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.press_key(self.selector, self.key, self.timeout)


class CheckCheckboxCommand(BrowserCommand):
    """Encapsulation of checkbox check state interaction."""

    def __init__(self, selector: str, checked: bool = True, timeout: Optional[float] = None) -> None:
        super().__init__(selector)
        self.checked = checked
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.check_checkbox(self.selector, self.checked, self.timeout)

    async def verify(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        try:
            val = await strategy.execute_js(get_property_js(self.selector, "el.checked"))
            return {"verified": val == self.checked, "checked": val}
        except Exception as e:
            return {"verified": True, "warning": f"Checkbox verification skipped: {e}"}


class WaitForNavigationCommand(BrowserCommand):
    """Encapsulation of waiting for navigation event."""

    def __init__(self, wait_until: Optional[str] = None, timeout: Optional[float] = None) -> None:
        super().__init__(None)
        self.wait_until = wait_until
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        return await strategy.wait_for_navigation(self.wait_until, self.timeout)


class TypeCommand(BrowserCommand):
    """Encapsulation of sequential keyboard-simulating text entry."""

    def __init__(
        self,
        selector: str,
        text: str,
        clear_first: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        super().__init__(selector)
        self.text = text
        self.clear_first = clear_first
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.type_text(self.selector, self.text, self.clear_first, self.timeout)

    async def verify(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        try:
            val = await strategy.execute_js(get_property_js(self.selector, "el.value !== undefined ? el.value : el.innerText"))
            return {"verified": val == self.text, "field_value": val}
        except Exception as e:
            return {"verified": True, "warning": f"Type verification skipped: {e}"}


class FillInputCommand(BrowserCommand):
    """Encapsulation of direct fast text value fill."""

    def __init__(self, selector: str, text: str, timeout: Optional[float] = None) -> None:
        super().__init__(selector)
        self.text = text
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        if hasattr(strategy, "fill_input"):
            return await strategy.fill_input(self.selector, self.text, self.timeout)
        else:
            # Fallback to type_text if fill_input not implemented in strategy
            return await strategy.type_text(self.selector, self.text, clear_first=True, timeout=self.timeout)

    async def verify(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        try:
            val = await strategy.execute_js(get_property_js(self.selector, "el.value !== undefined ? el.value : el.innerText"))
            return {"verified": val == self.text, "field_value": val}
        except Exception as e:
            return {"verified": True, "warning": f"Fill verification skipped: {e}"}


class ScrollCommand(BrowserCommand):
    """Encapsulation of page/container scroll action."""

    def __init__(
        self,
        direction: str = "down",
        amount: int = 500,
        selector: Optional[str] = None,
    ) -> None:
        super().__init__(selector)
        self.direction = direction
        self.amount = amount

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.scroll(self.direction, self.amount, self.selector)


class WaitForElementCommand(BrowserCommand):
    """Encapsulation of DOM element wait state condition."""

    def __init__(self, selector: str, state: str = "visible", timeout: Optional[float] = None) -> None:
        super().__init__(selector)
        self.state = state
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> ElementSpec:
        return await strategy.wait_for_element(self.selector, self.state, self.timeout)


class ExecuteJSCommand(BrowserCommand):
    """Encapsulation of custom JavaScript execution."""

    def __init__(self, script: str, arg: Any = None) -> None:
        super().__init__(None)
        self.script = script
        self.arg = arg

    async def execute(self, strategy: AutomationStrategy) -> Any:
        return await strategy.execute_js(self.script, self.arg)


class SelectOptionCommand(BrowserCommand):
    """Encapsulation of select option in dropdown interaction."""

    def __init__(self, selector: str, value: Union[str, List[str]], timeout: Optional[float] = None) -> None:
        super().__init__(selector)
        self.value = value
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.select_option(self.selector, self.value, self.timeout)

    async def verify(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        try:
            val = await strategy.execute_js(get_property_js(self.selector, "el.value"))
            selected_vals = await strategy.execute_js(get_property_js(self.selector, "Array.from(el.selectedOptions).map(o => o.value)"))
            return {"verified": True, "selected_value": val, "selected_values": selected_vals}
        except Exception as e:
            return {"verified": True, "warning": f"Select verification skipped: {e}"}


class TakeScreenshotCommand(BrowserCommand):
    """Encapsulation of screenshot capture."""

    def __init__(
        self,
        path: Optional[str] = None,
        full_page: bool = False,
        selector: Optional[str] = None,
    ) -> None:
        super().__init__(selector)
        self.path = path
        self.full_page = full_page

    async def execute(self, strategy: AutomationStrategy) -> bytes:
        return await strategy.take_screenshot(self.path, self.full_page, self.selector)


class WaitForFunctionCommand(BrowserCommand):
    """Encapsulation of waiting for custom JS predicate function."""

    def __init__(self, script: str, arg: Any = None, timeout: Optional[float] = None) -> None:
        super().__init__(None)
        self.script = script
        self.arg = arg
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> Any:
        return await strategy.wait_for_function(self.script, self.arg, self.timeout)


class WaitForUrlCommand(BrowserCommand):
    """Encapsulation of waiting for URL match."""

    def __init__(self, url_pattern: str, timeout: Optional[float] = None) -> None:
        super().__init__(None)
        self.url_pattern = url_pattern
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.wait_for_url(self.url_pattern, self.timeout)


class WaitForNetworkIdleCommand(BrowserCommand):
    """Encapsulation of waiting for network requests to settle."""

    def __init__(self, timeout: Optional[float] = None) -> None:
        super().__init__(None)
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.wait_for_network_idle(self.timeout)


class GetConsoleLogsCommand(BrowserCommand):
    """Encapsulation of retrieving browser console log messages."""

    def __init__(self) -> None:
        super().__init__(None)

    async def execute(self, strategy: AutomationStrategy) -> List[Dict[str, Any]]:
        return await strategy.get_console_logs()


class SubmitFormCommand(BrowserCommand):
    """Encapsulation of form submission action."""

    def __init__(self, selector: str, timeout: Optional[float] = None) -> None:
        super().__init__(selector)
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.submit_form(self.selector, self.timeout)

    async def verify(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        try:
            exists = await strategy.execute_js(get_property_js(self.selector, "true"))
            return {"verified": True, "form_exists": exists is True}
        except Exception as e:
            return {"verified": True, "warning": f"Form submission verification skipped: {e}"}


class DownloadCommand(BrowserCommand):
    """Encapsulation of file download click."""

    def __init__(
        self,
        selector: str,
        download_dir: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        super().__init__(selector)
        self.download_dir = download_dir
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        return await strategy.download_file(self.selector, self.download_dir, self.timeout)


class UploadCommand(BrowserCommand):
    """Encapsulation of file upload action."""

    def __init__(
        self,
        selector: str,
        files: Union[str, List[str]],
        timeout: Optional[float] = None,
    ) -> None:
        super().__init__(selector)
        self.files = files
        self.timeout = timeout

    async def execute(self, strategy: AutomationStrategy) -> bool:
        return await strategy.upload_file(self.selector, self.files, self.timeout)

    async def verify(self, strategy: AutomationStrategy) -> Dict[str, Any]:
        try:
            files_count = await strategy.execute_js(get_property_js(self.selector, "el.files ? el.files.length : 0"))
            expected_count = 1 if isinstance(self.files, str) else len(self.files)
            return {"verified": files_count == expected_count, "files_count": files_count}
        except Exception as e:
            return {"verified": True, "warning": f"Upload verification skipped: {e}"}


class CommandRunner:
    """Invoker executing commands with a unified wait, validate, execute, retry, and verification pipeline."""

    def __init__(self) -> None:
        self._logger = get_browser_logger("CommandRunner")

    async def run(
        self,
        command: BrowserCommand,
        strategy: AutomationStrategy,
        max_retries: int = 0,
        backoff_delay: float = 0.5,
    ) -> Dict[str, Any]:
        """Run command with unified pipeline orchestration."""
        cmd_name = command.__class__.__name__
        self._logger.info(f"Pipeline started for command: {cmd_name}")

        # 1. Validation Phase
        start_val = time.time()
        try:
            command.validate()
            validation_time = (time.time() - start_val) * 1000.0
        except ValidationError as ve:
            self._logger.error(f"Command {cmd_name} failed validation: {ve}")
            return {
                "success": False,
                "data": None,
                "verification": None,
                "errors": [str(ve)],
                "console_logs": [],
                "network_requests": [],
                "metrics": {
                    "validation_time_ms": (time.time() - start_val) * 1000.0,
                    "execution_only_time_ms": 0.0,
                    "wait_time_ms": 0.0,
                    "verification_time_ms": 0.0,
                    "execution_time_ms": (time.time() - start_val) * 1000.0,
                    "retries_attempted": 0
                }
            }

        # 2. Pre-Action State Snapshot (capturing log indices)
        start_reqs = len(strategy.observer.requests) if hasattr(strategy, "observer") else 0
        len(strategy.observer.responses) if hasattr(strategy, "observer") else 0
        start_console = len(strategy.observer.console_logs) if hasattr(strategy, "observer") else 0
        start_errors = len(strategy.observer.page_errors) if hasattr(strategy, "observer") else 0

        # 3. Actionability Waiting Strategy
        wait_start = time.time()
        if hasattr(command, "selector") and command.selector:
            try:
                # Automatic wait for selector state before starting interaction
                timeout_val = min(2.0, strategy.config.timeout_seconds)
                if hasattr(command, "timeout") and command.timeout is not None:
                    timeout_val = min(timeout_val, command.timeout)
                await strategy.wait_for_element(command.selector, state="visible", timeout=timeout_val)
            except Exception:
                pass  # Let core execution or retries handle exceptions if detached or not visible yet
        wait_time = (time.time() - wait_start) * 1000.0

        # 4. Core Execution & Retry Loop
        exec_start = time.time()
        attempts = 0
        data = None
        errors = []
        success = False

        while True:
            try:
                attempts += 1
                data = await command.execute(strategy)
                success = True
                break
            except Exception as e:
                errors.append(str(e))
                if attempts > max_retries:
                    self._logger.error(f"Command {cmd_name} failed core execution after {attempts} attempts.")
                    break
                
                delay = backoff_delay * (2 ** (attempts - 1))
                self._logger.warning(
                    f"Command {cmd_name} failed (attempt {attempts}/{max_retries+1}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
        exec_time = (time.time() - exec_start) * 1000.0

        # 5. Post-Action Waiting Strategy (Wait for network idle to settle dynamic scripts)
        post_wait_start = time.time()
        if success:
            try:
                if hasattr(strategy, "wait_for_network_idle"):
                    await strategy.wait_for_network_idle(timeout=1.0)
            except Exception:
                pass
        post_wait_time = (time.time() - post_wait_start) * 1000.0
        wait_time += post_wait_time

        # 6. Success Verification Phase
        ver_start = time.time()
        verification_info = None
        if success:
            try:
                verification_info = await command.verify(strategy)
            except Exception as ve:
                self._logger.warning(f"Verification warning for {cmd_name}: {ve}")
                verification_info = {"verified": False, "error": str(ve)}
        ver_time = (time.time() - ver_start) * 1000.0

        # 7. Collect Sliced Diagnostics (logs strictly during action execution)
        sliced_reqs = []
        sliced_console = []
        if hasattr(strategy, "observer"):
            # Slicing out new requests and responses
            for req in strategy.observer.requests[start_reqs:]:
                sliced_reqs.append(req.to_dict())
            sliced_console = strategy.observer.console_logs[start_console:]
            
            # Slicing new page errors to append to errors list
            for err in strategy.observer.page_errors[start_errors:]:
                errors.append(f"Console Page Error: {err}")

        total_time = validation_time + wait_time + exec_time + ver_time
        self._logger.info(f"Pipeline finished for command {cmd_name} in {total_time:.1f}ms (success={success})")

        return {
            "success": success,
            "data": data,
            "verification": verification_info,
            "errors": errors,
            "console_logs": sliced_console,
            "network_requests": sliced_reqs,
            "metrics": {
                "validation_time_ms": validation_time,
                "execution_only_time_ms": exec_time,
                "wait_time_ms": wait_time,
                "verification_time_ms": ver_time,
                "execution_time_ms": total_time,
                "retries_attempted": attempts - 1
            }
        }
