"""Unit tests for Step 4: Browser Service Layer, Search, Content Analysis, and Crawling Architecture.

Tests ContentRouter strategy assignment, LanguageDetector, high-level AI operations (read_page,
extract_information, search_page, find_links, collect_documents), automatic memory payload disposal,
RAII context managers, and CrawlerEngine multi-page web research crawling.
"""

import json
import unittest
from unittest.mock import MagicMock, patch
import httpx

from tools.browser.config import BrowserConfig
from tools.browser.constants import PageStatus
from tools.browser.core.browser import Browser
from tools.browser.models import FetchResult, PageMetadata, PageState, LinkInfo
from tools.browser.services import (
    ContentRouter,
    JSONParser,
    TextParser,
    PDFParser,
    LanguageDetector,
    CrawlerEngine,
)


class TestBrowserServiceLayer(unittest.TestCase):
    """Test suite verifying Step 4 Browser Service Layer functionality."""

    def setUp(self):
        self.config = BrowserConfig(timeout_seconds=5.0)

    def test_content_router_mime_routing(self):
        """Test ContentRouter assigns matching parser strategies by MIME type or extension."""
        router = ContentRouter()

        # HTML
        res_html = FetchResult(url="https://e.org", status_code=200, mime_type="text/html")
        parser_html = router.route(res_html)
        self.assertEqual(parser_html.__class__.__name__, "BS4Parser")

        # JSON
        res_json = FetchResult(url="https://e.org/api", status_code=200, mime_type="application/json")
        parser_json = router.route(res_json)
        self.assertIsInstance(parser_json, JSONParser)

        # Plain Text
        res_text = FetchResult(url="https://e.org/notes.txt", status_code=200, mime_type="text/plain")
        parser_text = router.route(res_text)
        self.assertIsInstance(parser_text, TextParser)

        # PDF
        res_pdf = FetchResult(url="https://e.org/paper.pdf", status_code=200, mime_type="application/pdf")
        parser_pdf = router.route(res_pdf)
        self.assertIsInstance(parser_pdf, PDFParser)

    def test_language_detector(self):
        """Test LanguageDetector identifies language code from metadata or text."""
        detector = LanguageDetector()

        meta_en = PageMetadata(language="en-US")
        self.assertEqual(detector.detect(meta_en), "en")

        meta_es = PageMetadata(language="es")
        self.assertEqual(detector.detect(meta_es), "es")

        meta_fallback = PageMetadata()
        text_fr = "Bonjour tout le monde. C'est un rapport dans la langue francaise pour les agents."
        self.assertEqual(detector.detect(meta_fallback, text_fr), "fr")

    @patch("httpx.Client.stream")
    def test_read_page_and_memory_payload_release(self, mock_stream):
        """Test read_page executes full pipeline and automatically disposes raw byte buffers."""
        html_payload = """<html><body>
        <h1>Quantum Computing Breakthrough</h1>
        <p>Researchers have achieved quantum supremacy using superconducting qubits.</p>
        <a href="https://external.com/paper.pdf">Download Paper PDF</a>
        </body></html>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = httpx.Headers({"content-type": "text/html"})
        mock_response.iter_bytes.return_value = [html_payload.encode("utf-8")]
        mock_response.encoding = "utf-8"
        mock_response.history = []
        mock_response.url = "https://quantum-lab.org/article"

        mock_stream.return_value.__enter__.return_value = mock_response

        with Browser(config=self.config) as browser:
            response = browser.read_page("https://quantum-lab.org/article")

            self.assertEqual(response.status, PageStatus.PARSED)
            self.assertIn("Quantum Computing Breakthrough", response.extracted_text)
            self.assertIsNone(response.raw_html)  # Released by automatic memory management!
            self.assertEqual(browser.current_state.metadata.language, "en")

    @patch("httpx.Client.stream")
    def test_extract_information(self, mock_stream):
        """Test extract_information matches query against headings, paragraphs, and tables."""
        html_payload = """<html><head><title>Artificial Intelligence Benchmark</title></head><body>
        <h1>Artificial Intelligence Benchmark</h1>
        <p>This report covers transformer models and reinforcement learning benchmarks.</p>
        <table>
            <tr><th>Framework</th><th>Score</th></tr>
            <tr><td>TensorFlow</td><td>92.4</td></tr>
            <tr><td>PyTorch</td><td>96.1</td></tr>
        </table>
        </body></html>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = httpx.Headers({"content-type": "text/html"})
        mock_response.iter_bytes.return_value = [html_payload.encode("utf-8")]
        mock_response.encoding = "utf-8"
        mock_response.history = []
        mock_response.url = "https://ai-benchmarks.com/results"

        mock_stream.return_value.__enter__.return_value = mock_response

        with Browser(config=self.config) as browser:
            info = browser.extract_information("https://ai-benchmarks.com/results", query="transformer PyTorch")

            self.assertIn("Artificial Intelligence Benchmark", info["title"])
            self.assertGreaterEqual(len(info["matched_paragraphs"]), 1)
            self.assertGreaterEqual(len(info["matched_tables"]), 1)

    @patch("httpx.Client.stream")
    def test_search_page_and_find_links(self, mock_stream):
        """Test search_page in-page snippet matching and find_links link filtering."""
        html_payload = """<html><body>
        <p>First paragraph detailing autonomous systems.</p>
        <p>Second paragraph explaining agentic reasoning models in detail.</p>
        <a href="/internal/docs">Internal Docs</a>
        <a href="https://external-ref.org/report">External Report</a>
        <a href="/data/dataset.csv">Dataset CSV</a>
        </body></html>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = httpx.Headers({"content-type": "text/html"})
        mock_response.iter_bytes.return_value = [html_payload.encode("utf-8")]
        mock_response.encoding = "utf-8"
        mock_response.history = []
        mock_response.url = "https://agent-research.org"

        mock_stream.return_value.__enter__.return_value = mock_response

        with Browser(config=self.config) as browser:
            browser.read_page("https://agent-research.org")

            # In-page search
            snippets = browser.search_page("agentic reasoning")
            self.assertGreaterEqual(len(snippets), 1)
            self.assertIn("agentic reasoning", snippets[0]["snippet"].lower())

            # External links filter
            ext_links = browser.find_links(filters={"is_external": True})
            self.assertEqual(len(ext_links), 1)
            self.assertEqual(ext_links[0].href, "https://external-ref.org/report")

            # Document collection
            docs = browser.collect_documents("https://agent-research.org")
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0]["extension"], "csv")

    @patch("httpx.Client.stream")
    def test_crawler_engine(self, mock_stream):
        """Test CrawlerEngine multi-page recursive web research crawl."""
        html_seed = """<html><body>
        <h1>Seed Research Page</h1>
        <a href="https://example.org/page1">Page 1</a>
        <a href="https://example.org/page2">Page 2</a>
        <a href="https://off-domain.com">Off Domain</a>
        </body></html>"""

        html_page1 = "<html><body><h1>Page 1 Content</h1></body></html>"
        html_page2 = "<html><body><h1>Page 2 Content</h1></body></html>"

        res_seed = MagicMock()
        res_seed.status_code = 200
        res_seed.headers = httpx.Headers({"content-type": "text/html"})
        res_seed.iter_bytes.return_value = [html_seed.encode("utf-8")]
        res_seed.encoding = "utf-8"
        res_seed.history = []
        res_seed.url = "https://example.org/seed"

        res_page1 = MagicMock()
        res_page1.status_code = 200
        res_page1.headers = httpx.Headers({"content-type": "text/html"})
        res_page1.iter_bytes.return_value = [html_page1.encode("utf-8")]
        res_page1.encoding = "utf-8"
        res_page1.history = []
        res_page1.url = "https://example.org/page1"

        res_page2 = MagicMock()
        res_page2.status_code = 200
        res_page2.headers = httpx.Headers({"content-type": "text/html"})
        res_page2.iter_bytes.return_value = [html_page2.encode("utf-8")]
        res_page2.encoding = "utf-8"
        res_page2.history = []
        res_page2.url = "https://example.org/page2"

        ctx_seed = MagicMock()
        ctx_seed.__enter__.return_value = res_seed

        ctx1 = MagicMock()
        ctx1.__enter__.return_value = res_page1

        ctx2 = MagicMock()
        ctx2.__enter__.return_value = res_page2

        mock_stream.side_effect = [ctx_seed, ctx1, ctx2]

        with Browser(config=self.config) as browser:
            crawl_results = browser.crawl(
                start_url="https://example.org/seed",
                max_depth=1,
                max_pages=3,
                allowed_domains=["example.org"],
                rate_limit_delay=0.0,
            )

            nodes = crawl_results.nodes if hasattr(crawl_results, "nodes") else crawl_results
            self.assertGreaterEqual(len(nodes), 2)
            urls = [n.url for n in nodes]
            self.assertIn("https://example.org/seed", urls)
            self.assertIn("https://example.org/page1", urls)
            self.assertNotIn("https://off-domain.com", urls)


if __name__ == "__main__":
    unittest.main()
