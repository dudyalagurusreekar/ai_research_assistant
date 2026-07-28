"""Modular Extractor Components for the Browser Tool Subsystem.

This module provides single-responsibility extractor classes for parsing metadata,
main text, document outlines, links, images, tables, forms, and JSON-LD structured data.
Following SOLID principles (Single Responsibility & Open-Closed), each extractor is decoupled,
allowing future extractors (e.g. OCR, Video, Charts) to be added seamlessly.
"""

import json
from typing import List, Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag

from tools.browser.models.page import LinkInfo, FormInfo
from tools.browser.models.response import PageMetadata
from tools.browser.utils.helpers import extract_domain, clean_text


class MetadataExtractor:
    """Extractor responsible for parsing document metadata, canonical tags, and Open Graph attributes."""

    def extract(self, soup: BeautifulSoup, base_url: str) -> PageMetadata:
        """Extract PageMetadata DTO from document DOM tree.

        Args:
            soup (BeautifulSoup): DOM tree.
            base_url (str): Page URL for resolving relative links.

        Returns:
            PageMetadata: Populated metadata DTO.
        """
        title = ""
        description = None
        keywords = None
        canonical_url = None
        language = None
        og_type = None
        open_graph: Dict[str, str] = {}

        # 1. Document Title
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title = clean_text(title_tag.string)

        # 2. HTML Language Attribute
        html_tag = soup.find("html")
        if html_tag and isinstance(html_tag, Tag):
            language = html_tag.get("lang") or html_tag.get("xml:lang")

        # 3. Meta Tags (description, keywords, canonical)
        for meta in soup.find_all("meta"):
            if not isinstance(meta, Tag):
                continue

            name = meta.get("name", "").lower()
            property_attr = meta.get("property", "").lower()
            content = meta.get("content", "")

            if not content:
                continue

            content_clean = clean_text(content)

            if name == "description" and not description:
                description = content_clean
            elif name == "keywords" and not keywords:
                keywords = content_clean

            # Open Graph Tags
            if property_attr.startswith("og:") or name.startswith("og:"):
                og_key = property_attr or name
                open_graph[og_key] = content_clean
                if og_key == "og:title" and not title:
                    title = content_clean
                elif og_key == "og:description" and not description:
                    description = content_clean
                elif og_key == "og:type":
                    og_type = content_clean

        # 4. Canonical URL Link
        canonical_tag = soup.find("link", rel=lambda r: r and "canonical" in r.lower())
        if canonical_tag and isinstance(canonical_tag, Tag):
            href = canonical_tag.get("href")
            if href:
                canonical_url = urljoin(base_url, href)

        return PageMetadata(
            title=title or base_url,
            description=description,
            keywords=keywords,
            canonical_url=canonical_url,
            language=language,
            og_type=og_type,
            open_graph=open_graph,
        )


class TextExtractor:
    """Extractor responsible for parsing main body text, headings, paragraphs, and list items."""

    def extract(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract structured text content from DOM tree.

        Args:
            soup (BeautifulSoup): Cleaned DOM tree.

        Returns:
            Dict[str, Any]: Dictionary containing main_text, headings, paragraphs, and lists.
        """
        # Target main content container if present (<article>, <main>, or <body>)
        container = soup.find("article") or soup.find("main") or soup.find("body") or soup

        # 1. Headings Extraction (H1 - H6)
        headings: List[Dict[str, str]] = []
        for level in range(1, 7):
            tag_name = f"h{level}"
            for h_tag in container.find_all(tag_name):
                text = clean_text(h_tag.get_text())
                if text:
                    headings.append({"level": tag_name, "text": text})

        # 2. Paragraphs Extraction
        paragraphs: List[str] = []
        for p_tag in container.find_all("p"):
            text = clean_text(p_tag.get_text())
            if text and len(text) > 10:  # Filter out trivial fragments
                paragraphs.append(text)

        # 3. Lists Extraction (<ul> / <ol>)
        lists: List[List[str]] = []
        for list_tag in container.find_all(["ul", "ol"]):
            items = []
            for li in list_tag.find_all("li", recursive=False):
                item_text = clean_text(li.get_text())
                if item_text:
                    items.append(item_text)
            if items:
                lists.append(items)

        # 4. Main Plain Text Representation
        main_text = clean_text(container.get_text(separator=" ", strip=True))

        return {
            "main_text": main_text,
            "headings": headings,
            "paragraphs": paragraphs,
            "lists": lists,
        }


class LinkExtractor:
    """Extractor responsible for parsing anchor links and classifying internal vs external targets."""

    def extract(self, soup: BeautifulSoup, base_url: str) -> List[LinkInfo]:
        """Extract resolved links from document.

        Args:
            soup (BeautifulSoup): DOM tree.
            base_url (str): Source document URL.

        Returns:
            List[LinkInfo]: Extracted LinkInfo DTOs.
        """
        links: List[LinkInfo] = []
        base_domain = extract_domain(base_url)
        seen_urls = set()

        for a_tag in soup.find_all("a", href=True):
            if not isinstance(a_tag, Tag):
                continue

            raw_href = a_tag["href"].strip()
            if not raw_href or raw_href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            absolute_href = urljoin(base_url, raw_href)
            if absolute_href in seen_urls:
                continue
            seen_urls.add(absolute_href)

            text = clean_text(a_tag.get_text())
            title = a_tag.get("title")
            target_domain = extract_domain(absolute_href)
            is_external = bool(target_domain and base_domain and target_domain != base_domain)

            links.append(
                LinkInfo(
                    href=absolute_href,
                    text=text,
                    title=title,
                    is_external=is_external,
                )
            )

        return links


class ImageExtractor:
    """Extractor responsible for parsing image elements, resolving URLs, and capturing alt text."""

    def extract(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract resolved image element attributes.

        Args:
            soup (BeautifulSoup): DOM tree.
            base_url (str): Source document URL.

        Returns:
            List[Dict[str, str]]: Image metadata dictionaries ({'src': '...', 'alt': '...'}).
        """
        images: List[Dict[str, str]] = []
        seen_srcs = set()

        for img in soup.find_all("img"):
            if not isinstance(img, Tag):
                continue

            src = img.get("src") or img.get("data-src")
            if not src:
                continue

            absolute_src = urljoin(base_url, src.strip())
            if absolute_src in seen_srcs:
                continue
            seen_srcs.add(absolute_src)

            alt = clean_text(img.get("alt", ""))
            title = img.get("title", "")

            images.append({
                "src": absolute_src,
                "alt": alt,
                "title": title,
            })

        return images


class TableExtractor:
    """Extractor responsible for parsing HTML tables into structured header and row matrixes."""

    def extract(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract tabular datasets from document.

        Args:
            soup (BeautifulSoup): DOM tree.

        Returns:
            List[Dict[str, Any]]: List of extracted table dicts ({'caption': '...', 'headers': [...], 'rows': [[...]]}).
        """
        tables: List[Dict[str, Any]] = []

        for table in soup.find_all("table"):
            if not isinstance(table, Tag):
                continue

            caption_tag = table.find("caption")
            caption = clean_text(caption_tag.get_text()) if caption_tag else ""

            headers: List[str] = []
            rows: List[List[str]] = []

            # Extract table headers
            thead = table.find("thead")
            header_rows = thead.find_all("tr") if thead else table.find_all("tr")[:1]
            if header_rows:
                for th in header_rows[0].find_all(["th", "td"]):
                    headers.append(clean_text(th.get_text()))

            # Extract table body rows
            tbody = table.find("tbody") or table
            tr_list = tbody.find_all("tr")
            # If headers were in first row, skip it in body loop
            start_idx = 1 if (header_rows and tr_list and tr_list[0] == header_rows[0]) else 0

            for tr in tr_list[start_idx:]:
                row_cells = [clean_text(td.get_text()) for td in tr.find_all(["td", "th"])]
                if any(row_cells):
                    rows.append(row_cells)

            if headers or rows:
                tables.append({
                    "caption": caption,
                    "headers": headers,
                    "rows": rows,
                })

        return tables


class FormExtractor:
    """Extractor responsible for parsing interactive form elements and input field attributes."""

    def extract(self, soup: BeautifulSoup, base_url: str) -> List[FormInfo]:
        """Extract structured form schemas.

        Args:
            soup (BeautifulSoup): DOM tree.
            base_url (str): Source document URL.

        Returns:
            List[FormInfo]: FormInfo DTO list.
        """
        forms: List[FormInfo] = []

        for form in soup.find_all("form"):
            if not isinstance(form, Tag):
                continue

            raw_action = form.get("action", "").strip()
            action = urljoin(base_url, raw_action) if raw_action else base_url
            method = form.get("method", "GET").upper()

            inputs: List[Dict[str, str]] = []
            for field in form.find_all(["input", "select", "textarea"]):
                if not isinstance(field, Tag):
                    continue

                name = field.get("name")
                if not name:
                    continue

                field_type = field.get("type", field.name).lower()
                value = field.get("value", "")
                placeholder = field.get("placeholder", "")

                inputs.append({
                    "name": name,
                    "type": field_type,
                    "value": value,
                    "placeholder": placeholder,
                })

            forms.append(FormInfo(action=action, method=method, inputs=inputs))

        return forms


class StructuredDataExtractor:
    """Extractor responsible for parsing JSON-LD (`<script type="application/ld+json">`) metadata."""

    def extract(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract parsed JSON-LD objects from document.

        Args:
            soup (BeautifulSoup): DOM tree.

        Returns:
            List[Dict[str, Any]]: Extracted JSON-LD dictionaries.
        """
        structured_data: List[Dict[str, Any]] = []

        for script in soup.find_all("script", type=lambda t: t and "ld+json" in t.lower()):
            if not script.string:
                continue
            try:
                data = json.loads(script.string.strip())
                if isinstance(data, dict):
                    structured_data.append(data)
                elif isinstance(data, list):
                    structured_data.extend([item for item in data if isinstance(item, dict)])
            except Exception:
                pass

        return structured_data
