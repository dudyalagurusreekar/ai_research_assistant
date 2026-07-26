"""Unit tests for Step 5: Web Crawling Engine Subsystem.

Tests BFS and DFS traversal strategies, RobotsTxtHandler compliance, SitemapParser,
CrawlerEngine domain crawling, sitemap crawling, conditional crawl_until, state checkpointing,
parent-child link graph tracking, and Browser facade integration.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import httpx

from tools.browser.config import BrowserConfig
from tools.browser.core.browser import Browser
from tools.browser.crawler import (
    BFSTraversal,
    DFSTraversal,
    RobotsTxtHandler,
    SitemapParser,
    CrawlerEngine,
    CrawlResult,
    CrawlNode,
)


class TestCrawlerSubsystem(unittest.TestCase):
    """Test suite verifying Step 5 Web Crawling Engine functionality."""

    def setUp(self):
        self.config = BrowserConfig(timeout_seconds=5.0)

    def test_traversal_strategies_bfs_and_dfs(self):
        """Test BFSTraversal FIFO queue vs DFSTraversal LIFO stack ordering."""
        # BFS
        bfs = BFSTraversal()
        bfs.add_url("https://e.org/a", 0)
        bfs.add_url("https://e.org/b", 0)
        self.assertEqual(bfs.pop_url()[0], "https://e.org/a")
        self.assertEqual(bfs.pop_url()[0], "https://e.org/b")

        # DFS
        dfs = DFSTraversal()
        dfs.add_url("https://e.org/a", 0)
        dfs.add_url("https://e.org/b", 0)
        self.assertEqual(dfs.pop_url()[0], "https://e.org/b")
        self.assertEqual(dfs.pop_url()[0], "https://e.org/a")

    def test_robots_txt_handler(self):
        """Test RobotsTxtHandler parsing and Disallow evaluation."""
        robots_txt_content = """User-agent: *
Disallow: /private/
Disallow: /admin/
"""
        handler = RobotsTxtHandler()
        mock_fetcher = MagicMock()
        mock_res = MagicMock()
        mock_res.success = True
        mock_res.text = robots_txt_content
        mock_fetcher.fetch.return_value = mock_res

        allowed = handler.can_fetch("TestBot", "https://example.org/public/page", mock_fetcher)
        disallowed = handler.can_fetch("TestBot", "https://example.org/private/secret", mock_fetcher)

        self.assertTrue(allowed)
        self.assertFalse(disallowed)

    def test_sitemap_parser(self):
        """Test SitemapParser location URL discovery."""
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.org/page1</loc></url>
            <url><loc>https://example.org/page2</loc></url>
        </urlset>"""

        parser = SitemapParser()
        mock_fetcher = MagicMock()
        mock_res = MagicMock()
        mock_res.success = True
        mock_res.text = sitemap_xml
        mock_fetcher.fetch.return_value = mock_res

        urls = parser.parse_sitemap("https://example.org/sitemap.xml", mock_fetcher)
        self.assertEqual(len(urls), 2)
        self.assertIn("https://example.org/page1", urls)
        self.assertIn("https://example.org/page2", urls)

    @patch("httpx.Client.stream")
    def test_crawler_engine_bfs_crawl_and_link_graph(self, mock_stream):
        """Test CrawlerEngine BFS crawling and parent-child link graph generation."""
        seed_html = """<html><head><title>Seed</title></head><body>
        <a href="https://example.org/child1">Child 1</a>
        <a href="https://example.org/child2">Child 2</a>
        </body></html>"""

        child1_html = "<html><head><title>Child 1</title></head><body>Child 1 Text</body></html>"
        child2_html = "<html><head><title>Child 2</title></head><body>Child 2 Text</body></html>"

        res_seed = MagicMock(status_code=200, headers=httpx.Headers({"content-type": "text/html"}), iter_bytes=MagicMock(return_value=[seed_html.encode("utf-8")]), encoding="utf-8", history=[], url="https://example.org/seed")
        res_c1 = MagicMock(status_code=200, headers=httpx.Headers({"content-type": "text/html"}), iter_bytes=MagicMock(return_value=[child1_html.encode("utf-8")]), encoding="utf-8", history=[], url="https://example.org/child1")
        res_c2 = MagicMock(status_code=200, headers=httpx.Headers({"content-type": "text/html"}), iter_bytes=MagicMock(return_value=[child2_html.encode("utf-8")]), encoding="utf-8", history=[], url="https://example.org/child2")

        mock_stream.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=res_seed)),
            MagicMock(__enter__=MagicMock(return_value=res_c1)),
            MagicMock(__enter__=MagicMock(return_value=res_c2)),
        ]

        with Browser(config=self.config) as browser:
            crawl_res = browser.crawl("https://example.org/seed", max_depth=1, max_pages=3, respect_robots_txt=False, rate_limit_delay=0.0)

            self.assertIsInstance(crawl_res, CrawlResult)
            self.assertEqual(len(crawl_res.nodes), 3)
            self.assertIn("https://example.org/seed", crawl_res.link_graph)
            self.assertEqual(len(crawl_res.link_graph["https://example.org/seed"]), 2)

    @patch("httpx.Client.stream")
    def test_crawl_until_condition(self, mock_stream):
        """Test crawl_until stops crawling when condition function evaluates to True."""
        html1 = '<html><body><p>Standard page without target concept.</p><a href="https://example.org/page2">Page 2</a></body></html>'
        html2 = "<html><body><p>Breakthrough in Quantum Computing achieved!</p></body></html>"

        res1 = MagicMock(status_code=200, headers=httpx.Headers({"content-type": "text/html"}), iter_bytes=MagicMock(return_value=[html1.encode("utf-8")]), encoding="utf-8", history=[], url="https://example.org/page1")
        res2 = MagicMock(status_code=200, headers=httpx.Headers({"content-type": "text/html"}), iter_bytes=MagicMock(return_value=[html2.encode("utf-8")]), encoding="utf-8", history=[], url="https://example.org/page2")

        mock_stream.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=res1)),
            MagicMock(__enter__=MagicMock(return_value=res2)),
        ]

        with Browser(config=self.config) as browser:
            match_node = browser.crawl_until(
                start_url="https://example.org/page1",
                condition_fn=lambda state: "quantum computing" in state.main_text.lower(),
                max_pages=5,
                respect_robots_txt=False,
                rate_limit_delay=0.0,
            )

            self.assertIsNotNone(match_node)
            self.assertEqual(match_node.url, "https://example.org/page2")

    def test_checkpoint_save_and_load(self):
        """Test stateful checkpoint saving and loading."""
        node = CrawlNode(url="https://example.org/test", depth=1, status_code=200)
        result = CrawlResult(seed_url="https://example.org/test", nodes=[node])

        engine = CrawlerEngine(MagicMock())
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp_path = tmp.name

        try:
            engine.save_checkpoint(result, tmp_path)
            loaded_data = engine.load_checkpoint(tmp_path)

            self.assertEqual(loaded_data["seed_url"], "https://example.org/test")
            self.assertEqual(loaded_data["total_pages"], 1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
