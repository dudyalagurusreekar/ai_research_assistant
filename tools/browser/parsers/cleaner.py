"""HTML Cleaning Module for the Browser Tool Subsystem.

This module provides the `HTMLCleaner` class, implementing the Single Responsibility Principle
by sanitizing raw HTML, stripping non-content noise (scripts, styles, ads, navigation bars,
footers, hidden elements, tracking code), and returning a clean DOM tree preserving
meaningful document structure.
"""

from typing import List, Optional, Set
from bs4 import BeautifulSoup, Comment, Tag

# Tags that never contain human-readable body content
NOISE_TAGS: Set[str] = {
    "script",
    "style",
    "noscript",
    "template",
    "iframe",
    "svg",
    "canvas",
    "embed",
    "object",
    "applet",
}

# Structural boilerplate layout tags
BOILERPLATE_TAGS: Set[str] = {
    "header",
    "footer",
    "nav",
    "aside",
}

# CSS selectors matching common advertisements, cookie banners, and noise widgets
NOISE_SELECTORS: List[str] = [
    "[hidden]",
    '[aria-hidden="true"]',
    '[style*="display: none"]',
    '[style*="display:none"]',
    ".ad",
    ".ads",
    ".advertisement",
    ".cookie-banner",
    ".cookie-consent",
    ".popup",
    ".modal",
    ".social-share",
]


class HTMLCleaner:
    """Sanitizer responsible for stripping noise and boilerplate from HTML documents.

    Follows Single Responsibility Principle to ensure parser logic focuses purely on extraction.
    """

    def __init__(
        self,
        remove_boilerplate: bool = True,
        extra_noise_selectors: Optional[List[str]] = None,
    ) -> None:
        """Initialize HTMLCleaner settings.

        Args:
            remove_boilerplate (bool): Whether to strip header, footer, nav, aside elements.
            extra_noise_selectors (Optional[List[str]]): Additional CSS selectors to strip.
        """
        self.remove_boilerplate = remove_boilerplate
        self.noise_selectors = list(NOISE_SELECTORS)
        if extra_noise_selectors:
            self.noise_selectors.extend(extra_noise_selectors)

    def clean(self, raw_html: str) -> BeautifulSoup:
        """Sanitize raw HTML and return a clean BeautifulSoup DOM tree.

        Args:
            raw_html (str): Unprocessed HTML payload string.

        Returns:
            BeautifulSoup: Cleaned DOM tree preserving semantic content.
        """
        if not raw_html:
            return BeautifulSoup("<html><body></body></html>", "lxml")

        soup = BeautifulSoup(raw_html, "lxml")

        # 1. Remove HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 2. Decompose absolute noise tags (script, style, noscript, etc.)
        for tag_name in NOISE_TAGS:
            for element in soup.find_all(tag_name):
                element.decompose()

        # 3. Decompose boilerplate structural tags if enabled
        if self.remove_boilerplate:
            for tag_name in BOILERPLATE_TAGS:
                for element in soup.find_all(tag_name):
                    element.decompose()

        # 4. Decompose noise CSS selectors (hidden, ads, popups)
        for selector in self.noise_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception:
                pass

        # 5. Strip inline event attributes (onclick, onload) and noisy inline styles
        for tag in soup.find_all(True):
            if isinstance(tag, Tag):
                attrs = dict(tag.attrs)
                for attr_name in attrs:
                    if attr_name.lower().startswith("on") or attr_name.lower() == "style":
                        del tag.attrs[attr_name]

        return soup

    def clean_to_string(self, raw_html: str) -> str:
        """Sanitize raw HTML string and return cleaned HTML string.

        Args:
            raw_html (str): Unprocessed raw HTML.

        Returns:
            str: Cleaned HTML string markup.
        """
        clean_soup = self.clean(raw_html)
        return str(clean_soup)
