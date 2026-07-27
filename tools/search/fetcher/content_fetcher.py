"""Content Fetcher integrating Browser Tool and Document Intelligence Platform."""

import os
import urllib.parse
from typing import Dict, Any, Optional
from tools.search.interfaces.provider import IContentFetcher
from infrastructure.logging.logger import StructuredLogger


class ContentFetcher(IContentFetcher):
    """Retrieves web pages via Browser Tool and automatically routes downloaded files into Document Tool."""

    def __init__(
        self,
        browser_facade: Optional[Any] = None,
        document_facade: Optional[Any] = None,
    ) -> None:
        self._logger = StructuredLogger("ContentFetcher")
        self._browser_facade = browser_facade
        self._document_facade = document_facade

    async def fetch_and_ingest(
        self,
        url_or_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fetch content from URL or path and route files to Document Intelligence Platform if applicable."""
        opts = options or {}
        self._logger.info(f"Fetching content for '{url_or_path}'")

        # Check if local file or downloadable document extension
        ext = os.path.splitext(url_or_path.split("?")[0])[1].lower()
        is_doc = ext in [".pdf", ".docx", ".pptx", ".xlsx", ".csv", ".txt", ".md", ".html", ".xml", ".zip", ".png", ".jpg"] or os.path.exists(url_or_path)

        if is_doc and self._document_facade:
            self._logger.info(f"Routing document file '{url_or_path}' to Document Intelligence Platform")
            try:
                doc = await self._document_facade.parse_document(url_or_path)
                return {
                    "source": url_or_path,
                    "content_type": "document",
                    "document_id": doc.document_id,
                    "title": doc.metadata.title or os.path.basename(url_or_path),
                    "full_text": doc.get_full_text(),
                    "metadata": doc.metadata.to_dict(),
                    "sections_count": len(doc.sections),
                    "chunks_count": len(doc.chunks),
                }
            except Exception as e:
                self._logger.error(f"Error parsing document via Document Tool: {e}")

        # Web page fetching via Browser Tool or fallback
        if self._browser_facade:
            self._logger.info(f"Delegating web navigation to Browser Tool for '{url_or_path}'")
            try:
                res = await self._browser_facade.execute_action("navigate", url=url_or_path)
                return {
                    "source": url_or_path,
                    "content_type": "web_page",
                    "status": "success",
                    "raw_result": res,
                }
            except Exception as e:
                self._logger.warning(f"Browser navigation fallback for '{url_or_path}': {e}")

        return {
            "source": url_or_path,
            "content_type": "web_page",
            "status": "simulated",
            "full_text": f"Simulated content retrieved for {url_or_path}",
        }
