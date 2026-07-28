"""Fetcher Factory for the Browser Tool Subsystem.

This module provides the `FetcherFactory` class, which implements the Strategy Pattern
by instantiating concrete `BaseFetcher` implementations based on configuration settings.
"""

from typing import Dict, Type, Union, Optional

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.core.base_fetcher import BaseFetcher
from tools.browser.exceptions import UnsupportedEngineError


class FetcherFactory:
    """Factory for creating network fetcher strategy instances.

    Supports registry pattern allowing custom fetcher implementations to be
    registered dynamically for extension (e.g. Playwright, Selenium, Caching).
    """

    _registry: Dict[str, Type[BaseFetcher]] = {}

    @classmethod
    def register_fetcher(
        cls,
        engine_type: Union[BrowserEngineType, str],
        fetcher_cls: Type[BaseFetcher],
    ) -> None:
        """Register a concrete fetcher implementation class.

        Args:
            engine_type (Union[BrowserEngineType, str]): Target engine type identifier.
            fetcher_cls (Type[BaseFetcher]): Subclass of BaseFetcher to register.
        """
        key = engine_type.value if isinstance(engine_type, BrowserEngineType) else str(engine_type).upper()
        cls._registry[key] = fetcher_cls

    @classmethod
    def create_fetcher(
        cls,
        engine_type: Optional[Union[BrowserEngineType, str]] = None,
        config: Optional[BrowserConfig] = None,
    ) -> BaseFetcher:
        """Instantiate and return a concrete BaseFetcher implementation.

        Args:
            engine_type (Optional[Union[BrowserEngineType, str]]): Strategy engine identifier.
            config (Optional[BrowserConfig]): Browser configuration container.

        Returns:
            BaseFetcher: Instantiated concrete network fetcher strategy.

        Raises:
            UnsupportedEngineError: If requested engine type is unknown or unregistered.
        """
        config = config or BrowserConfig()
        config.validate()

        target_engine = engine_type or config.engine_type
        key = target_engine.value if isinstance(target_engine, BrowserEngineType) else str(target_engine).upper()

        if key not in cls._registry:
            if key == BrowserEngineType.HTTP_BASIC.value:
                from tools.browser.fetchers.http_fetcher import HTTPFetcher
                cls._registry[key] = HTTPFetcher
            elif key in (BrowserEngineType.PLAYWRIGHT.value, BrowserEngineType.HEADLESS_CHROME.value):
                from tools.browser.fetchers.playwright_fetcher import PlaywrightFetcher
                cls._registry[key] = PlaywrightFetcher
            elif key == BrowserEngineType.MOCK.value:
                # Dynamically define a MockFetcher for testing
                from tools.browser.models.response import FetchResult
                class MockFetcher(BaseFetcher):
                    def fetch(self, params):
                        return FetchResult(url=params.url, status_code=200, content=b"<html><body>Mock Page</body></html>", success=True)
                    async def fetch_async(self, params):
                        return FetchResult(url=params.url, status_code=200, content=b"<html><body>Mock Page</body></html>", success=True)
                    def close(self):
                        pass
                cls._registry[key] = MockFetcher
            else:
                raise UnsupportedEngineError(
                    f"Unsupported or unregistered fetcher engine type: '{key}'. "
                    f"Available engines: {list(cls._registry.keys())}"
                )

        fetcher_cls = cls._registry[key]
        return fetcher_cls(config)
