"""Constants and Enums for the Browser Tool.

This module defines all enumeration types, constant values, default headers,
timeouts, and standard browser configuration defaults used across the
Browser Tool architecture.
"""

from enum import Enum
from typing import Dict, Final


class HttpMethod(str, Enum):
    """Supported HTTP request methods."""
    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class BrowserAction(str, Enum):
    """Enumeration of high-level browser actions."""
    OPEN_URL = "OPEN_URL"
    CLICK = "CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    HOVER = "HOVER"
    FILL_INPUT = "FILL_INPUT"
    CLEAR_INPUT = "CLEAR_INPUT"
    PRESS_KEY = "PRESS_KEY"
    SELECT_DROPDOWN = "SELECT_DROPDOWN"
    CHECK_CHECKBOX = "CHECK_CHECKBOX"
    UPLOAD_FILE = "UPLOAD_FILE"
    DOWNLOAD_FILE = "DOWNLOAD_FILE"
    WAIT_FOR_SELECTOR = "WAIT_FOR_SELECTOR"
    WAIT_FOR_NAVIGATION = "WAIT_FOR_NAVIGATION"
    SCROLL_PAGE = "SCROLL_PAGE"
    EXECUTE_JAVASCRIPT = "EXECUTE_JAVASCRIPT"
    CAPTURE_SCREENSHOT = "CAPTURE_SCREENSHOT"
    CAPTURE_NETWORK_REQUESTS = "CAPTURE_NETWORK_REQUESTS"
    CAPTURE_CONSOLE_LOGS = "CAPTURE_CONSOLE_LOGS"
    GET_CURRENT_URL = "GET_CURRENT_URL"
    GET_PAGE_TITLE = "GET_PAGE_TITLE"
    GET_PAGE_HTML = "GET_PAGE_HTML"
    GET_CLEAN_TEXT = "GET_CLEAN_TEXT"

    # Legacy action keys for backward compatibility
    NAVIGATE = "NAVIGATE"
    TYPE = "TYPE"
    FORM_FILL = "FORM_FILL"
    SUBMIT = "SUBMIT"
    SCROLL = "SCROLL"
    EXTRACT = "EXTRACT"
    SCREENSHOT = "SCREENSHOT"
    PDF = "PDF"
    EXECUTE_SCRIPT = "EXECUTE_SCRIPT"
    WAIT_FOR_ELEMENT = "WAIT_FOR_ELEMENT"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"
    LOGIN = "LOGIN"
    GO_BACK = "GO_BACK"
    GO_FORWARD = "GO_FORWARD"
    REFRESH = "REFRESH"


class PageStatus(str, Enum):
    """State of a webpage load/parse lifecycle."""
    UNINITIALIZED = "UNINITIALIZED"
    LOADING = "LOADING"
    LOADED = "LOADED"
    PARSED = "PARSED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class BrowserEngineType(str, Enum):
    """Supported underlying engine drivers."""
    HTTP_BASIC = "HTTP_BASIC"        # Lightweight HTTP client (Step 2)
    HEADLESS_CHROME = "HEADLESS_CHROME"  # Dynamic browser automation engine
    PLAYWRIGHT = "PLAYWRIGHT"        # Playwright rendering engine (Step 6)
    SELENIUM = "SELENIUM"          # Selenium driver engine (extensibility stub)
    MOCK = "MOCK"                    # Testing & dry-run engine


# Default Configuration Constants
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
DEFAULT_NAVIGATION_TIMEOUT_SECONDS: Final[float] = 45.0
DEFAULT_MAX_REDIRECTS: Final[int] = 5
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_BACKOFF_FACTOR: Final[float] = 0.5
DEFAULT_MAX_PAGE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB limit
DEFAULT_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 AI-Research-Assistant/1.0"
)

DEFAULT_HEADERS: Final[Dict[str, str]] = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

DEFAULT_VIEWPORT_WIDTH: Final[int] = 1280
DEFAULT_VIEWPORT_HEIGHT: Final[int] = 800

DEFAULT_SCREENSHOT_TIMEOUT_MS: Final[float] = 5000.0

