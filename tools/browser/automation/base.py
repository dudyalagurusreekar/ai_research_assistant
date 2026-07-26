"""Abstract Base Strategy Interface for Browser Automation Engines.

Following the Strategy Pattern and SOLID principles (Single Responsibility,
Open-Closed, Interface Segregation), this abstract base class defines the target
contract for all dynamic browser automation engines (PlaywrightStrategy,
SeleniumStrategy, MockAutomationStrategy).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from tools.browser.config import BrowserConfig
from tools.browser.automation.models import ElementSpec, SessionState, NetworkRequestLog, NetworkResponseLog


class AutomationStrategy(ABC):
    """Abstract interface defining standard capabilities for dynamic browser drivers."""

    def __init__(self, config: BrowserConfig) -> None:
        """Initialize automation strategy with configuration.

        Args:
            config (BrowserConfig): Central browser configuration container.
        """
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Launch underlying browser process, create context and default page."""
        pass

    @abstractmethod
    async def navigate(
        self,
        url: str,
        wait_until: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Navigate to a target URL in the active page.

        Args:
            url (str): Target webpage URL.
            wait_until (Optional[str]): Wait condition ('domcontentloaded', 'load', 'networkidle').
            timeout (Optional[float]): Timeout in seconds.

        Returns:
            Dict[str, Any]: Basic navigation metadata (url, status_code, title).
        """
        pass

    @abstractmethod
    async def click(
        self,
        selector: str,
        timeout: Optional[float] = None,
        force: bool = False,
    ) -> bool:
        """Click on a DOM element matching the target selector.

        Args:
            selector (str): CSS selector or XPath expression.
            timeout (Optional[float]): Action timeout in seconds.
            force (bool): Bypass actionability checks.

        Returns:
            bool: True if click succeeded.
        """
        pass

    @abstractmethod
    async def double_click(
        self,
        selector: str,
        timeout: Optional[float] = None,
        force: bool = False,
    ) -> bool:
        """Double click on a DOM element matching the target selector.

        Args:
            selector (str): CSS selector or XPath expression.
            timeout (Optional[float]): Action timeout in seconds.
            force (bool): Bypass actionability checks.

        Returns:
            bool: True if double click succeeded.
        """
        pass

    @abstractmethod
    async def hover(
        self,
        selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Hover mouse cursor over a DOM element matching the target selector.

        Args:
            selector (str): CSS selector or XPath expression.
            timeout (Optional[float]): Action timeout in seconds.

        Returns:
            bool: True if hover succeeded.
        """
        pass

    @abstractmethod
    async def clear_input(
        self,
        selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Clear text input field matching the target selector.

        Args:
            selector (str): Target input element selector.
            timeout (Optional[float]): Action timeout.

        Returns:
            bool: True if clear succeeded.
        """
        pass

    @abstractmethod
    async def press_key(
        self,
        selector: str,
        key: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Simulate pressing a specific key or key combination on a DOM element.

        Args:
            selector (str): Target element selector.
            key (str): Key value (e.g. 'Enter', 'Escape', 'ArrowDown').
            timeout (Optional[float]): Action timeout.

        Returns:
            bool: True if key press succeeded.
        """
        pass

    @abstractmethod
    async def check_checkbox(
        self,
        selector: str,
        checked: bool = True,
        timeout: Optional[float] = None,
    ) -> bool:
        """Check or uncheck checkbox/radio matching the target selector.

        Args:
            selector (str): Checkbox/radio element selector.
            checked (bool): Target checked state.
            timeout (Optional[float]): Action timeout.

        Returns:
            bool: True if checkbox check state was set successfully.
        """
        pass

    @abstractmethod
    async def wait_for_navigation(
        self,
        wait_until: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Wait for active page navigation or URL transition to complete.

        Args:
            wait_until (Optional[str]): Wait condition ('domcontentloaded', 'load', 'networkidle').
            timeout (Optional[float]): Timeout in seconds.

        Returns:
            Dict[str, Any]: Navigation details.
        """
        pass

    @abstractmethod
    async def type_text(
        self,
        selector: str,
        text: str,
        clear_first: bool = True,
        timeout: Optional[float] = None,
    ) -> bool:
        """Type text into an input or textarea element.

        Args:
            selector (str): Target element selector.
            text (str): String content to enter.
            clear_first (bool): Clear input prior to typing.
            timeout (Optional[float]): Timeout in seconds.

        Returns:
            bool: True if typing succeeded.
        """
        pass

    @abstractmethod
    async def fill_input(
        self,
        selector: str,
        text: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Directly fill text into input field without simulating keyboard typing.

        Args:
            selector (str): Target element selector.
            text (str): String content to fill.
            timeout (Optional[float]): Timeout in seconds.

        Returns:
            bool: True if fill succeeded.
        """
        pass

    @abstractmethod
    async def fill_form(
        self,
        field_values: Dict[str, str],
        submit_selector: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Fill out multiple form fields by selector and optionally submit.

        Args:
            field_values (Dict[str, str]): Mapping of field selector -> input value.
            submit_selector (Optional[str]): Optional submit button selector.
            timeout (Optional[float]): Action timeout.

        Returns:
            bool: True if form was filled and submitted.
        """
        pass

    @abstractmethod
    async def select_option(
        self,
        selector: str,
        value: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Select option in a HTML `<select>` element by value or label.

        Args:
            selector (str): Target `<select>` element selector.
            value (str): Option value or text label.
            timeout (Optional[float]): Action timeout.

        Returns:
            bool: True if option was selected.
        """
        pass

    @abstractmethod
    async def scroll(
        self,
        direction: str = "down",
        amount: int = 500,
        selector: Optional[str] = None,
    ) -> bool:
        """Scroll the window or specific container element.

        Args:
            direction (str): 'down', 'up', 'top', 'bottom'.
            amount (int): Scroll distance in pixels.
            selector (Optional[str]): Optional scroll container element selector.

        Returns:
            bool: True if scroll completed.
        """
        pass

    @abstractmethod
    async def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[float] = None,
    ) -> ElementSpec:
        """Wait for a DOM element to reach a specific state.

        Args:
            selector (str): Element selector.
            state (str): 'attached', 'detached', 'visible', 'hidden'.
            timeout (Optional[float]): Timeout in seconds.

        Returns:
            ElementSpec: Details of the located element.
        """
        pass

    @abstractmethod
    async def execute_js(self, script: str, arg: Any = None) -> Any:
        """Execute custom JavaScript in the context of the current document.

        Args:
            script (str): JavaScript expression or function body.
            arg (Any): Optional JSON-serializable argument to pass into script.

        Returns:
            Any: Result evaluated from JS execution.
        """
        pass

    @abstractmethod
    async def take_screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False,
        selector: Optional[str] = None,
    ) -> bytes:
        """Capture screenshot of current page view, full scrollable document, or specific element.

        Args:
            path (Optional[str]): File path to write image artifact to.
            full_page (bool): Capture full scrollable document height.
            selector (Optional[str]): Target DOM element selector for element screenshot.

        Returns:
            bytes: PNG binary image payload.
        """
        pass

    @abstractmethod
    async def wait_for_function(
        self,
        script: str,
        arg: Any = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Wait until custom JavaScript function/expression evaluates to truthy value.

        Args:
            script (str): JS expression or function snippet.
            arg (Any): Optional argument for evaluation.
            timeout (Optional[float]): Timeout in seconds.

        Returns:
            Any: Evaluated JS return value.
        """
        pass

    @abstractmethod
    async def wait_for_url(
        self,
        url_pattern: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait until page URL matches target pattern or string.

        Args:
            url_pattern (str): String pattern or regex.
            timeout (Optional[float]): Timeout in seconds.

        Returns:
            bool: True when URL matches.
        """
        pass

    @abstractmethod
    async def wait_for_network_idle(
        self,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait until network requests settle to idle state.

        Args:
            timeout (Optional[float]): Timeout in seconds.

        Returns:
            bool: True when network is idle.
        """
        pass

    @abstractmethod
    async def get_console_logs(self) -> List[Dict[str, Any]]:
        """Retrieve recorded browser console messages log."""
        pass

    @abstractmethod
    async def submit_form(
        self,
        selector: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Submit a form element or click form submit button.

        Args:
            selector (str): Form or submit button selector.
            timeout (Optional[float]): Timeout in seconds.

        Returns:
            bool: True if form was submitted.
        """
        pass

    @abstractmethod
    async def capture_pdf(self, path: Optional[str] = None) -> bytes:
        """Generate PDF document print representation of page.

        Args:
            path (Optional[str]): Target file path to write PDF to.

        Returns:
            bytes: PDF binary document payload.
        """
        pass

    @abstractmethod
    async def download_file(
        self,
        trigger_selector: str,
        download_dir: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Click an element that triggers a file download and wait for save.

        Args:
            trigger_selector (str): Selector of button/link initiating download.
            download_dir (Optional[str]): Override destination directory.
            timeout (Optional[float]): Download completion timeout.

        Returns:
            str: Saved local file path.
        """
        pass

    @abstractmethod
    async def upload_file(
        self,
        selector: str,
        files: Union[str, List[str]],
        timeout: Optional[float] = None,
    ) -> bool:
        """Upload file(s) to a file input element (`<input type="file">`).

        Args:
            selector (str): File input selector.
            files (Union[str, List[str]]): Path or list of local file paths.
            timeout (Optional[float]): Action timeout.

        Returns:
            bool: True if upload succeeded.
        """
        pass

    @abstractmethod
    async def get_page_source(self) -> str:
        """Retrieve current fully-rendered HTML DOM content as string."""
        pass

    @abstractmethod
    async def get_url(self) -> str:
        """Retrieve active page URL."""
        pass

    @abstractmethod
    async def get_title(self) -> str:
        """Retrieve active page document title."""
        pass

    @abstractmethod
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """Export browser cookies from current context."""
        pass

    @abstractmethod
    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Inject browser cookies into active context."""
        pass

    @abstractmethod
    async def export_storage_state(self, path: Optional[str] = None) -> SessionState:
        """Export full authentication state (cookies & storage) to file or DTO.

        Args:
            path (Optional[str]): Optional JSON output file path.

        Returns:
            SessionState: Serialized state container.
        """
        pass

    @abstractmethod
    async def import_storage_state(self, state: Union[str, Dict[str, Any], SessionState]) -> None:
        """Import authentication state into active context.

        Args:
            state (Union[str, Dict[str, Any], SessionState]): File path, dict, or DTO.
        """
        pass

    @abstractmethod
    async def get_network_logs(self) -> Dict[str, Any]:
        """Retrieve intercepted network requests and responses log."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close page, browser context, and underlying browser driver instance."""
        pass
