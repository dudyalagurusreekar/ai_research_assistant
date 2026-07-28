"""Unified MemoryToolFacade for the Memory Platform."""

import json
from typing import Dict, List, Any, Optional

from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult
from core.models.event import Event
from core.events import AsyncEventBus
from tools.memory.models.memory_models import (
    MemoryItem,
    MemoryType,
    MemoryLink,
    MemorySearchResult,
    MemoryConsolidationResult,
)
from tools.memory.manager.memory_manager import MemoryManager
from infrastructure.logging.logger import StructuredLogger


class MemoryToolFacade(ITool):
    """Public unified API facade for the Memory Platform."""

    name = "memory_tool"
    description = "Centralized persistent memory tool for knowledge storage, retrieval, graph linking, and consolidation."

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        event_bus: Optional[AsyncEventBus] = None,
    ) -> None:
        self.name = "memory_tool"
        self._logger = StructuredLogger("MemoryToolFacade")
        self._event_bus = event_bus or AsyncEventBus()
        self._manager = memory_manager or MemoryManager()

        self._metadata = ToolMetadata(
            name="memory_tool",
            version="1.0.0",
            description="Centralized persistent memory tool for knowledge storage, retrieval, graph linking, and consolidation.",
            capabilities=["memory", "remember", "recall", "graph_linking", "consolidation"],
            parameters_schema={
                "action": "Action to perform ('remember', 'recall', 'link', 'consolidate', 'ingest')",
                "content": "Memory content text to store",
                "query": "Query text for memory recall",
                "memory_type": "Memory type ('short_term', 'long_term', 'session', 'working', 'knowledge')",
            },
            tags=["memory", "persistence", "knowledge"],
            is_async=True,
            enabled=True,
        )

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata descriptor."""
        return self._metadata

    async def forward(self, action: str = "recall", **kwargs) -> str:
        """Standard tool execution wrapper returning JSON string."""
        try:
            if action in ["remember", "store"]:
                kwargs_copy = dict(kwargs)
                content = kwargs_copy.pop("content", kwargs_copy.pop("text", ""))
                m_type = kwargs_copy.pop("memory_type", MemoryType.SHORT_TERM)
                if isinstance(m_type, str):
                    m_type = MemoryType(m_type)
                item = await self.remember(content, memory_type=m_type, **kwargs_copy)
                return json.dumps(item.to_dict(), indent=2)
            elif action in ["recall", "search", "query"]:
                kwargs_copy = dict(kwargs)
                q_text = kwargs_copy.pop("query", kwargs_copy.pop("q", ""))
                res = await self.recall(q_text, **kwargs_copy)
                return json.dumps(res.to_dict(), indent=2)
            elif action in ["link", "connect"]:
                src = kwargs.get("source_id", "")
                tgt = kwargs.get("target_id", "")
                rel = kwargs.get("relationship_type", "relates_to")
                lnk = await self.link(src, tgt, relationship_type=rel)
                return json.dumps(lnk.to_dict(), indent=2)
            elif action in ["consolidate", "decay"]:
                c_res = await self.consolidate()
                return json.dumps(c_res.to_dict(), indent=2)
            else:
                return json.dumps({"error": f"Unknown memory action '{action}'"}, indent=2)
        except Exception as e:
            self._logger.error(f"Error in MemoryToolFacade.forward action '{action}': {e}")
            return json.dumps({"error": str(e)}, indent=2)

    async def execute(self, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Execute method returning ToolResult object conforming to ITool interface."""
        params = dict(parameters or {})
        params.update(kwargs)
        action = params.get("action", "recall")
        try:
            output_json = await self.forward(action=action, **params)
            data = json.loads(output_json)
            if isinstance(data, dict) and "error" in data:
                return ToolResult.error(error_message=data["error"])
            return ToolResult.success(data=data)
        except Exception as e:
            return ToolResult.error(error_message=str(e))

    async def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 1.0,
        source: str = "user",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> MemoryItem:
        """Remember a new item in memory platform."""
        try:
            item = await self._manager.store_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                source=source,
                tags=tags,
                metadata=metadata,
            )
            await self._publish_event("memory.created", {"memory_id": item.memory_id, "memory_type": item.memory_type.value})
            return item
        except Exception as e:
            await self._publish_event("memory.failed", {"action": "remember", "error": str(e)})
            raise

    async def recall(self, query: str, **kwargs) -> MemorySearchResult:
        """Recall items from memory matching query."""
        try:
            res = await self._manager.recall(query, **kwargs)
            await self._publish_event("memory.retrieved", {"query": query, "found_count": res.total_found})
            return res
        except Exception as e:
            await self._publish_event("memory.failed", {"action": "recall", "error": str(e)})
            raise

    async def link(self, source_id: str, target_id: str, relationship_type: str = "relates_to") -> MemoryLink:
        """Create a semantic link between two memories."""
        lnk = await self._manager.link_memories(source_id, target_id, relationship_type=relationship_type)
        await self._publish_event("memory.linked", {"link_id": lnk.link_id, "source": source_id, "target": target_id})
        return lnk

    async def consolidate(self) -> MemoryConsolidationResult:
        """Run memory consolidation cycle."""
        c_res = await self._manager.consolidate_memories()
        await self._publish_event("memory.consolidated", c_res.to_dict())
        return c_res

    async def ingest_document(self, document: Any) -> List[MemoryItem]:
        """Ingest a NormalizedDocument into Knowledge Memory."""
        items = await self._manager.ingest_normalized_document(document)
        await self._publish_event("memory.created", {"ingested_document": getattr(document, "document_id", ""), "items_count": len(items)})
        return items

    async def ingest_search_results(self, search_result: Any) -> List[MemoryItem]:
        """Ingest a NormalizedSearchResult into Knowledge Memory."""
        items = await self._manager.ingest_search_result(search_result)
        await self._publish_event("memory.created", {"ingested_search": getattr(search_result, "search_id", ""), "items_count": len(items)})
        return items

    async def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish domain event over AsyncEventBus."""
        if self._event_bus:
            try:
                event_obj = Event(
                    event_type=event_type,
                    source="MemoryToolFacade",
                    payload=payload,
                )
                await self._event_bus.publish(event_obj)
            except Exception as e:
                self._logger.warning(f"Error publishing memory event '{event_type}': {e}")
