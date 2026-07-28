"""Concrete BeautifulSoup4 / lxml Document Parser Strategy for the Browser Tool.

This module implements `BS4Parser`, inheriting from `BaseParser`. It uses
`HTMLCleaner` to sanitize raw HTML and coordinates modular extractors
to produce a structured `PageState` DTO.
"""

from typing import Optional

from tools.browser.core.base_parser import BaseParser
from tools.browser.exceptions import DOMParseError
from tools.browser.models.page import PageState
from tools.browser.models.response import FetchResult, PageMetadata
from tools.browser.parsers.cleaner import HTMLCleaner
from tools.browser.parsers.extractors import (
    MetadataExtractor,
    TextExtractor,
    LinkExtractor,
    ImageExtractor,
    TableExtractor,
    FormExtractor,
    StructuredDataExtractor,
)
from tools.browser.utils.logging import get_browser_logger


class BS4Parser(BaseParser):
    """Production-grade HTML/DOM parser powered by BeautifulSoup4 and lxml.

    Follows the Pipeline Pattern and Composition:
    Raw HTML -> HTMLCleaner -> Modular Extractors -> PageState DTO.
    """

    def __init__(
        self,
        cleaner: Optional[HTMLCleaner] = None,
        metadata_extractor: Optional[MetadataExtractor] = None,
        text_extractor: Optional[TextExtractor] = None,
        link_extractor: Optional[LinkExtractor] = None,
        image_extractor: Optional[ImageExtractor] = None,
        table_extractor: Optional[TableExtractor] = None,
        form_extractor: Optional[FormExtractor] = None,
        structured_data_extractor: Optional[StructuredDataExtractor] = None,
    ) -> None:
        """Initialize BS4Parser with cleaner and composed extractor strategies."""
        self._logger = get_browser_logger("BS4Parser")
        self.cleaner = cleaner or HTMLCleaner()

        # Composed extractors (Dependency Injection & Single Responsibility)
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.text_extractor = text_extractor or TextExtractor()
        self.link_extractor = link_extractor or LinkExtractor()
        self.image_extractor = image_extractor or ImageExtractor()
        self.table_extractor = table_extractor or TableExtractor()
        self.form_extractor = form_extractor or FormExtractor()
        self.structured_data_extractor = structured_data_extractor or StructuredDataExtractor()

    def parse(self, fetch_result: FetchResult) -> PageState:
        """Parse raw network FetchResult into a structured PageState model.

        Args:
            fetch_result (FetchResult): Raw HTTP response payload and metadata.

        Returns:
            PageState: Structured page state model.

        Raises:
            DOMParseError: If HTML cannot be parsed into a DOM tree.
        """
        raw_html = fetch_result.text
        url = fetch_result.url

        try:
            self._logger.debug(f"Parsing document HTML for URL '{url}' ({len(raw_html)} bytes)")

            # 1. Clean raw HTML (remove scripts, styles, ads, noise)
            clean_soup = self.cleaner.clean(raw_html)

            # 2. Delegate extraction to composed extractors
            metadata = self.metadata_extractor.extract(clean_soup, url)
            text_data = self.text_extractor.extract(clean_soup)
            links = self.link_extractor.extract(clean_soup, url)
            images = self.image_extractor.extract(clean_soup, url)
            tables = self.table_extractor.extract(clean_soup)
            forms = self.form_extractor.extract(clean_soup, url)
            structured_data = self.structured_data_extractor.extract(clean_soup)

            # 3. Construct unified PageState DTO
            return PageState(
                url=url,
                metadata=metadata,
                main_text=text_data["main_text"],
                headings=text_data["headings"],
                paragraphs=text_data["paragraphs"],
                lists=text_data["lists"],
                links=links,
                forms=forms,
                images=images,
                tables=tables,
                structured_data=structured_data,
            )

        except Exception as e:
            self._logger.error(f"DOM parsing error for '{url}': {e}")
            raise DOMParseError(f"Failed to parse document DOM for '{url}': {e}")

    def extract_metadata(self, raw_html: str, url: str) -> PageMetadata:
        """Extract document metadata (title, meta description, open graph tags).

        Args:
            raw_html (str): Raw HTML string.
            url (str): Source document URL.

        Returns:
            PageMetadata: Extracted document metadata.
        """
        try:
            clean_soup = self.cleaner.clean(raw_html)
            return self.metadata_extractor.extract(clean_soup, url)
        except Exception as e:
            raise DOMParseError(f"Metadata extraction failed for '{url}': {e}")

    def extract_clean_text(self, raw_html: str) -> str:
        """Extract cleaned main readable text from HTML document.

        Args:
            raw_html (str): Raw HTML content string.

        Returns:
            str: Normalized readable plain text content.
        """
        try:
            clean_soup = self.cleaner.clean(raw_html)
            text_data = self.text_extractor.extract(clean_soup)
            return text_data["main_text"]
        except Exception as e:
            raise DOMParseError(f"Text extraction failed: {e}")
