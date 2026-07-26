"""Abstract Base Class for Network Fetchers in the Browser Tool.

Following SOLID principles (Single Responsibility & Open-Closed), this interface
defines the contract that all concrete network fetchers (Step 2 HTTPFetcher,
future HeadlessFetcher, MockFetcher) must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional

from tools.browser.config import BrowserConfig
from tools.browser.models.request import NavigationParams
from tools.browser.models.response import FetchResult


class BaseFetcher(ABC):
    """Abstract interface for fetching network resources over HTTP/HTTPS.

    Concrete subclasses in Step 2 will implement the actual network communication.

    Attributes:
        config (BrowserConfig): Reference to browser configuration settings.
    """

    def __init__(self, config: BrowserConfig) -> None:
        """Initialize base fetcher with configuration settings.

        Args:
            config (BrowserConfig): Configuration container.
        """
        self.config = config

    @abstractmethod
    def fetch(self, params: NavigationParams) -> FetchResult:
        """Fetch a web resource synchronously given navigation parameters.

        Args:
            params (NavigationParams): Navigation details including URL, headers, method.

        Returns:
            FetchResult: Raw network response result.

        Raises:
            FetchError: If network request encounters fatal error.
            TimeoutError: If request exceeds specified timeout limit.
        """
        pass

    @abstractmethod
    async def fetch_async(self, params: NavigationParams) -> FetchResult:
        """Fetch a web resource asynchronously given navigation parameters.

        Args:
            params (NavigationParams): Navigation details including URL, headers, method.

        Returns:
            FetchResult: Raw network response result.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Release underlying network sockets, sessions, or browser driver resources."""
        pass
