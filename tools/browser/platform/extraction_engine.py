"""Extraction Engine for Sprint 11 Browser Automation Platform."""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from tools.browser.platform.models import ExtractionResult, ExtractionSchema

logger = logging.getLogger("Tools.Browser.Platform.ExtractionEngine")


class ExtractionEngine:
    """Performs structured extraction, schema mapping, table parsing, and metadata scraping."""

    async def extract_text(self, page: Any, selector: Optional[str] = None) -> str:
        """Extract clean text content from page or target selector."""
        html_content = ""
        if hasattr(page, "content"):
            try:
                html_content = await page.content()
            except Exception as e:
                logger.warning(f"Error fetching page content for text extraction: {e}")

        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        if selector:
            target = soup.select_one(selector)
            if target:
                return target.get_text(separator="\n", strip=True)
            return ""

        return soup.get_text(separator="\n", strip=True)

    async def extract_tables(self, page: Any, selector: Optional[str] = None) -> List[List[Dict[str, str]]]:
        """Extract HTML tables as structured JSON list of dict records."""
        html_content = ""
        if hasattr(page, "content"):
            try:
                html_content = await page.content()
            except Exception as e:
                logger.warning(f"Error fetching page content for table extraction: {e}")

        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        tables = soup.select(selector) if selector else soup.find_all("table")

        result_tables = []
        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue

            headers = []
            header_row = rows[0]
            header_cells = header_row.find_all(["th", "td"])
            if header_cells:
                headers = [cell.get_text(strip=True) or f"col_{i}" for i, cell in enumerate(header_cells)]
                row_start = 1
            else:
                row_start = 0

            records = []
            for row in rows[row_start:]:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                record = {}
                for i, cell in enumerate(cells):
                    col_name = headers[i] if i < len(headers) else f"col_{i}"
                    record[col_name] = cell.get_text(strip=True)
                if record:
                    records.append(record)

            if records:
                result_tables.append(records)

        return result_tables

    async def extract_schema(self, page: Any, schema: ExtractionSchema) -> ExtractionResult:
        """Extract structured data matching an ExtractionSchema."""
        start_time = time.time()
        html_content = ""
        if hasattr(page, "content"):
            try:
                html_content = await page.content()
            except Exception as e:
                logger.warning(f"Error fetching page content for schema extraction: {e}")

        if not html_content:
            return ExtractionResult(
                schema_id=schema.schema_id,
                success=False,
                extracted_data=[],
                error="Empty HTML content",
                extraction_time_ms=(time.time() - start_time) * 1000,
            )

        soup = BeautifulSoup(html_content, "html.parser")

        if schema.multiple and schema.container_selector:
            containers = soup.select(schema.container_selector)
            items = []
            for container in containers:
                item = {}
                for field_name, field_selector in schema.fields.items():
                    elem = container.select_one(field_selector)
                    item[field_name] = elem.get_text(strip=True) if elem else ""
                items.append(item)

            return ExtractionResult(
                schema_id=schema.schema_id,
                success=True,
                extracted_data=items,
                item_count=len(items),
                extraction_time_ms=(time.time() - start_time) * 1000,
            )
        else:
            item = {}
            for field_name, field_selector in schema.fields.items():
                elem = soup.select_one(field_selector)
                item[field_name] = elem.get_text(strip=True) if elem else ""

            return ExtractionResult(
                schema_id=schema.schema_id,
                success=True,
                extracted_data=item,
                item_count=1 if item else 0,
                extraction_time_ms=(time.time() - start_time) * 1000,
            )

    async def extract_metadata(self, page: Any) -> Dict[str, Any]:
        """Extract OpenGraph, Twitter, and JSON-LD structured metadata from page."""
        html_content = ""
        if hasattr(page, "content"):
            try:
                html_content = await page.content()
            except Exception:
                pass

        if not html_content:
            return {}

        soup = BeautifulSoup(html_content, "html.parser")
        metadata: Dict[str, Any] = {"open_graph": {}, "twitter": {}, "json_ld": []}

        # Meta tags
        for meta in soup.find_all("meta"):
            prop = meta.get("property") or meta.get("name")
            content = meta.get("content")
            if not prop or not content:
                continue

            if prop.startswith("og:"):
                metadata["open_graph"][prop[3:]] = content
            elif prop.startswith("twitter:"):
                metadata["twitter"][prop[8:]] = content

        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            if script.string:
                try:
                    data = json.loads(script.string)
                    metadata["json_ld"].append(data)
                except Exception:
                    pass

        return metadata
