"""Custom Exception Hierarchy for Browser Automation Subsystem.

This module defines specialized exceptions inheriting from BrowserError for
handling failures during dynamic browser operations, element manipulation,
script execution, and session management.
"""

from typing import Optional, Dict, Any
from tools.browser.exceptions import BrowserError


class AutomationError(BrowserError):
    """Base exception class for all dynamic browser automation errors."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = context or {}
        if url:
            ctx["url"] = url
        if selector:
            ctx["selector"] = selector
        super().__init__(message, context=ctx)
        self.url = url
        self.selector = selector


class ElementNotFoundError(AutomationError):
    """Raised when a specified target DOM element or selector cannot be located."""
    pass


class InteractionError(AutomationError):
    """Raised when an interactive action (click, fill, scroll, select) fails."""
    pass


class ScriptExecutionError(AutomationError):
    """Raised when custom JavaScript execution on page fails or returns an error."""

    def __init__(
        self,
        message: str,
        script: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = context or {}
        if script:
            ctx["script_snippet"] = script[:100]
        super().__init__(message, context=ctx)
        self.script = script


class SessionError(AutomationError):
    """Raised when exporting, importing, or persisting browser authentication session state fails."""
    pass


class DialogError(AutomationError):
    """Raised when handling JavaScript dialog alerts/confirms/prompts encounters an error."""
    pass


class DownloadError(AutomationError):
    """Raised when file download operation fails or times out."""
    pass


class UploadError(AutomationError):
    """Raised when file upload input target or file path resolution fails."""
    pass
