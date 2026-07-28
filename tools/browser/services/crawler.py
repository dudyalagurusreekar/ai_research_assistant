"""Recursive Web Crawling Engine for the Browser Tool Subsystem.

This module provides the `CrawlerEngine` class, enabling multi-page web research crawling
with configurable depth limits, domain restrictions, rate limiting, and visited URL deduplication.
"""

from collections import deque
import time
from typing import List, Set, Optional, TYPE_CHECKING

from tools.browser.models.response import BrowserResponse
from tools.browser.utils.helpers import extract_domain, sanitize_url
from tools.browser.utils.logging import get_browser_logger

if TYPE_CHECKING:
    from tools.browser.core.browser import Browser


class CrawlerEngine:
    """Recursive multi-page web crawling engine.

    Follows Single Responsibility Principle to orchestrate multi-page navigation
    queues without containing low-level parsing or networking code.
    """

    def __init__(self, browser: "Browser") -> None:
        """Initialize CrawlerEngine with Browser orchestrator reference.

        Args:
            browser (Browser): Parent Browser orchestrator instance.
        """
        self.browser = browser
        self._logger = get_browser_logger("CrawlerEngine")

    def crawl(
        self,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 10,
        allowed_domains: Optional[List[str]] = None,
        rate_limit_delay: float = 0.5,
    ) -> List[BrowserResponse]:
        """Perform a multi-page web research crawl starting from a seed URL.

        Args:
            start_url (str): Initial seed webpage URL.
            max_depth (int): Maximum depth level to crawl (default: 2).
            max_pages (int): Maximum total pages to fetch (default: 10).
            allowed_domains (Optional[List[str]]): Domain restriction whitelist.
            rate_limit_delay (float): Polling delay in seconds between fetches.

        Returns:
            List[BrowserResponse]: Collection of fetched BrowserResponse objects.
        """
        seed_url = sanitize_url(start_url)
        seed_domain = extract_domain(seed_url)

        target_domains = set(allowed_domains) if allowed_domains else {seed_domain}

        visited: Set[str] = set()
        queue: deque = deque([(seed_url, 0)])  # (url, depth)
        results: List[BrowserResponse] = []

        self._logger.info(
            f"Starting recursive crawl from '{seed_url}' (max_depth={max_depth}, max_pages={max_pages})"
        )

        while queue and len(results) < max_pages:
            current_url, depth = queue.popleft()

            if current_url in visited:
                continue
            visited.add(current_url)

            current_domain = extract_domain(current_url)
            if target_domains and current_domain not in target_domains:
                self._logger.debug(f"Skipping off-domain URL '{current_url}'")
                continue

            self._logger.info(f"Crawling [{len(results) + 1}/{max_pages}] Depth {depth}: '{current_url}'")

            try:
                response = self.browser.read_page(current_url)
                results.append(response)

                # Queue child internal links if max_depth is not reached
                if depth < max_depth and self.browser.current_state:
                    for link in self.browser.current_state.links:
                        child_url = sanitize_url(link.href)
                        if child_url not in visited and extract_domain(child_url) in target_domains:
                            queue.append((child_url, depth + 1))

            except Exception as e:
                self._logger.warning(f"Crawl fetch failed for '{current_url}': {e}")

            if rate_limit_delay > 0:
                time.sleep(rate_limit_delay)

        self._logger.info(f"Crawl completed. Fetched {len(results)} pages across {len(visited)} URLs.")
        return results
