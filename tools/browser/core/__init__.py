"""Core orchestration and abstract component contracts for the Browser Tool.

This package defines abstract interfaces for Network Fetchers (`BaseFetcher`),
Content Parsers (`BaseParser`), and the main `Browser` orchestrator engine skeleton.
"""

from tools.browser.core.base_fetcher import BaseFetcher
from tools.browser.core.base_parser import BaseParser
from tools.browser.core.browser import Browser

__all__ = [
    "BaseFetcher",
    "BaseParser",
    "Browser",
]
