"""Short-Term Memory Provider strategy implementation."""

import asyncio
from typing import List, Dict, Optional
from tools.memory.interfaces.memory_interfaces import IMemoryProvider
from tools.memory.models.memory_models import MemoryItem, MemoryType, MemoryQuery
from infrastructure.logging.logger import StructuredLogger


class ShortTermMemoryProvider(IMemoryProvider):
    """In-memory bounded storage strategy for short-term observations and conversation turns."""

    def __init__(self, capacity: int = 100) -> None:
        self._logger = StructuredLogger("ShortTermMemoryProvider")
        self._capacity = capacity
        self._items: Dict[str, MemoryItem] = {}

    @property
    def memory_type(self) -> MemoryType:
        return MemoryType.SHORT_TERM

    async def store(self, item: MemoryItem) -> str:
        """Store memory item in short-term buffer."""
        item.memory_type = MemoryType.SHORT_TERM
        
        # Enforce capacity by removing oldest low-importance items if capacity exceeded
        if len(self._items) >= self._capacity and item.memory_id not in self._items:
            oldest_key = min(self._items.keys(), key=lambda k: (self._items[k].importance, self._items[k].created_at))
            del self._items[oldest_key]

        self._items[item.memory_id] = item
        self._logger.debug(f"Stored short-term memory '{item.memory_id}'")
        return item.memory_id

    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve memory item by ID."""
        item = self._items.get(memory_id)
        if item:
            item.touch()
        return item

    async def query(self, memory_query: MemoryQuery) -> List[MemoryItem]:
        """Query short-term memory items."""
        results = []
        for item in self._items.values():
            if item.importance < memory_query.min_importance:
                continue
            if memory_query.query_text and memory_query.query_text.lower() not in item.content.lower():
                continue
            if memory_query.tags and not any(t in item.tags for t in memory_query.tags):
                continue
            results.append(item)

        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[: memory_query.max_results]

    async def delete(self, memory_id: str) -> bool:
        """Delete memory item."""
        if memory_id in self._items:
            del self._items[memory_id]
            return True
        return False

    async def list_all(self) -> List[MemoryItem]:
        """Return all items."""
        return list(self._items.values())
