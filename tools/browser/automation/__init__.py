"""Browser Automation Subsystem Package.

Provides dynamic browser automation, Playwright strategy integration,
command pattern action execution, event monitoring, session management,
and custom exception definitions.
"""

from tools.browser.automation.base import AutomationStrategy
from tools.browser.automation.models import (
    NetworkRequestLog,
    NetworkResponseLog,
    DialogLog,
    ElementSpec,
    SessionState,
)
from tools.browser.automation.exceptions import (
    AutomationError,
    ElementNotFoundError,
    InteractionError,
    ScriptExecutionError,
    SessionError,
    DialogError,
    DownloadError,
    UploadError,
)
from tools.browser.automation.observer import NetworkObserver
from tools.browser.automation.commands import (
    BrowserCommand,
    ClickCommand,
    TypeCommand,
    ScrollCommand,
    WaitForElementCommand,
    ExecuteJSCommand,
    TakeScreenshotCommand,
    DownloadCommand,
    UploadCommand,
    CommandRunner,
)
from tools.browser.automation.playwright_strategy import PlaywrightStrategy
from tools.browser.automation.factory import AutomationStrategyFactory, MockAutomationStrategy
from tools.browser.automation.engine import BrowserAutomationEngine

__all__ = [
    "AutomationStrategy",
    "NetworkRequestLog",
    "NetworkResponseLog",
    "DialogLog",
    "ElementSpec",
    "SessionState",
    "AutomationError",
    "ElementNotFoundError",
    "InteractionError",
    "ScriptExecutionError",
    "SessionError",
    "DialogError",
    "DownloadError",
    "UploadError",
    "NetworkObserver",
    "BrowserCommand",
    "ClickCommand",
    "TypeCommand",
    "ScrollCommand",
    "WaitForElementCommand",
    "ExecuteJSCommand",
    "TakeScreenshotCommand",
    "DownloadCommand",
    "UploadCommand",
    "CommandRunner",
    "PlaywrightStrategy",
    "AutomationStrategyFactory",
    "MockAutomationStrategy",
    "BrowserAutomationEngine",
]
