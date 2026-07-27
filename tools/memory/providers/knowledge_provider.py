"""Knowledge Memory Provider strategy implementation."""

from typing import List, Dict, Optional
from tools.memory.interfaces.memory_interfaces import IMemoryProvider
from tools.memory.models.memory_models import MemoryItem, MemoryType, MemoryQuery
from infrastructure.logging.logger import StructuredLogger


class KnowledgeMemoryProvider(IMemoryProvider):
    """Storage strategy for ingested documents, web search results, and scientific domain knowledge."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("KnowledgeMemoryProvider")
        self._items: Dict[str, MemoryItem] = {}

    @property
    def memory_type(self) -> MemoryType:
        return MemoryType.KNOWLEDGE

    async def store(self, item: MemoryItem) -> str:
        item.memory_type = MemoryType.KNOWLEDGE
        self._items[item.memory_id] = item
        self._logger.debug(f"Stored knowledge memory '{item.memory_id}'")
        return item.memory_id

    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        item = self._items.get(memory_id)
        if item:
            item.touch()
        return item

    async def query(self, memory_query: MemoryQuery) -> List[MemoryItem]:
        results = []
        for item in self._items.values():
            if memory_query.query_text and memory_query.query_text.lower() not in item.content.lower():
                continue
            results.append(item)
        results.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
        return results[: memory_query.max_results]

    async def delete(self, memory_id: str) -> bool:
        if memory_id in self._items:
            del self._items[memory_id]
            return True
        return False

    async def list_all(self) -> List[MemoryItem]:
        return list(self._items.values())
