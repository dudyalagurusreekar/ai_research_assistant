"""Abstract Base Class for Document Parsers in the Browser Tool.

Following SOLID principles (Single Responsibility & Interface Segregation),
this interface defines the contract that all concrete HTML/DOM parsers (Step 3)
must implement to convert raw content into structured `PageState`.
"""

from abc import ABC, abstractmethod
from typing import Optional

from tools.browser.models.response import FetchResult, PageMetadata
from tools.browser.models.page import PageState


class BaseParser(ABC):
    """Abstract interface for parsing raw response content into structured page state.

    Concrete subclasses in Step 3 will implement DOM parsing, link extraction,
    and text cleaning algorithms.
    """

    @abstractmethod
    def parse(self, fetch_result: FetchResult) -> PageState:
        """Parse a raw FetchResult into a structured PageState model.

        Args:
            fetch_result (FetchResult): Raw HTTP response payload and metadata.

        Returns:
            PageState: Structured page state containing title, text, links, and headings.

        Raises:
            ParsingError: If DOM structure or payload cannot be parsed.
        """
        pass

    @abstractmethod
    def extract_metadata(self, raw_html: str, url: str) -> PageMetadata:
        """Extract document metadata (title, meta description, open graph tags).

        Args:
            raw_html (str): Raw HTML string.
            url (str): Source document URL.

        Returns:
            PageMetadata: Extracted document metadata.
        """
        pass

    @abstractmethod
    def extract_clean_text(self, raw_html: str) -> str:
        """Extract cleaned main readable article text from HTML document.

        Args:
            raw_html (str): Raw HTML content string.

        Returns:
            str: Normalized readable plain text content.
        """
        pass
