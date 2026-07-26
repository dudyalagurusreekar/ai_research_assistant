"""Network Fetchers Package for the Browser Tool Subsystem.

This package provides concrete implementations of `BaseFetcher` along with
a `FetcherFactory` strategy pattern factory for dynamically instantiating fetchers.
"""

from tools.browser.core.base_fetcher import BaseFetcher
from tools.browser.fetchers.http_fetcher import HTTPFetcher
from tools.browser.fetchers.playwright_fetcher import PlaywrightFetcher
from tools.browser.fetchers.factory import FetcherFactory

__all__ = [
    "BaseFetcher",
    "HTTPFetcher",
    "PlaywrightFetcher",
    "FetcherFactory",
]
