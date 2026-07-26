"""Custom Exception Hierarchy for the Browser Tool.

This module defines a clean, strongly-typed exception hierarchy for catching,
handling, and reporting errors within the Browser Tool subsystem.
"""

from typing import Optional, Dict, Any


class BrowserError(Exception):
    """Base exception class for all errors originating from the Browser Tool.

    Attributes:
        message (str): Human-readable error description.
        context (Dict[str, Any]): Optional contextual key-value pairs (e.g. url, status_code).
    """

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
    pass


class ValidationError(BrowserError):
    """Raised when request parameters, URLs, or inputs fail validation checks."""
    pass


class NavigationError(BrowserError):
    """Base class for errors occurring during browser navigation actions."""
    pass


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
    pass


class HTTPError(FetchError):
    """Raised when an HTTP request returns an error status code (4xx or 5xx)."""
    pass


class NetworkError(FetchError):
    """Raised when underlying socket or network connectivity fails (DNS resolution, connection refused)."""
    pass


class ParsingError(BrowserError):
    """Base class for DOM parsing or content extraction failures."""
    pass


class DOMParseError(ParsingError):
    """Raised when HTML or document structure cannot be parsed properly."""
    pass


class ContentExtractionError(ParsingError):
    """Raised when target elements or structured content extraction fails."""
    pass


class UnsupportedEngineError(ConfigurationError):
    """Raised when requesting a browser driver/engine that is not supported or installed."""
    pass


# Re-export automation exception classes for unified access
try:
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
except ImportError:
    pass

