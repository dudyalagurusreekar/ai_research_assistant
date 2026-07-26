"""Content Router and Strategy-based Content Parsers for the Browser Tool Subsystem.

This module implements `ContentRouter`, following the Strategy and Factory patterns to route
network response payloads to their matching parser strategies based on MIME type or URL extension.
Includes built-in parsers for HTML, JSON, Plain Text/Markdown, and PDF documents.
"""

import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from tools.browser.core.base_parser import BaseParser
from tools.browser.exceptions import DOMParseError
from tools.browser.models.page import PageState
from tools.browser.models.response import FetchResult, PageMetadata
from tools.browser.parsers.bs4_parser import BS4Parser
from tools.browser.utils.helpers import clean_text
from tools.browser.utils.logging import get_browser_logger


class JSONParser(BaseParser):
    """Parser strategy for application/json response payloads."""

    def parse(self, fetch_result: FetchResult) -> PageState:
        url = fetch_result.url
        raw_text = fetch_result.text
        try:
            parsed_data = json.loads(raw_text) if raw_text else {}
            pretty_json = json.dumps(parsed_data, indent=2)
            structured_data = [parsed_data] if isinstance(parsed_data, dict) else (parsed_data if isinstance(parsed_data, list) else [])

            return PageState(
                url=url,
                metadata=PageMetadata(title=url, description="JSON API Response"),
                main_text=pretty_json,
                headings=[{"level": "h1", "text": "JSON Document"}],
                paragraphs=[pretty_json[:500]],
                structured_data=structured_data,
            )
        except Exception as e:
            raise DOMParseError(f"Failed to parse JSON content for '{url}': {e}")

    def extract_metadata(self, raw_html: str, url: str) -> PageMetadata:
        return PageMetadata(title=url, description="JSON Content")

    def extract_clean_text(self, raw_html: str) -> str:
        return raw_html


class TextParser(BaseParser):
    """Parser strategy for text/plain, text/markdown, and application/xml payloads."""

    def parse(self, fetch_result: FetchResult) -> PageState:
        url = fetch_result.url
        text = fetch_result.text or ""
        cleaned = clean_text(text)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        return PageState(
            url=url,
            metadata=PageMetadata(title=url, description="Plain Text Document"),
            main_text=cleaned,
            headings=[{"level": "h1", "text": "Plain Text Document"}],
            paragraphs=paragraphs[:20],
        )

    def extract_metadata(self, raw_html: str, url: str) -> PageMetadata:
        return PageMetadata(title=url, description="Plain Text")

    def extract_clean_text(self, raw_html: str) -> str:
        return clean_text(raw_html)


class PDFParser(BaseParser):
    """Parser strategy for application/pdf document payloads."""

    def parse(self, fetch_result: FetchResult) -> PageState:
        url = fetch_result.url
        content_len = len(fetch_result.content)
        placeholder_text = f"[PDF Document: {url} ({content_len} bytes)]"

        return PageState(
            url=url,
            metadata=PageMetadata(title=url, description=f"PDF Document ({content_len} bytes)"),
            main_text=placeholder_text,
            headings=[{"level": "h1", "text": "PDF Document"}],
            paragraphs=[placeholder_text],
        )

    def extract_metadata(self, raw_html: str, url: str) -> PageMetadata:
        return PageMetadata(title=url, description="PDF Document")

    def extract_clean_text(self, raw_html: str) -> str:
        return f"[PDF Document: {url}]"


class ContentRouter:
    """Strategy Router for assigning the correct BaseParser strategy based on content type.

    Follows the Strategy and Open-Closed principles so new document format handlers
    (e.g., DOCX, XLSX, OCR) can be registered dynamically.
    """

    def __init__(self, default_parser: Optional[BaseParser] = None) -> None:
        """Initialize ContentRouter with strategy registry."""
        self._logger = get_browser_logger("ContentRouter")
        self.default_parser = default_parser or BS4Parser()

        self._mime_map: Dict[str, BaseParser] = {
            "text/html": self.default_parser,
            "application/xhtml+xml": self.default_parser,
            "application/json": JSONParser(),
            "text/json": JSONParser(),
            "text/plain": TextParser(),
            "text/markdown": TextParser(),
            "text/xml": TextParser(),
            "application/xml": TextParser(),
            "application/pdf": PDFParser(),
        }

        self._ext_map: Dict[str, BaseParser] = {
            ".html": self.default_parser,
            ".htm": self.default_parser,
            ".json": JSONParser(),
            ".txt": TextParser(),
            ".md": TextParser(),
            ".xml": TextParser(),
            ".pdf": PDFParser(),
        }

    def register_parser(self, mime_type: str, parser: BaseParser) -> None:
        """Register a custom parser strategy for a specific MIME type.

        Args:
            mime_type (str): Target MIME type (e.g. 'application/pdf').
            parser (BaseParser): Concrete parser strategy instance.
        """
        self._mime_map[mime_type.lower()] = parser

    def route(self, fetch_result: FetchResult) -> BaseParser:
        """Route a network FetchResult to its matching parser strategy.

        Args:
            fetch_result (FetchResult): Raw network response result.

        Returns:
            BaseParser: Matched parser strategy instance.
        """
        mime_type = fetch_result.mime_type.lower()
        if mime_type in self._mime_map:
            self._logger.debug(f"Routed MIME type '{mime_type}' to {self._mime_map[mime_type].__class__.__name__}")
            return self._mime_map[mime_type]

        # Extension fallback check
        parsed_url = urlparse(fetch_result.url)
        path = parsed_url.path.lower()
        for ext, parser in self._ext_map.items():
            if path.endswith(ext):
                self._logger.debug(f"Routed file extension '{ext}' to {parser.__class__.__name__}")
                return parser

        self._logger.debug(f"Fallback to default parser {self.default_parser.__class__.__name__} for '{mime_type}'")
        return self.default_parser
