"""Configuration Management for the Browser Tool.

This module provides the central `BrowserConfig` dataclass, supporting
default values, validation, environment variable loading, and dictionary export.
"""

from dataclasses import dataclass, field
import os
from typing import Dict, Any, Optional

from tools.browser.constants import (
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_NAVIGATION_TIMEOUT_SECONDS,
    DEFAULT_MAX_REDIRECTS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_MAX_PAGE_SIZE_BYTES,
    DEFAULT_USER_AGENT,
    DEFAULT_HEADERS,
    DEFAULT_VIEWPORT_WIDTH,
    DEFAULT_VIEWPORT_HEIGHT,
    BrowserEngineType,
)
from tools.browser.exceptions import ConfigurationError


@dataclass
class BrowserConfig:
    """Configuration container for controlling browser behavior.

    Attributes:
        engine_type (BrowserEngineType): Underlying execution driver engine.
        timeout_seconds (float): General network request timeout in seconds.
        navigation_timeout_seconds (float): Page load navigation timeout.
        max_redirects (int): Maximum HTTP redirects allowed.
        max_retries (int): Maximum retry attempts for transient network/server failures.
        backoff_factor (float): Exponential backoff delay factor in seconds.
        max_page_size_bytes (int): Maximum response payload size limit.
        user_agent (str): User-Agent string header.
        default_headers (Dict[str, str]): Default HTTP request headers.
        viewport_width (int): Browser viewport width in pixels.
        viewport_height (int): Browser viewport height in pixels.
        follow_redirects (bool): Whether to follow HTTP redirects automatically.
        verify_ssl (bool): Whether to enforce SSL certificate validation.
        headless (bool): Run browser in headless mode (for full browser drivers).
        enable_cache (bool): Enable page content caching.
    """

    engine_type: BrowserEngineType = BrowserEngineType.HTTP_BASIC
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    navigation_timeout_seconds: float = DEFAULT_NAVIGATION_TIMEOUT_SECONDS
    max_redirects: int = DEFAULT_MAX_REDIRECTS
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    max_page_size_bytes: int = DEFAULT_MAX_PAGE_SIZE_BYTES
    user_agent: str = DEFAULT_USER_AGENT
    default_headers: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_HEADERS))
    viewport_width: int = DEFAULT_VIEWPORT_WIDTH
    viewport_height: int = DEFAULT_VIEWPORT_HEIGHT
    follow_redirects: bool = True
    verify_ssl: bool = True
    headless: bool = True
    enable_cache: bool = False

    # Automation Subsystem Settings (Step 6)
    playwright_browser_type: str = "chromium"
    playwright_launch_args: list = field(default_factory=list)
    storage_state_path: Optional[str] = None
    screenshot_dir: str = "data/screenshots"
    download_dir: str = "data/downloads"
    trace_dir: Optional[str] = None
    wait_until: str = "networkidle"
    ignore_https_errors: bool = True
    save_state_on_close: bool = False

    def validate(self) -> bool:
        """Validate configuration settings.

        Returns:
            bool: True if configuration is valid.

        Raises:
            ConfigurationError: If any config parameter is out of valid bounds.
        """
        if self.timeout_seconds <= 0:
            raise ConfigurationError(
                f"timeout_seconds must be positive, got {self.timeout_seconds}"
            )
        if self.navigation_timeout_seconds <= 0:
            raise ConfigurationError(
                f"navigation_timeout_seconds must be positive, got {self.navigation_timeout_seconds}"
            )
        if self.max_redirects < 0:
            raise ConfigurationError(
                f"max_redirects cannot be negative, got {self.max_redirects}"
            )
        if self.max_retries < 0:
            raise ConfigurationError(
                f"max_retries cannot be negative, got {self.max_retries}"
            )
        if self.backoff_factor < 0:
            raise ConfigurationError(
                f"backoff_factor cannot be negative, got {self.backoff_factor}"
            )
        if self.max_page_size_bytes <= 0:
            raise ConfigurationError(
                f"max_page_size_bytes must be positive, got {self.max_page_size_bytes}"
            )
        if self.viewport_width <= 0 or self.viewport_height <= 0:
            raise ConfigurationError(
                f"Viewport dimensions must be positive, got ({self.viewport_width}x{self.viewport_height})"
            )
        return True

    @classmethod
    def from_env(cls) -> "BrowserConfig":
        """Instantiate BrowserConfig loading overrides from environment variables.

        Supported Environment Variables:
            BROWSER_ENGINE_TYPE: Driver engine type.
            BROWSER_TIMEOUT_SECONDS: Timeout in seconds.
            BROWSER_MAX_RETRIES: Maximum retries count.
            BROWSER_BACKOFF_FACTOR: Exponential backoff factor.
            BROWSER_USER_AGENT: Custom user agent header.
            BROWSER_VERIFY_SSL: 'true' / 'false' flag.
            BROWSER_ENABLE_CACHE: 'true' / 'false' flag.

        Returns:
            BrowserConfig: Config populated with environment overrides.
        """
        engine_str = os.getenv("BROWSER_ENGINE_TYPE", BrowserEngineType.HTTP_BASIC.value)
        try:
            engine_type = BrowserEngineType(engine_str)
        except ValueError:
            engine_type = BrowserEngineType.HTTP_BASIC

        timeout = float(os.getenv("BROWSER_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
        max_retries = int(os.getenv("BROWSER_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
        backoff_factor = float(os.getenv("BROWSER_BACKOFF_FACTOR", str(DEFAULT_BACKOFF_FACTOR)))
        user_agent = os.getenv("BROWSER_USER_AGENT", DEFAULT_USER_AGENT)
        verify_ssl = os.getenv("BROWSER_VERIFY_SSL", "true").lower() in ("true", "1", "yes")
        enable_cache = os.getenv("BROWSER_ENABLE_CACHE", "false").lower() in ("true", "1", "yes")

        config = cls(
            engine_type=engine_type,
            timeout_seconds=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            user_agent=user_agent,
            verify_ssl=verify_ssl,
            enable_cache=enable_cache,
        )
        config.validate()
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to a dictionary representation."""
        return {
            "engine_type": self.engine_type.value,
            "timeout_seconds": self.timeout_seconds,
            "navigation_timeout_seconds": self.navigation_timeout_seconds,
            "max_redirects": self.max_redirects,
            "max_retries": self.max_retries,
            "backoff_factor": self.backoff_factor,
            "max_page_size_bytes": self.max_page_size_bytes,
            "user_agent": self.user_agent,
            "default_headers": self.default_headers,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "follow_redirects": self.follow_redirects,
            "verify_ssl": self.verify_ssl,
            "headless": self.headless,
            "enable_cache": self.enable_cache,
            "playwright_browser_type": self.playwright_browser_type,
            "storage_state_path": self.storage_state_path,
            "screenshot_dir": self.screenshot_dir,
            "download_dir": self.download_dir,
            "wait_until": self.wait_until,
            "save_state_on_close": self.save_state_on_close,
        }
