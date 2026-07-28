"""Search index for fast memory term matching and retrieval."""

import re
from typing import List, Dict
from tools.memory.interfaces.memory_interfaces import IMemoryIndex
from tools.memory.models.memory_models import MemoryItem, MemoryQuery
from infrastructure.logging.logger import StructuredLogger


class MemoryIndex(IMemoryIndex):
    """In-memory index supporting term matching and filtering across memory records."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("MemoryIndex")
        self._items: Dict[str, MemoryItem] = {}

    async def index_memory(self, item: MemoryItem) -> None:
        """Add or update memory item in search index."""
        self._items[item.memory_id] = item
        self._logger.debug(f"Indexed memory item '{item.memory_id}'")

    async def remove_from_index(self, memory_id: str) -> None:
        """Remove memory item from index."""
        if memory_id in self._items:
            del self._items[memory_id]

    async def search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Search indexed memory items using term matching and score calculation."""
        query_terms = set(re.findall(r"\w+", query.query_text.lower())) if query.query_text else set()
        matched: List[MemoryItem] = []

        for item in self._items.values():
            if query.memory_types and item.memory_type not in query.memory_types:
                continue
            if item.importance < query.min_importance:
                continue
            if query.tags and not any(t in item.tags for t in query.tags):
                continue
            
            if query_terms:
                item_terms = set(re.findall(r"\w+", item.content.lower()))
                if not (query_terms & item_terms):
                    continue
            matched.append(item)

        matched.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
        return matched[: query.max_results]
