"""Production Web Crawling Engine for the Browser Tool Subsystem.

This module implements the central `CrawlerEngine` class. It coordinates graph traversal
strategies (BFS/DFS), robots.txt compliance, sitemap parsing, link deduplication,
link lineage tracking, stateful checkpoint saving/loading, and automatic memory cleanup.
"""

import json
import time
from typing import List, Set, Optional, Dict, Any, Callable, TYPE_CHECKING

from tools.browser.crawler.models import CrawlNode, CrawlStats, CrawlResult
from tools.browser.crawler.strategies import TraversalStrategy, BFSTraversal
from tools.browser.crawler.robots import RobotsTxtHandler
from tools.browser.crawler.sitemap import SitemapParser
from tools.browser.models.page import PageState
from tools.browser.utils.helpers import extract_domain, sanitize_url
from tools.browser.utils.logging import get_browser_logger

if TYPE_CHECKING:
    from tools.browser.core.browser import Browser


class CrawlerEngine:
    """Production Web Crawling Engine.

    Follows Clean Architecture and SOLID principles, acting as a task-oriented crawler.
    """

    def __init__(self, browser: "Browser") -> None:
        """Initialize CrawlerEngine.

        Args:
            browser (Browser): Parent Browser orchestrator reference.
        """
        self.browser = browser
        self._logger = get_browser_logger("CrawlerEngine")
        self.robots_handler = RobotsTxtHandler()
        self.sitemap_parser = SitemapParser()

    def crawl(
        self,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 10,
        allowed_domains: Optional[List[str]] = None,
        respect_robots_txt: bool = False,
        strategy: Optional[TraversalStrategy] = None,
        rate_limit_delay: float = 0.5,
        keep_raw_html: bool = False,
    ) -> CrawlResult:
        """Perform a multi-page web research crawl starting from a seed URL."""
        seed_url = sanitize_url(start_url)
        seed_domain = extract_domain(seed_url)
        target_domains = set(allowed_domains) if allowed_domains else {seed_domain}

        traversal = strategy or BFSTraversal()
        traversal.add_url(seed_url, depth=0, parent_url=None)

        visited: Set[str] = set()
        nodes: List[CrawlNode] = []
        link_graph: Dict[str, List[str]] = {}
        stats = CrawlStats()

        self._logger.info(
            f"Starting crawl from '{seed_url}' (Strategy: {traversal.__class__.__name__}, "
            f"max_depth={max_depth}, max_pages={max_pages})"
        )

        user_agent = self.browser.config.user_agent

        while traversal.has_urls() and len(nodes) < max_pages:
            item = traversal.pop_url()
            if not item:
                break
            current_url, depth, parent_url = item

            if current_url in visited:
                continue
            visited.add(current_url)

            # Check domain restriction
            current_domain = extract_domain(current_url)
            if target_domains and current_domain not in target_domains:
                continue

            # Check robots.txt rules
            if respect_robots_txt:
                allowed = self.robots_handler.can_fetch(user_agent, current_url, self.browser.fetcher)
                if not allowed:
                    self._logger.warning(f"Skipping '{current_url}' due to robots.txt restriction.")
                    stats.robots_disallowed_count += 1
                    continue

            self._logger.info(f"Crawling [{len(nodes) + 1}/{max_pages}] Depth {depth}: '{current_url}'")

            try:
                response = self.browser.read_page(current_url, keep_raw_html=keep_raw_html)
                page_state = self.browser.current_state

                node = CrawlNode(
                    url=response.url,
                    depth=depth,
                    parent_url=parent_url,
                    page_state=page_state,
                    status_code=response.status_code,
                )
                nodes.append(node)
                stats.total_pages_crawled += 1

                # Queue child links if max_depth is not exceeded
                if depth < max_depth and page_state:
                    child_urls = []
                    for link in page_state.links:
                        child_url = sanitize_url(link.href)
                        if child_url not in visited and child_url not in child_urls and extract_domain(child_url) in target_domains:
                            traversal.add_url(child_url, depth + 1, parent_url=response.url)
                            child_urls.append(child_url)

                    link_graph[response.url] = child_urls

            except Exception as e:
                self._logger.warning(f"Crawl fetch failed for '{current_url}': {e}")
                stats.failed_urls_count += 1

            if rate_limit_delay > 0:
                time.sleep(rate_limit_delay)

        stats.finalize()
        self._logger.info(
            f"Crawl finished. Processed {stats.total_pages_crawled} pages in {stats.total_duration_seconds}s."
        )

        return CrawlResult(seed_url=seed_url, nodes=nodes, stats=stats, link_graph=link_graph)

    def crawl_domain(
        self,
        domain: str,
        max_depth: int = 2,
        max_pages: int = 15,
        **kwargs: Any,
    ) -> CrawlResult:
        """Crawl an entire target domain starting from its root homepage.

        Args:
            domain (str): Target domain hostname (e.g. 'example.org').
            max_depth (int): Maximum depth.
            max_pages (int): Page limit.

        Returns:
            CrawlResult: Crawl result container.
        """
        seed_url = f"https://{domain}" if not domain.startswith("http") else domain
        return self.crawl(
            start_url=seed_url,
            max_depth=max_depth,
            max_pages=max_pages,
            allowed_domains=[extract_domain(seed_url)],
            **kwargs,
        )

    def crawl_site_map(
        self,
        sitemap_url: str,
        max_pages: int = 15,
        **kwargs: Any,
    ) -> CrawlResult:
        """Discover URLs from a sitemap.xml file and crawl them.

        Args:
            sitemap_url (str): Target sitemap.xml URL.
            max_pages (int): Page limit.

        Returns:
            CrawlResult: Crawl output model.
        """
        urls = self.sitemap_parser.parse_sitemap(sitemap_url, fetcher=self.browser.fetcher)
        if not urls:
            return CrawlResult(seed_url=sitemap_url)

        seed_url = urls[0]
        traversal = BFSTraversal()
        for u in urls[:max_pages]:
            traversal.add_url(u, depth=1, parent_url=sitemap_url)

        return self.crawl(
            start_url=seed_url,
            max_pages=max_pages,
            strategy=traversal,
            **kwargs,
        )

    def crawl_until(
        self,
        start_url: str,
        condition_fn: Callable[[PageState], bool],
        max_pages: int = 10,
        **kwargs: Any,
    ) -> Optional[CrawlNode]:
        """Crawl until a custom condition function evaluates to True.

        Args:
            start_url (str): Seed URL.
            condition_fn (Callable[[PageState], bool]): Predicate evaluated on each page state.
            max_pages (int): Safety page limit.

        Returns:
            Optional[CrawlNode]: Matching CrawlNode or None if condition wasn't met.
        """
        crawl_res = self.crawl(start_url=start_url, max_pages=max_pages, **kwargs)
        for node in crawl_res.nodes:
            if node.page_state and condition_fn(node.page_state):
                return node
        return None

    def save_checkpoint(self, result: CrawlResult, filepath: str) -> None:
        """Persist crawl state and nodes to a JSON checkpoint file.

        Args:
            result (CrawlResult): Crawl output model to serialize.
            filepath (str): Target JSON file path.
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
        self._logger.info(f"Saved crawl checkpoint to '{filepath}'")

    def load_checkpoint(self, filepath: str) -> Dict[str, Any]:
        """Load a saved crawl checkpoint JSON file.

        Args:
            filepath (str): Target JSON file path.

        Returns:
            Dict[str, Any]: Serialized checkpoint dictionary.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._logger.info(f"Loaded crawl checkpoint from '{filepath}'")
        return data
