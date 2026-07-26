"""Unit tests for Step 3: HTML Cleaning and Parsing Layer (HTMLCleaner, BS4Parser, Extractors, ParserFactory).

Tests HTML cleaning, metadata extraction, document outline extraction, internal/external link
classification, image resolution, tabular data parsing, form extraction, JSON-LD structured data parsing,
and Browser orchestrator integration.
"""

import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import httpx

from tools.browser.config import BrowserConfig
from tools.browser.constants import PageStatus
from tools.browser.core.browser import Browser
from tools.browser.models import FetchResult, PageState, LinkInfo, FormInfo, PageMetadata
from tools.browser.parsers import (
    HTMLCleaner,
    BS4Parser,
    ParserFactory,
    MetadataExtractor,
    TextExtractor,
    LinkExtractor,
    ImageExtractor,
    TableExtractor,
    FormExtractor,
    StructuredDataExtractor,
)


SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Research Overview</title>
    <meta name="description" content="A comprehensive report on artificial intelligence research.">
    <meta name="keywords" content="AI, Machine Learning, Deep Learning">
    <link rel="canonical" href="https://example.org/ai-research">
    <meta property="og:title" content="AI Research Report 2026">
    <meta property="og:type" content="article">
    <meta property="og:image" content="https://example.org/og-banner.jpg">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": "AI Research Progress"
    }
    </script>
    <style>body { font-family: sans-serif; }</style>
    <script>console.log('tracking code');</script>
</head>
<body>
    <!-- Header Boilerplate -->
    <header>
        <nav class="nav-menu">
            <a href="/home">Home</a> | <a href="/contact">Contact</a>
        </nav>
    </header>

    <div class="ad-banner">Advertisement Banner</div>

    <main>
        <article>
            <h1>Artificial Intelligence Frontiers</h1>
            <p>Artificial intelligence is transforming modern computing architectures rapidly.</p>

            <h2>Key Innovations</h2>
            <p>Recent breakthroughs include deep learning, transformer models, and autonomous agents.</p>
            <ul>
                <li>Transformer Architecture</li>
                <li>Reinforcement Learning</li>
                <li>Agentic Workflows</li>
            </ul>

            <h3>Comparative Performance Metrics</h3>
            <table>
                <caption>Model Benchmarks</caption>
                <thead>
                    <tr><th>Model</th><th>Accuracy</th><th>Latency (ms)</th></tr>
                </thead>
                <tbody>
                    <tr><td>Model A</td><td>94.5%</td><td>120</td></tr>
                    <tr><td>Model B</td><td>96.8%</td><td>85</td></tr>
                </tbody>
            </table>

            <p>Read more research at the <a href="https://external-lab.org/papers" title="External Lab Papers">External Lab</a>.</p>
            <p>Internal documentation is available at <a href="/docs/guide.html">Internal Guide</a>.</p>

            <img src="/images/chart.png" alt="Benchmark Comparison Chart">
        </article>

        <form action="/search" method="POST">
            <input type="text" name="q" placeholder="Search papers...">
            <input type="submit" value="Search">
        </form>
    </main>

    <footer class="footer">
        <p>&copy; 2026 AI Research Institute</p>
    </footer>

    <div style="display: none;">Hidden tracking pixel</div>
</body>
</html>
"""


class TestHTMLParserAndCleaner(unittest.TestCase):
    """Test suite for HTMLCleaner, Modular Extractors, BS4Parser, and ParserFactory."""

    def setUp(self):
        self.cleaner = HTMLCleaner()
        self.parser = BS4Parser(cleaner=self.cleaner)
        self.base_url = "https://example.org/ai-research"
        self.fetch_result = FetchResult(
            url=self.base_url,
            status_code=200,
            content=SAMPLE_HTML.encode("utf-8"),
            encoding="utf-8",
            mime_type="text/html",
        )

    def test_html_cleaner_strips_noise_and_boilerplate(self):
        """Test HTMLCleaner removes scripts, styles, comments, header, footer, nav, and hidden elements."""
        clean_soup = self.cleaner.clean(SAMPLE_HTML)

        # Check decomposed noise tags
        self.assertIsNone(clean_soup.find("script"))
        self.assertIsNone(clean_soup.find("style"))
        self.assertIsNone(clean_soup.find("header"))
        self.assertIsNone(clean_soup.find("footer"))
        self.assertIsNone(clean_soup.find("nav"))

        # Check comment removal
        text_content = str(clean_soup)
        self.assertNotIn("Header Boilerplate", text_content)
        self.assertNotIn("console.log", text_content)

    def test_metadata_extractor(self):
        """Test MetadataExtractor parses title, meta tags, canonical link, and Open Graph attributes."""
        clean_soup = self.cleaner.clean(SAMPLE_HTML)
        extractor = MetadataExtractor()
        metadata = extractor.extract(clean_soup, self.base_url)

        self.assertEqual(metadata.title, "AI Research Overview")
        self.assertIn("comprehensive report", metadata.description)
        self.assertEqual(metadata.keywords, "AI, Machine Learning, Deep Learning")
        self.assertEqual(metadata.canonical_url, "https://example.org/ai-research")
        self.assertEqual(metadata.language, "en")
        self.assertEqual(metadata.og_type, "article")
        self.assertEqual(metadata.open_graph["og:title"], "AI Research Report 2026")
        self.assertEqual(metadata.open_graph["og:image"], "https://example.org/og-banner.jpg")

    def test_text_extractor(self):
        """Test TextExtractor parses main text, headings outline, paragraphs, and list items."""
        clean_soup = self.cleaner.clean(SAMPLE_HTML)
        extractor = TextExtractor()
        text_data = extractor.extract(clean_soup)

        self.assertIn("Artificial Intelligence Frontiers", text_data["main_text"])
        self.assertIn("Transformer Architecture", text_data["main_text"])

        # Verify Headings
        self.assertEqual(len(text_data["headings"]), 3)
        self.assertEqual(text_data["headings"][0], {"level": "h1", "text": "Artificial Intelligence Frontiers"})
        self.assertEqual(text_data["headings"][1], {"level": "h2", "text": "Key Innovations"})

        # Verify Lists
        self.assertGreaterEqual(len(text_data["lists"]), 1)
        self.assertIn("Transformer Architecture", text_data["lists"][0])

    def test_link_extractor_classification(self):
        """Test LinkExtractor resolves URLs and classifies internal vs external targets."""
        clean_soup = self.cleaner.clean(SAMPLE_HTML)
        extractor = LinkExtractor()
        links = extractor.extract(clean_soup, self.base_url)

        self.assertGreaterEqual(len(links), 2)

        # External Link check
        ext_link = next(l for l in links if "external-lab.org" in l.href)
        self.assertEqual(ext_link.href, "https://external-lab.org/papers")
        self.assertEqual(ext_link.text, "External Lab")
        self.assertTrue(ext_link.is_external)

        # Internal Link check
        int_link = next(l for l in links if "/docs/guide.html" in l.href)
        self.assertEqual(int_link.href, "https://example.org/docs/guide.html")
        self.assertEqual(int_link.text, "Internal Guide")
        self.assertFalse(int_link.is_external)

    def test_image_extractor(self):
        """Test ImageExtractor resolves image source URLs and captures alt text."""
        clean_soup = self.cleaner.clean(SAMPLE_HTML)
        extractor = ImageExtractor()
        images = extractor.extract(clean_soup, self.base_url)

        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["src"], "https://example.org/images/chart.png")
        self.assertEqual(images[0]["alt"], "Benchmark Comparison Chart")

    def test_table_extractor(self):
        """Test TableExtractor parses headers and row cell matrices."""
        clean_soup = self.cleaner.clean(SAMPLE_HTML)
        extractor = TableExtractor()
        tables = extractor.extract(clean_soup)

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["caption"], "Model Benchmarks")
        self.assertEqual(tables[0]["headers"], ["Model", "Accuracy", "Latency (ms)"])
        self.assertEqual(len(tables[0]["rows"]), 2)
        self.assertEqual(tables[0]["rows"][0], ["Model A", "94.5%", "120"])
        self.assertEqual(tables[0]["rows"][1], ["Model B", "96.8%", "85"])

    def test_form_extractor(self):
        """Test FormExtractor parses action, method, and input attributes."""
        clean_soup = self.cleaner.clean(SAMPLE_HTML)
        extractor = FormExtractor()
        forms = extractor.extract(clean_soup, self.base_url)

        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0].action, "https://example.org/search")
        self.assertEqual(forms[0].method, "POST")
        self.assertGreaterEqual(len(forms[0].inputs), 1)
        self.assertEqual(forms[0].inputs[0]["name"], "q")

    def test_structured_data_extractor(self):
        """Test StructuredDataExtractor parses JSON-LD metadata objects."""
        # Uncleaned soup to ensure script tag presence for JSON-LD check
        soup = BeautifulSoup(SAMPLE_HTML, "lxml")
        extractor = StructuredDataExtractor()
        data = extractor.extract(soup)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["@type"], "TechArticle")
        self.assertEqual(data[0]["headline"], "AI Research Progress")

    def test_bs4_parser_end_to_end(self):
        """Test BS4Parser converts FetchResult into fully populated PageState DTO."""
        page_state = self.parser.parse(self.fetch_result)

        self.assertIsInstance(page_state, PageState)
        self.assertEqual(page_state.url, self.base_url)
        self.assertEqual(page_state.metadata.title, "AI Research Overview")
        self.assertIn("Artificial Intelligence Frontiers", page_state.main_text)
        self.assertEqual(len(page_state.headings), 3)
        self.assertEqual(len(page_state.tables), 1)
        self.assertEqual(len(page_state.forms), 1)
        self.assertEqual(len(page_state.images), 1)
        self.assertGreaterEqual(len(page_state.links), 2)

    def test_parser_factory_strategy(self):
        """Test ParserFactory strategy creation."""
        parser = ParserFactory.create_parser("BS4")
        self.assertIsInstance(parser, BS4Parser)

    @patch("httpx.Client.stream")
    def test_browser_integration_full_pipeline(self, mock_stream):
        """Test end-to-end Browser orchestrator pipeline: Fetcher -> Cleaner -> Parser -> PageState."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = httpx.Headers({"content-type": "text/html"})
        mock_response.iter_bytes.return_value = [SAMPLE_HTML.encode("utf-8")]
        mock_response.encoding = "utf-8"
        mock_response.history = []
        mock_response.url = self.base_url

        mock_stream.return_value.__enter__.return_value = mock_response

        # Initialize Browser engine with auto-wired HTTPFetcher & BS4Parser
        browser = Browser(config=BrowserConfig(timeout_seconds=5.0))
        response = browser.navigate(self.base_url)

        self.assertEqual(response.status, PageStatus.PARSED)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.metadata.title, "AI Research Overview")
        self.assertIn("Artificial Intelligence Frontiers", response.extracted_text)
        self.assertGreater(response.metrics.parse_duration_ms, 0)
        self.assertGreater(response.metrics.fetch_duration_ms, 0)

        browser.close()


if __name__ == "__main__":
    unittest.main()
