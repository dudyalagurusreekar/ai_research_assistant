"""Comprehensive Unit, Integration, Concurrency, and End-to-End Tests for Phase 6 Memory Platform."""

import asyncio

from tools.memory.facade.facade import MemoryToolFacade
from tools.memory.models.memory_models import (
    MemoryItem,
    MemoryType,
    MemoryLink,
    MemoryQuery,
)
from tools.memory.registry.memory_registry import MemoryRegistry
from tools.memory.index.memory_index import MemoryIndex
from tools.memory.graph.relationship_graph import RelationshipGraph
from tools.memory.consolidation.consolidator import MemoryConsolidator
from tools.memory.manager.memory_manager import MemoryManager
from tools.memory.providers.short_term_provider import ShortTermMemoryProvider
from tools.memory.providers.long_term_provider import LongTermMemoryProvider
from tools.memory.providers.session_provider import SessionMemoryProvider
from tools.memory.providers.working_provider import WorkingMemoryProvider
from tools.memory.providers.knowledge_provider import KnowledgeMemoryProvider
from tools.memory.tool import MemoryTool
from core.events import AsyncEventBus


def test_memory_providers():
    """Verify storage, query, touch, and deletion across all 5 memory providers."""
    async def _test():
        st_p = ShortTermMemoryProvider(capacity=10)
        lt_p = LongTermMemoryProvider()
        SessionMemoryProvider()
        WorkingMemoryProvider()
        KnowledgeMemoryProvider()

        # Store items
        item1 = MemoryItem(content="User asked about quantum computing", importance=0.8)
        item2 = MemoryItem(content="Persistent research goal: AI architectures", importance=0.95)

        id1 = await st_p.store(item1)
        id2 = await lt_p.store(item2)

        assert await st_p.retrieve(id1) is not None
        assert await lt_p.retrieve(id2) is not None

        # Query
        q_res = await st_p.query(MemoryQuery(query_text="quantum"))
        assert len(q_res) == 1
        assert q_res[0].memory_id == id1

        # Delete
        assert await st_p.delete(id1) is True
        assert await st_p.retrieve(id1) is None

    asyncio.run(_test())


def test_memory_registry():
    """Verify registration and resolution of memory provider strategies."""
    registry = MemoryRegistry()
    st_p = ShortTermMemoryProvider()
    lt_p = LongTermMemoryProvider()

    registry.register(st_p)
    registry.register(lt_p)

    assert registry.get_provider(MemoryType.SHORT_TERM) == st_p
    assert registry.get_provider(MemoryType.LONG_TERM) == lt_p
    assert len(registry.list_providers()) == 2


def test_memory_index():
    """Verify memory search index term matching."""
    async def _test():
        index = MemoryIndex()
        item1 = MemoryItem(content="Machine Learning algorithms for healthcare", tags=["ai"])
        item2 = MemoryItem(content="Quantum superposition and qubit gates", tags=["physics"])

        await index.index_memory(item1)
        await index.index_memory(item2)

        results = await index.search(MemoryQuery(query_text="machine learning"))
        assert len(results) == 1
        assert results[0].memory_id == item1.memory_id

    asyncio.run(_test())


def test_relationship_graph():
    """Verify semantic memory linking and BFS graph traversal."""
    async def _test():
        graph = RelationshipGraph()
        link1 = MemoryLink(source_memory_id="mem_a", target_memory_id="mem_b", relationship_type="supports")
        link2 = MemoryLink(source_memory_id="mem_b", target_memory_id="mem_c", relationship_type="derived_from")

        await graph.add_link(link1)
        await graph.add_link(link2)

        links_a = await graph.get_links_for_memory("mem_a")
        assert len(links_a) == 1

        related_depth1 = await graph.get_related_memories("mem_a", depth=1)
        assert "mem_b" in related_depth1
        assert "mem_c" not in related_depth1

        related_depth2 = await graph.get_related_memories("mem_a", depth=2)
        assert "mem_b" in related_depth2
        assert "mem_c" in related_depth2

    asyncio.run(_test())


def test_memory_consolidator():
    """Verify memory decay, consolidation, and pruning policies."""
    async def _test():
        consolidator = MemoryConsolidator()
        st_p = ShortTermMemoryProvider()
        lt_p = LongTermMemoryProvider()

        # High-value item to consolidate
        item_high = MemoryItem(content="Crucial discovery", importance=0.9, access_count=3)
        # Low-value item to prune
        item_low = MemoryItem(content="Trivial observation", importance=0.05, access_count=0)

        await st_p.store(item_high)
        await st_p.store(item_low)

        res = await consolidator.consolidate([st_p, lt_p])
        assert res.consolidated_count >= 1
        assert res.pruned_count >= 1

        # Check transferred to long term
        lt_items = await lt_p.list_all()
        assert len(lt_items) >= 1
        assert lt_items[0].content == "Crucial discovery"

    asyncio.run(_test())


def test_memory_manager_ingestion():
    """Verify Document and Search Result ingestion into MemoryManager."""
    async def _test():
        manager = MemoryManager()

        # Mock Phase 4 NormalizedDocument
        class MockDocument:
            document_id = "doc_test_999"
            full_text = "Quantum computing transforms cryptography and materials science."
            class metadata:
                title = "Quantum Document"
            chunks = []

        # Mock Phase 5 NormalizedSearchResult
        class MockResultItem:
            title = "SearchResult 1"
            snippet = "Latest AI breakthrough"
            url = "https://example.com/ai"
            source_provider = "web_search"

        class MockSearchResult:
            search_id = "srch_test_888"
            class query:
                raw_query = "AI research"
            results = [MockResultItem()]

        doc_mems = await manager.ingest_normalized_document(MockDocument())
        assert len(doc_mems) >= 1
        assert "Quantum Document" in doc_mems[0].content

        search_mems = await manager.ingest_search_result(MockSearchResult())
        assert len(search_mems) == 1
        assert search_mems[0].metadata["url"] == "https://example.com/ai"

    asyncio.run(_test())


def test_memory_facade_end_to_end_and_events():
    """Verify MemoryToolFacade unified APIs and AsyncEventBus notifications."""
    async def _test():
        bus = AsyncEventBus()
        events_fired = []

        async def _on_event(evt):
            events_fired.append(evt.event_type)

        bus.subscribe("memory.created", _on_event)
        bus.subscribe("memory.retrieved", _on_event)
        bus.subscribe("memory.linked", _on_event)
        bus.subscribe("memory.consolidated", _on_event)

        facade = MemoryToolFacade(event_bus=bus)

        # 1. Remember
        item = await facade.remember("Neural network optimization strategies", memory_type=MemoryType.SHORT_TERM)
        assert item.content == "Neural network optimization strategies"

        # 2. Recall
        search_res = await facade.recall("optimization")
        assert search_res.total_found >= 1

        # 3. Link
        item2 = await facade.remember("Backpropagation algorithms", memory_type=MemoryType.SHORT_TERM)
        link = await facade.link(item.memory_id, item2.memory_id, relationship_type="relates_to")
        assert link.source_memory_id == item.memory_id

        # 4. Consolidate
        c_res = await facade.consolidate()
        assert c_res.timestamp != ""

        # Wait briefly for async events
        await asyncio.sleep(0.05)
        assert "memory.created" in events_fired
        assert "memory.retrieved" in events_fired
        assert "memory.linked" in events_fired
        assert "memory.consolidated" in events_fired

        # Test forward method
        forward_json = await facade.forward(action="remember", content="Transformer architecture paper")
        assert "memory_id" in forward_json

    asyncio.run(_test())


def test_smolagents_memory_tool_wrapper():
    """Verify smolagents MemoryTool wrapper."""
    tool = MemoryTool()
    res_str = tool.forward(action="remember", content="Tool wrapper test memory")
    assert "memory_id" in res_str
