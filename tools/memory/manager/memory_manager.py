"""Unified Memory Manager coordinating storage providers, indexing, graph links, and consolidation."""

import asyncio
from typing import List, Dict, Any, Optional
from tools.memory.interfaces.memory_interfaces import IMemoryManager
from tools.memory.models.memory_models import (
    MemoryItem,
    MemoryType,
    MemoryLink,
    MemoryQuery,
    MemorySearchResult,
    MemoryConsolidationResult,
)
from tools.memory.registry.memory_registry import MemoryRegistry
from tools.memory.index.memory_index import MemoryIndex
from tools.memory.graph.relationship_graph import RelationshipGraph
from tools.memory.consolidation.consolidator import MemoryConsolidator
from tools.memory.providers.short_term_provider import ShortTermMemoryProvider
from tools.memory.providers.long_term_provider import LongTermMemoryProvider
from tools.memory.providers.session_provider import SessionMemoryProvider
from tools.memory.providers.working_provider import WorkingMemoryProvider
from tools.memory.providers.knowledge_provider import KnowledgeMemoryProvider
from infrastructure.logging.logger import StructuredLogger


class MemoryManager(IMemoryManager):
    """Central Memory Manager orchestrating storage, indexing, graph relationships, and consolidation."""

    def __init__(
        self,
        registry: Optional[MemoryRegistry] = None,
        index: Optional[MemoryIndex] = None,
        graph: Optional[RelationshipGraph] = None,
        consolidator: Optional[MemoryConsolidator] = None,
    ) -> None:
        self._logger = StructuredLogger("MemoryManager")
        self._registry = registry or MemoryRegistry()
        self._index = index or MemoryIndex()
        self._graph = graph or RelationshipGraph()
        self._consolidator = consolidator or MemoryConsolidator()

        # Register default memory providers if none registered
        if not self._registry.list_providers():
            self._registry.register(ShortTermMemoryProvider())
            self._registry.register(LongTermMemoryProvider())
            self._registry.register(SessionMemoryProvider())
            self._registry.register(WorkingMemoryProvider())
            self._registry.register(KnowledgeMemoryProvider())

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 1.0,
        source: str = "user",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """Store a new memory item into appropriate provider and index."""
        item = MemoryItem(
            memory_type=memory_type,
            content=content,
            importance=importance,
            source=source,
            tags=tags or [],
            metadata=metadata or {},
        )

        provider = self._registry.get_provider(memory_type)
        if not provider:
            # Fallback to short-term
            provider = self._registry.get_provider(MemoryType.SHORT_TERM)

        if provider:
            await provider.store(item)

        # Index item for search
        await self._index.index_memory(item)
        self._logger.info(f"Stored memory item '{item.memory_id}' in '{memory_type.value}' store.")
        return item

    async def recall(self, query_text: str, **kwargs) -> MemorySearchResult:
        """Recall memory items matching query text and filters."""
        m_types = kwargs.get("memory_types", [])
        if isinstance(m_types, str):
            m_types = [MemoryType(m_types)]
        elif isinstance(m_types, list):
            m_types = [MemoryType(m) if isinstance(m, str) else m for m in m_types]

        query = MemoryQuery(
            query_text=query_text,
            memory_types=m_types,
            tags=kwargs.get("tags", []),
            min_importance=kwargs.get("min_importance", 0.0),
            max_results=kwargs.get("max_results", 10),
            session_id=kwargs.get("session_id"),
        )

        # 1. Search via Index
        memories = await self._index.search(query)

        # 2. Touch recalled memories & calculate relevance scores
        relevance_scores: Dict[str, float] = {}
        for m in memories:
            m.touch()
            relevance_scores[m.memory_id] = round(m.importance, 4)

        result = MemorySearchResult(
            query=query,
            memories=memories,
            relevance_scores=relevance_scores,
            total_found=len(memories),
        )
        self._logger.info(f"Recalled {len(memories)} memories for query '{query_text}'")
        return result

    async def link_memories(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str = "relates_to",
        weight: float = 1.0,
    ) -> MemoryLink:
        """Create a semantic link between two memory records."""
        link = MemoryLink(
            source_memory_id=source_id,
            target_memory_id=target_id,
            relationship_type=relationship_type,
            weight=weight,
        )
        await self._graph.add_link(link)
        return link

    async def get_related_memories(self, memory_id: str, depth: int = 1) -> List[MemoryItem]:
        """Retrieve related memory items via relationship graph traversal."""
        related_ids = await self._graph.get_related_memories(memory_id, depth=depth)
        memories = []
        for p in self._registry.list_providers():
            for rid in related_ids:
                item = await p.retrieve(rid)
                if item and item not in memories:
                    memories.append(item)
        return memories

    async def consolidate_memories(self) -> MemoryConsolidationResult:
        """Run memory consolidation, importance decay, and pruning."""
        return await self._consolidator.consolidate(self._registry.list_providers())

    async def ingest_normalized_document(self, document: Any) -> List[MemoryItem]:
        """Ingest a NormalizedDocument object from Phase 4 Document Intelligence Platform."""
        stored_memories = []
        full_text = getattr(document, "get_full_text", lambda: "")() or getattr(document, "full_text", "")
        title = getattr(getattr(document, "metadata", None), "title", "Document") or "Document"

        main_mem = await self.store_memory(
            content=f"Document '{title}': {full_text[:500]}",
            memory_type=MemoryType.KNOWLEDGE,
            source="document",
            importance=0.90,
            tags=["document", "knowledge"],
            metadata={"document_id": getattr(document, "document_id", ""), "title": title},
        )
        stored_memories.append(main_mem)

        # Ingest chunks if present
        chunks = getattr(document, "chunks", [])
        for chk in chunks[:5]:
            chk_mem = await self.store_memory(
                content=f"Document Section ({title}): {getattr(chk, 'text', '')}",
                memory_type=MemoryType.KNOWLEDGE,
                source="document_chunk",
                importance=0.85,
                tags=["document_chunk"],
                metadata={"chunk_id": getattr(chk, "chunk_id", ""), "document_id": getattr(document, "document_id", "")},
            )
            await self.link_memories(main_mem.memory_id, chk_mem.memory_id, relationship_type="contains_chunk")
            stored_memories.append(chk_mem)

        return stored_memories

    async def ingest_search_result(self, search_result: Any) -> List[MemoryItem]:
        """Ingest a NormalizedSearchResult object from Phase 5 Search & Knowledge Platform."""
        stored_memories = []
        results = getattr(search_result, "results", [])
        q_raw = getattr(getattr(search_result, "query", None), "raw_query", "search")

        for item in results[:5]:
            m = await self.store_memory(
                content=f"Search Result '{getattr(item, 'title', '')}': {getattr(item, 'snippet', '')}",
                memory_type=MemoryType.KNOWLEDGE,
                source="search",
                importance=0.80,
                tags=["search_result"],
                metadata={"url": getattr(item, "url", ""), "provider": getattr(item, "source_provider", ""), "query": q_raw},
            )
            stored_memories.append(m)

        return stored_memories
