"""Page State and Abstraction Models for the Browser Tool.

This module defines DOM abstractions, link structures, form models, and
`PageState` representation used by content parsers and agent readers.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from tools.browser.models.response import PageMetadata


@dataclass
class LinkInfo:
    """Structured link extracted from a web document.

    Attributes:
        href (str): Resolved absolute or relative URL target.
        text (str): Anchor text contents.
        title (Optional[str]): Title attribute of the anchor tag.
        is_external (bool): Flag indicating if link points to an external domain.
    """

    href: str
    text: str = ""
    title: Optional[str] = None
    is_external: bool = False


@dataclass
class FormInfo:
    """Structured representation of an HTML form element.

    Attributes:
        action (str): Form action target URL.
        method (str): HTTP method (GET or POST).
        inputs (List[Dict[str, str]]): List of input field attributes (name, type, value).
    """

    action: str
    method: str = "GET"
    inputs: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ElementNode:
    """Lightweight abstraction representing an HTML element in parsed DOM tree.

    Attributes:
        tag (str): HTML element tag name (e.g. 'div', 'p', 'h1', 'a').
        attributes (Dict[str, str]): HTML tag attributes (id, class, src, etc.).
        text (str): Direct text content inside element.
        children (List['ElementNode']): Nested child element nodes.
    """

    tag: str
    attributes: Dict[str, str] = field(default_factory=dict)
    text: str = ""
    children: List["ElementNode"] = field(default_factory=list)


@dataclass
class PageState:
    """Structured in-memory representation of a fully parsed web page.

    Attributes:
        url (str): Page URL.
        metadata (PageMetadata): Page metadata.
        main_text (str): Cleaned readable main article/content text.
        headings (List[Dict[str, str]]): List of heading elements ({'level': 'h1', 'text': '...'}).
        links (List[LinkInfo]): Extracted anchor links.
        forms (List[FormInfo]): Extracted form elements.
        images (List[Dict[str, str]]): Extracted image elements ({'src': '...', 'alt': '...'}).
        tables (List[Dict[str, Any]]): Extracted tabular data ({'headers': [...], 'rows': [[...]]}).
        paragraphs (List[str]): List of extracted paragraph content blocks.
        lists (List[List[str]]): List of bullet or numbered list items.
        structured_data (List[Dict[str, Any]]): JSON-LD and Schema.org metadata objects.
        dom_tree (Optional[ElementNode]): Root node of parsed lightweight element tree.
    """

    url: str
    metadata: PageMetadata = field(default_factory=PageMetadata)
    main_text: str = ""
    headings: List[Dict[str, str]] = field(default_factory=list)
    links: List[LinkInfo] = field(default_factory=list)
    forms: List[FormInfo] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    lists: List[List[str]] = field(default_factory=list)
    structured_data: List[Dict[str, Any]] = field(default_factory=list)
    dom_tree: Optional[ElementNode] = None

    def get_summary(self, max_length: int = 500) -> str:
        """Return a quick plain text summary of page content."""
        if not self.main_text:
            return f"Page: {self.metadata.title or self.url} (No main text content)"
        return self.main_text[:max_length] + ("..." if len(self.main_text) > max_length else "")
