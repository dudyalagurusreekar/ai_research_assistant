"""Custom Exception Hierarchy for the Browser Tool.

This module defines a clean, strongly-typed exception hierarchy for catching,
handling, and reporting errors within the Browser Tool subsystem.
"""

from typing import Optional, Dict, Any


class BrowserError(Exception):
    """Base exception class for all errors originating from the Browser Tool."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} [{context_str}]"
        return self.message


class ConfigurationError(BrowserError):
    """Raised when browser configuration is invalid or missing required values."""


class ValidationError(BrowserError):
    """Raised when request parameters, URLs, or inputs fail validation checks."""


class NavigationError(BrowserError):
    """Base class for errors occurring during browser navigation actions."""


class FetchError(NavigationError):
    """Raised when fetching a network resource fails."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = context or {}
        if url:
            ctx["url"] = url
        if status_code is not None:
            ctx["status_code"] = status_code
        super().__init__(message, context=ctx)
        self.url = url
        self.status_code = status_code


class TimeoutError(FetchError):
    """Raised when a network operation or browser navigation exceeds timeout thresholds."""


class HTTPError(FetchError):
    """Raised when an HTTP request returns an error status code (4xx or 5xx)."""


class NetworkError(FetchError):
    """Raised when underlying socket or network connectivity fails."""


class ParsingError(BrowserError):
    """Base class for DOM parsing or content extraction failures."""


class DOMParseError(ParsingError):
    """Raised when HTML or document structure cannot be parsed properly."""


class ContentExtractionError(ParsingError):
    """Raised when target elements or structured content extraction fails."""


class UnsupportedEngineError(ConfigurationError):
    """Raised when requesting a browser driver/engine that is not supported."""


class AutomationError(BrowserError):
    """Base exception class for dynamic browser automation errors."""


class ElementNotFoundError(AutomationError):
    """Raised when a target DOM element cannot be located."""


class InteractionError(AutomationError):
    """Raised when an interactive action fails."""


class ScriptExecutionError(AutomationError):
    """Raised when custom JavaScript execution fails."""


class SessionError(AutomationError):
    """Raised when browser session state operation fails."""


class DialogError(AutomationError):
    """Raised when handling JavaScript dialog alerts/prompts encounters an error."""


class DownloadError(AutomationError):
    """Raised when file download operation fails or times out."""


class UploadError(AutomationError):
    """Raised when file upload operation fails."""
