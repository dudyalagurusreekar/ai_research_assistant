"""Long-Term Memory Provider strategy implementation."""

from typing import List, Dict, Optional
from tools.memory.interfaces.memory_interfaces import IMemoryProvider
from tools.memory.models.memory_models import MemoryItem, MemoryType, MemoryQuery
from infrastructure.artifacts import ArtifactStore
from infrastructure.logging.logger import StructuredLogger


class LongTermMemoryProvider(IMemoryProvider):
    """Persistent storage strategy for long-term consolidated knowledge and historical records."""

    def __init__(self, artifact_store: Optional[ArtifactStore] = None) -> None:
        self._logger = StructuredLogger("LongTermMemoryProvider")
        self._artifact_store = artifact_store
        self._items: Dict[str, MemoryItem] = {}

    @property
    def memory_type(self) -> MemoryType:
        return MemoryType.LONG_TERM

    async def store(self, item: MemoryItem) -> str:
        """Store memory item in long-term storage."""
        item.memory_type = MemoryType.LONG_TERM
        self._items[item.memory_id] = item

        if self._artifact_store:
            try:
                import json
                await self._artifact_store.save_artifact(
                    name=f"lt_mem_{item.memory_id}.json",
                    artifact_type="memory_record",
                    content=json.dumps(item.to_dict()),
                    mime_type="application/json",
                    metadata={"memory_id": item.memory_id, "importance": item.importance},
                )
            except Exception as e:
                self._logger.warning(f"Error persisting memory artifact: {e}")

        self._logger.info(f"Stored long-term memory '{item.memory_id}'")
        return item.memory_id

    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve memory item by ID."""
        item = self._items.get(memory_id)
        if item:
            item.touch()
        return item

    async def query(self, memory_query: MemoryQuery) -> List[MemoryItem]:
        """Query long-term memory items."""
        results = []
        for item in self._items.values():
            if item.importance < memory_query.min_importance:
                continue
            if memory_query.query_text and memory_query.query_text.lower() not in item.content.lower():
                continue
            if memory_query.tags and not any(t in item.tags for t in memory_query.tags):
                continue
            results.append(item)

        results.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
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
