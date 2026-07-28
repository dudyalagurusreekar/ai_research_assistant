"""Robots.txt Compliance Handler for the Web Crawling Subsystem.

This module provides the `RobotsTxtHandler` class, responsible for fetching, parsing,
caching, and evaluating `robots.txt` rules per domain using `urllib.robotparser`.
"""

from typing import Dict, Optional, Any
from urllib.robotparser import RobotFileParser

from tools.browser.utils.helpers import extract_domain
from tools.browser.utils.logging import get_browser_logger


class RobotsTxtHandler:
    """Handler managing per-domain `robots.txt` compliance and caching."""

    def __init__(self) -> None:
        self._logger = get_browser_logger("RobotsTxtHandler")
        self._cache: Dict[str, Optional[RobotFileParser]] = {}

    def can_fetch(self, user_agent: str, url: str, fetcher: Optional[Any] = None) -> bool:
        """Check whether user_agent is allowed to fetch the target URL.

        Args:
            user_agent (str): User-Agent string header.
            url (str): Target URL to evaluate.
            fetcher (Optional[Any]): Network fetcher to download robots.txt if uncached.

        Returns:
            bool: True if allowed to fetch under robots.txt rules.
        """
        domain = extract_domain(url)
        if not domain:
            return True

        if domain in self._cache:
            parser = self._cache[domain]
            return parser.can_fetch(user_agent, url) if parser else True

        # Fetch robots.txt if fetcher is available
        robots_url = f"https://{domain}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)

        if fetcher:
            try:
                from tools.browser.models.request import NavigationParams
                res = fetcher.fetch(NavigationParams(url=robots_url, timeout=5.0))
                if res.success and res.text:
                    parser.parse(res.text.splitlines())
                    self._cache[domain] = parser
                    return parser.can_fetch(user_agent, url)
            except Exception as e:
                self._logger.debug(f"Could not fetch robots.txt for '{domain}': {e}")

        # Default fallback: allow access if robots.txt is 404 or missing
        self._cache[domain] = None
        return True
