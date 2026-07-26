"""Strategy Factory for Browser Automation Drivers.

This module provides `AutomationStrategyFactory`, allowing concrete driver strategies
(PlaywrightStrategy, SeleniumStrategy, MockAutomationStrategy) to be instantiated
or registered dynamically, following the Strategy and Open-Closed principles.
"""

from typing import Dict, Type, Union, Optional, Any
from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.automation.base import AutomationStrategy
from tools.browser.exceptions import UnsupportedEngineError


class MockAutomationStrategy(AutomationStrategy):
    """Stub mock strategy for dry-run testing and mock unit tests."""

    def __init__(self, config: BrowserConfig) -> None:
        super().__init__(config)
        self.initialized = False
        self.current_url = "about:blank"
        self.page_source = "<html><body>Mock Content</body></html>"
        self.cookies: list = []

    async def initialize(self) -> None:
        self.initialized = True

    async def navigate(self, url: str, wait_until: Optional[str] = None, timeout: Optional[float] = None) -> dict:
        self.initialized = True
        self.current_url = url
        return {"url": url, "status_code": 200, "title": "Mock Title", "success": True}

    async def click(self, selector: str, timeout: Optional[float] = None, force: bool = False) -> bool:
        return True

    async def double_click(self, selector: str, timeout: Optional[float] = None, force: bool = False) -> bool:
        return True

    async def hover(self, selector: str, timeout: Optional[float] = None) -> bool:
        return True

    async def clear_input(self, selector: str, timeout: Optional[float] = None) -> bool:
        return True

    async def press_key(self, selector: str, key: str, timeout: Optional[float] = None) -> bool:
        return True

    async def check_checkbox(self, selector: str, checked: bool = True, timeout: Optional[float] = None) -> bool:
        return True

    async def wait_for_navigation(self, wait_until: Optional[str] = None, timeout: Optional[float] = None) -> dict:
        return {"url": self.current_url, "status_code": 200, "title": "Mock Title", "success": True}

    async def type_text(self, selector: str, text: str, clear_first: bool = True, timeout: Optional[float] = None) -> bool:
        return True

    async def fill_input(self, selector: str, text: str, timeout: Optional[float] = None) -> bool:
        return True

    async def fill_form(self, field_values: dict, submit_selector: Optional[str] = None, timeout: Optional[float] = None) -> bool:
        return True

    async def select_option(self, selector: str, value: str, timeout: Optional[float] = None) -> bool:
        return True

    async def scroll(self, direction: str = "down", amount: int = 500, selector: Optional[str] = None) -> bool:
        return True

    async def wait_for_element(self, selector: str, state: str = "visible", timeout: Optional[float] = None):
        from tools.browser.automation.models import ElementSpec
        return ElementSpec(selector=selector, tag_name="div", is_visible=True)

    async def execute_js(self, script: str, arg: Any = None) -> Any:
        return "mock_js_result"

    async def take_screenshot(self, path: Optional[str] = None, full_page: bool = False, selector: Optional[str] = None) -> bytes:
        return b"mock_png_bytes"

    async def capture_pdf(self, path: Optional[str] = None) -> bytes:
        return b"mock_pdf_bytes"

    async def download_file(self, trigger_selector: str, download_dir: Optional[str] = None, timeout: Optional[float] = None) -> dict:
        return {"suggested_filename": "mock.txt", "path": "/tmp/mock_download.txt", "url": "http://mock/download"}

    async def upload_file(self, selector: str, files: Union[str, list], timeout: Optional[float] = None) -> bool:
        return True

    async def wait_for_function(self, script: str, arg: Any = None, timeout: Optional[float] = None) -> Any:
        return True

    async def wait_for_url(self, url_pattern: str, timeout: Optional[float] = None) -> bool:
        return True

    async def wait_for_network_idle(self, timeout: Optional[float] = None) -> bool:
        return True

    async def get_console_logs(self) -> list:
        return []

    async def submit_form(self, selector: str, timeout: Optional[float] = None) -> bool:
        return True

    async def get_page_source(self) -> str:
        return self.page_source

    async def get_url(self) -> str:
        return self.current_url

    async def get_title(self) -> str:
        return "Mock Title"

    async def get_cookies(self) -> list:
        return self.cookies

    async def set_cookies(self, cookies: list) -> None:
        self.cookies = cookies

    async def export_storage_state(self, path: Optional[str] = None):
        from tools.browser.automation.models import SessionState
        return SessionState(cookies=self.cookies, origins=[])

    async def import_storage_state(self, state) -> None:
        pass

    async def get_network_logs(self) -> dict:
        return {"requests": [], "responses": []}

    async def close(self) -> None:
        self.initialized = False


class AutomationStrategyFactory:
    """Strategy Factory container for registering and creating browser automation strategies."""

    _registry: Dict[str, Type[AutomationStrategy]] = {}

    @classmethod
    def register_strategy(
        cls,
        engine_type: Union[BrowserEngineType, str],
        strategy_cls: Type[AutomationStrategy],
    ) -> None:
        """Register a concrete strategy class.

        Args:
            engine_type (Union[BrowserEngineType, str]): Unique key or BrowserEngineType enum value.
            strategy_cls (Type[AutomationStrategy]): Subclass implementing AutomationStrategy.
        """
        key = engine_type.value if isinstance(engine_type, BrowserEngineType) else str(engine_type).upper()
        cls._registry[key] = strategy_cls

    @classmethod
    def create_strategy(
        cls,
        engine_type: Optional[Union[BrowserEngineType, str]] = None,
        config: Optional[BrowserConfig] = None,
    ) -> AutomationStrategy:
        """Instantiate and return a concrete strategy driver.

        Args:
            engine_type (Optional[Union[BrowserEngineType, str]]): Target engine identifier.
            config (Optional[BrowserConfig]): Browser configuration settings.

        Returns:
            AutomationStrategy: Concrete strategy driver instance.

        Raises:
            UnsupportedEngineError: If engine type is unrecognized.
        """
        config = config or BrowserConfig()
        target = engine_type or config.engine_type
        key = target.value if isinstance(target, BrowserEngineType) else str(target).upper()

        if key not in cls._registry:
            if key in (BrowserEngineType.PLAYWRIGHT.value, BrowserEngineType.HEADLESS_CHROME.value):
                from tools.browser.automation.playwright_strategy import PlaywrightStrategy
                cls._registry[key] = PlaywrightStrategy
            elif key == BrowserEngineType.MOCK.value:
                cls._registry[key] = MockAutomationStrategy
            elif key == BrowserEngineType.SELENIUM.value:
                raise UnsupportedEngineError(
                    "Selenium driver engine is registered in the architecture but not implemented. "
                    "Use PLAYWRIGHT or HTTP_BASIC."
                )
            else:
                raise UnsupportedEngineError(f"Unsupported browser automation engine key: '{key}'")

        strategy_cls = cls._registry[key]
        return strategy_cls(config)
