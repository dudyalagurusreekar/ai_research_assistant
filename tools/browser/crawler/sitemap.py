"""Sitemap XML Parser for the Web Crawling Subsystem.

This module provides the `SitemapParser` class, responsible for discovering seed URLs
from standard `sitemap.xml` files.
"""

from typing import List, Optional, Any
from bs4 import BeautifulSoup

from tools.browser.utils.helpers import sanitize_url
from tools.browser.utils.logging import get_browser_logger


class SitemapParser:
    """Parser responsible for discovering seed URLs from sitemap.xml documents."""

    def __init__(self) -> None:
        self._logger = get_browser_logger("SitemapParser")

    def parse_sitemap(self, sitemap_url: str, fetcher: Optional[Any] = None) -> List[str]:
        """Fetch and extract location URLs from a sitemap XML payload.

        Args:
            sitemap_url (str): Target sitemap.xml URL.
            fetcher (Optional[Any]): Network fetcher strategy.

        Returns:
            List[str]: List of discovered absolute webpage URLs.
        """
        urls: List[str] = []
        if not fetcher:
            return urls

        try:
            from tools.browser.models.request import NavigationParams
            res = fetcher.fetch(NavigationParams(url=sitemap_url, timeout=10.0))
            if not res.success or not res.text:
                return urls

            soup = BeautifulSoup(res.text, "xml")
            for loc in soup.find_all("loc"):
                if loc.string:
                    cleaned_url = sanitize_url(loc.string)
                    if cleaned_url and cleaned_url not in urls:
                        urls.append(cleaned_url)

            self._logger.info(f"Discovered {len(urls)} URLs from sitemap '{sitemap_url}'")
        except Exception as e:
            self._logger.warning(f"Failed to parse sitemap '{sitemap_url}': {e}")

        return urls
