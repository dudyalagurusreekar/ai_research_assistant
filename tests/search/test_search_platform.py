"""Comprehensive Unit, Integration, Concurrency, and End-to-End Tests for Phase 5 Search & Knowledge Platform."""

import asyncio
import os
import tempfile
import pytest

from tools.search.facade.facade import SearchToolFacade
from tools.search.models.search_models import (
    SearchQuery,
    SearchResultItem,
    SearchRankScore,
    QueryIntent,
    KnowledgeIndexEntry,
)
from tools.search.registry.provider_registry import SearchProviderRegistry
from tools.search.planner.query_planner import QueryPlanner
from tools.search.executor.search_executor import SearchExecutor
from tools.search.normalizer.result_normalizer import ResultNormalizer
from tools.search.ranking.ranking_engine import RankingEngine
from tools.search.fetcher.content_fetcher import ContentFetcher
from tools.search.cache.search_cache import SearchCache
from tools.search.index.knowledge_index import KnowledgeIndex
from tools.search.providers.web_provider import WebSearchProvider
from tools.search.providers.academic_provider import AcademicSearchProvider
from tools.search.providers.github_provider import GitHubSearchProvider
from tools.search.providers.local_provider import LocalDocumentSearchProvider
from tools.search.tool import SearchTool
from core.events import AsyncEventBus


def test_provider_registry():
    """Verify registration and resolution of search providers."""
    registry = SearchProviderRegistry()
    web_p = WebSearchProvider()
    acad_p = AcademicSearchProvider()
    
    registry.register(web_p)
    registry.register(acad_p)

    assert registry.get_provider("web_search") == web_p
    assert registry.get_provider("academic_search") == acad_p
    assert len(registry.list_providers()) == 2

    academic_matches = registry.get_providers_for_intent("academic")
    assert len(academic_matches) >= 1


def test_query_planner():
    """Verify query planning, filter extraction, and intent detection."""
    async def _test():
        planner = QueryPlanner()
        
        # General query
        plan1 = await planner.plan_query("machine learning advances")
        assert plan1.intent == QueryIntent.GENERAL_WEB
        assert "web_search" in plan1.target_providers

        # Academic query with filters
        plan2 = await planner.plan_query("quantum computing arxiv paper filetype:pdf site:arxiv.org")
        assert plan2.intent == QueryIntent.ACADEMIC
        assert "pdf" in plan2.file_type_filters
        assert "arxiv.org" in plan2.domain_filters
        assert "academic_search" in plan2.target_providers

        # Code query
        plan3 = await planner.plan_query("python repository github code for transformer")
        assert plan3.intent == QueryIntent.CODE_GITHUB
        assert "github_search" in plan3.target_providers

    asyncio.run(_test())


def test_search_executor():
    """Verify parallel provider execution and latency tracking."""
    async def _test():
        executor = SearchExecutor()
        planner = QueryPlanner()
        plan = await planner.plan_query("neural networks")
        
        providers = [WebSearchProvider(), AcademicSearchProvider(), GitHubSearchProvider()]
        result = await executor.execute_search(plan, providers)
        
        assert len(result.results) > 0
        assert result.metrics.total_raw_results == len(result.results)
        assert len(result.metrics.providers_attempted) == 3
        assert result.metrics.total_execution_time_ms > 0

    asyncio.run(_test())


def test_ranking_engine_deduplication_and_scoring():
    """Verify relevance scoring, authority weighting, and deduplication."""
    async def _test():
        ranking = RankingEngine()
        query = SearchQuery(raw_query="artificial intelligence arxiv paper", normalized_query="artificial intelligence arxiv paper")
        
        item1 = SearchResultItem(
            title="Artificial Intelligence Paper",
            url="https://arxiv.org/abs/2607.0001",
            snippet="Comprehensive AI paper on deep models",
        )
        item2 = SearchResultItem(
            title="Artificial Intelligence Paper",
            url="https://arxiv.org/abs/2607.0001/",  # Duplicate canonical URL
            snippet="Duplicate content",
        )
        item3 = SearchResultItem(
            title="Random Unrelated Page",
            url="https://example.org/blog/random",
            snippet="Cooking recipes and gardening tips",
        )

        ranked = await ranking.rank_and_deduplicate(query, [item1, item2, item3])
        assert len(ranked) == 2  # Deduplicated item2
        assert ranked[0].url.startswith("https://arxiv.org")  # Higher authority & relevance
        assert ranked[0].score.final_score > ranked[1].score.final_score

    asyncio.run(_test())


def test_knowledge_index():
    """Verify local knowledge index storage and term search."""
    async def _test():
        index = KnowledgeIndex()
        entry1 = KnowledgeIndexEntry(
            title="Quantum Mechanics Fundamentals",
            summary="Introductory principles of quantum physics and wave functions",
            keywords=["quantum", "physics"],
        )
        entry2 = KnowledgeIndexEntry(
            title="Deep Learning Frameworks",
            summary="Neural network architectures and GPU acceleration",
            keywords=["deep learning", "ai"],
        )

        await index.index_entry(entry1)
        await index.index_entry(entry2)

        results = await index.search_index("quantum physics")
        assert len(results) >= 1
        assert results[0].entry_id == entry1.entry_id

    asyncio.run(_test())


def test_search_cache():
    """Verify query caching."""
    async def _test():
        cache = SearchCache()
        query = SearchQuery(raw_query="caching test query", normalized_query="caching test query")
        
        assert await cache.get(query) is None

        from tools.search.models.search_models import NormalizedSearchResult
        res = NormalizedSearchResult(query=query)
        await cache.set(query, res)

        cached_hit = await cache.get(query)
        assert cached_hit is not None
        assert cached_hit.metrics.cached_hit is True

    asyncio.run(_test())


def test_content_fetcher_document_handoff():
    """Verify content fetcher document handoff to DocumentToolFacade."""
    async def _test():
        class MockDocFacade:
            async def parse_document(self, path):
                from tools.document.models.document import NormalizedDocument, DocumentMetadata
                return NormalizedDocument(
                    document_id="doc_mock_123",
                    full_text="Parsed mock doc content",
                    metadata=DocumentMetadata(title="Parsed PDF Test"),
                )

        fetcher = ContentFetcher(document_facade=MockDocFacade())
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 mock pdf content")
            fpath = f.name

        try:
            res = await fetcher.fetch_and_ingest(fpath)
            assert res["content_type"] == "document"
            assert res["document_id"] == "doc_mock_123"
            assert "Parsed mock doc content" in res["full_text"]
        finally:
            if os.path.exists(fpath):
                os.remove(fpath)

    asyncio.run(_test())


def test_search_facade_end_to_end_and_events():
    """Verify full SearchToolFacade multi-provider execution and AsyncEventBus notifications."""
    async def _test():
        bus = AsyncEventBus()
        events_fired = []

        async def _on_event(evt):
            events_fired.append(evt.event_type)

        bus.subscribe("search.started", _on_event)
        bus.subscribe("result.normalized", _on_event)
        bus.subscribe("search.completed", _on_event)

        facade = SearchToolFacade(event_bus=bus)
        
        # Test unified search API
        res = await facade.search("machine learning arxiv paper filetype:pdf")
        assert len(res.results) > 0
        assert res.query.raw_query == "machine learning arxiv paper filetype:pdf"
        assert res.metrics.total_deduplicated_results == len(res.results)

        # Wait briefly for async events
        await asyncio.sleep(0.05)
        assert "search.started" in events_fired
        assert "result.normalized" in events_fired
        assert "search.completed" in events_fired

        # Test forward JSON method
        json_output = await facade.forward(action="search", query="neural networks")
        assert "search_id" in json_output
        assert "results" in json_output

        # Test multi-search API
        multi_res = await facade.multi_search(["query 1", "query 2"])
        assert len(multi_res) == 2

    asyncio.run(_test())


def test_smolagents_search_tool_wrapper():
    """Verify smolagents SearchTool wrapper."""
    tool = SearchTool()
    res_str = tool.forward(action="search", query="quantum physics")
    assert "search_id" in res_str
    assert "results" in res_str
