"""Browser Driver Abstraction Interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IBrowserDriver(ABC):
    """Abstract Interface defining browser automation driver capabilities."""

    @abstractmethod
    async def open_url(self, url: str) -> bool:
        """Navigate to a target URL."""
        pass

    @abstractmethod
    async def click(self, selector: str) -> bool:
        """Click an interactive element by selector."""
        pass

    @abstractmethod
    async def type_text(self, selector: str, text: str) -> bool:
        """Type text into an input element."""
        pass

    @abstractmethod
    async def scroll(self, direction: str = "down", amount: int = 500) -> bool:
        """Scroll page up or down by pixel amount."""
        pass

    @abstractmethod
    async def wait_for_selector(self, selector: str, timeout_seconds: float = 10.0) -> bool:
        """Wait for an element matching selector to become visible."""
        pass

    @abstractmethod
    async def get_html(self) -> str:
        """Return raw page HTML content."""
        pass

    @abstractmethod
    async def get_current_url(self) -> str:
        """Return active page URL."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close browser resources."""
        pass
