"""Knowledge Index for storing and searching normalized document metadata."""

import re
from typing import List, Dict, Any
from tools.search.interfaces.provider import IKnowledgeIndex
from tools.search.models.search_models import KnowledgeIndexEntry
from infrastructure.logging.logger import StructuredLogger


class KnowledgeIndex(IKnowledgeIndex):
    """In-memory searchable index for processed document metadata, snippets, and search results."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("KnowledgeIndex")
        self._entries: Dict[str, KnowledgeIndexEntry] = {}

    async def index_entry(self, entry: KnowledgeIndexEntry) -> str:
        """Add or update entry in knowledge index."""
        self._entries[entry.entry_id] = entry
        self._logger.debug(f"Indexed knowledge entry '{entry.entry_id}' ({entry.title})")
        return entry.entry_id

    async def search_index(self, query: str, top_k: int = 10) -> List[KnowledgeIndexEntry]:
        """Search knowledge index using term overlap scoring."""
        query_terms = set(re.findall(r"\w+", query.lower()))
        if not query_terms:
            return list(self._entries.values())[:top_k]

        scored_entries = []
        for entry in self._entries.values():
            text_to_match = f"{entry.title} {entry.summary} {' '.join(entry.keywords)}".lower()
            entry_terms = set(re.findall(r"\w+", text_to_match))
            overlap = len(query_terms & entry_terms)
            if overlap > 0:
                score = overlap / len(query_terms)
                scored_entries.append((score, entry))

        scored_entries.sort(key=lambda x: x[0], reverse=True)
        results = [entry for _, entry in scored_entries[:top_k]]
        self._logger.info(f"KnowledgeIndex search '{query}' returned {len(results)} matches.")
        return results
