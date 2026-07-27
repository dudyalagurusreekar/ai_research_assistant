"""Result Normalizer for standardizing search items."""

import re
from typing import List
from tools.search.models.search_models import SearchResultItem
from infrastructure.logging.logger import StructuredLogger


class ResultNormalizer:
    """Standardizes raw provider output items into clean SearchResultItem objects."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ResultNormalizer")

    def normalize(self, items: List[SearchResultItem]) -> List[SearchResultItem]:
        """Clean and normalize a list of search result items."""
        normalized_items = []
        for item in items:
            item.title = self._clean_text(item.title) or "Untitled Search Result"
            item.snippet = self._clean_text(item.snippet)
            item.url = item.url.strip()
            normalized_items.append(item)
        return normalized_items

    def _clean_text(self, text: str) -> str:
        """Strip HTML tags and collapse whitespace."""
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", "", text)
        return " ".join(clean.split())
