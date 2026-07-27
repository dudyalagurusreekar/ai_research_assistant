"""Unified SearchToolFacade for the Search & Knowledge Platform."""

import json
import asyncio
from typing import Dict, List, Any, Optional

from core.interfaces.tool import ITool
from core.models.tool_result import ToolResult
from core.events import AsyncEventBus
from tools.search.models.search_models import (
    SearchQuery,
    NormalizedSearchResult,
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
from infrastructure.logging.logger import StructuredLogger


from core.models.metadata import ToolMetadata


class SearchToolFacade(ITool):
    """Public unified API facade for the Search & Knowledge Platform."""

    name = "search_tool"
    description = "Unified Search and Knowledge Platform Tool for multi-provider knowledge discovery."

    def __init__(
        self,
        provider_registry: Optional[SearchProviderRegistry] = None,
        query_planner: Optional[QueryPlanner] = None,
        search_executor: Optional[SearchExecutor] = None,
        result_normalizer: Optional[ResultNormalizer] = None,
        ranking_engine: Optional[RankingEngine] = None,
        content_fetcher: Optional[ContentFetcher] = None,
        search_cache: Optional[SearchCache] = None,
        knowledge_index: Optional[KnowledgeIndex] = None,
        event_bus: Optional[AsyncEventBus] = None,
        browser_facade: Optional[Any] = None,
        document_facade: Optional[Any] = None,
    ) -> None:
        self.name = "search_tool"
        self._logger = StructuredLogger("SearchToolFacade")
        self._event_bus = event_bus or AsyncEventBus()
        self._knowledge_index = knowledge_index or KnowledgeIndex()

        self._metadata = ToolMetadata(
            name="search_tool",
            version="1.0.0",
            description="Unified Search and Knowledge Platform Tool for multi-provider knowledge discovery.",
            capabilities=["search", "academic_search", "code_search", "knowledge_discovery"],
            parameters_schema={
                "action": "Action to perform ('search', 'fetch', 'local_search')",
                "query": "Search query string",
                "url": "URL or document path to fetch",
            },
            tags=["search", "knowledge", "multi-provider"],
            is_async=True,
            enabled=True,
        )

        # Strategy Registry
        self._registry = provider_registry or SearchProviderRegistry()
        if not self._registry.list_providers():
            self._registry.register(WebSearchProvider())
            self._registry.register(AcademicSearchProvider())
            self._registry.register(GitHubSearchProvider())
            self._registry.register(LocalDocumentSearchProvider(knowledge_index=self._knowledge_index))

        # Core Components
        self._planner = query_planner or QueryPlanner()
        self._executor = search_executor or SearchExecutor()
        self._normalizer = result_normalizer or ResultNormalizer()
        self._ranking_engine = ranking_engine or RankingEngine()
        self._content_fetcher = content_fetcher or ContentFetcher(
            browser_facade=browser_facade,
            document_facade=document_facade,
        )
        self._cache = search_cache or SearchCache()

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata descriptor."""
        return self._metadata

    async def forward(self, action: str = "search", **kwargs) -> str:
        """Standard tool execution wrapper returning JSON string."""
        try:
            if action in ["search", "query"]:
                q_text = kwargs.get("query", kwargs.get("q", ""))
                res = await self.search(q_text, **kwargs)
                return json.dumps(res.to_dict(), indent=2)
            elif action == "fetch":
                url = kwargs.get("url", kwargs.get("path", ""))
                res_fetch = await self.fetch_and_ingest(url, **kwargs)
                return json.dumps(res_fetch, indent=2)
            elif action == "local_search":
                q_text = kwargs.get("query", "")
                entries = await self.search_local_knowledge(q_text, top_k=kwargs.get("top_k", 10))
                return json.dumps([e.to_dict() for e in entries], indent=2)
            else:
                return json.dumps({"error": f"Unknown action '{action}'"}, indent=2)
        except Exception as e:
            self._logger.error(f"Error in SearchToolFacade.forward action '{action}': {e}")
            return json.dumps({"error": str(e)}, indent=2)

    async def execute(self, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Execute method returning ToolResult object conforming to ITool interface."""
        params = dict(parameters or {})
        params.update(kwargs)
        action = params.get("action", "search")
        try:
            output_json = await self.forward(action=action, **params)
            data = json.loads(output_json)
            if isinstance(data, dict) and "error" in data:
                return ToolResult.error(error_message=data["error"])
            return ToolResult.success(data=data)
        except Exception as e:
            return ToolResult.error(error_message=str(e))

    async def search(self, raw_query: str, **options) -> NormalizedSearchResult:
        """Perform unified multi-provider search query."""
        if not raw_query or not raw_query.strip():
            raise ValueError("Search query string cannot be empty.")

        # 1. Plan query
        query_plan = await self._planner.plan_query(raw_query, options)
        await self._publish_event("search.started", {"query": raw_query, "intent": query_plan.intent.value})

        # 2. Check cache
        cached_res = await self._cache.get(query_plan)
        if cached_res:
            await self._publish_event("search.completed", {"query": raw_query, "cached": True})
            return cached_res

        # 3. Resolve target providers
        providers = []
        for p_name in query_plan.target_providers:
            provider_inst = self._registry.get_provider(p_name)
            if provider_inst:
                providers.append(provider_inst)

        if not providers:
            # Fallback to all registered providers
            providers = self._registry.list_providers()

        # 4. Execute search across providers
        try:
            raw_search_res = await self._executor.execute_search(query_plan, providers)
            
            # 5. Normalize items
            normalized_items = self._normalizer.normalize(raw_search_res.results)
            await self._publish_event("result.normalized", {"raw_count": len(raw_search_res.results), "normalized_count": len(normalized_items)})

            # 6. Rank and deduplicate results
            final_items = await self._ranking_engine.rank_and_deduplicate(query_plan, normalized_items)

            raw_search_res.results = final_items
            raw_search_res.metrics.total_deduplicated_results = len(final_items)

            # 7. Store in cache
            await self._cache.set(query_plan, raw_search_res)

            await self._publish_event("search.completed", {
                "query": raw_query,
                "results_count": len(final_items),
                "execution_time_ms": raw_search_res.metrics.total_execution_time_ms,
            })
            return raw_search_res
        except Exception as e:
            await self._publish_event("search.failed", {"query": raw_query, "error": str(e)})
            self._logger.error(f"Search execution failed for query '{raw_query}': {e}")
            raise

    async def multi_search(self, raw_queries: List[str], **options) -> List[NormalizedSearchResult]:
        """Perform concurrent multi-query searches."""
        tasks = [self.search(q, **options) for q in raw_queries]
        return await asyncio.gather(*tasks)

    async def fetch_and_ingest(self, url_or_path: str, **options) -> Dict[str, Any]:
        """Fetch web page or parse file into document platform."""
        res = await self._content_fetcher.fetch_and_ingest(url_or_path, options)
        await self._publish_event("content.fetched", {"source": url_or_path, "type": res.get("content_type")})
        
        # Optionally index into local knowledge index if document parsed
        if res.get("content_type") == "document" and "document_id" in res:
            entry = KnowledgeIndexEntry(
                document_id=res["document_id"],
                title=res.get("title", ""),
                source_url_or_path=url_or_path,
                mime_type=res.get("metadata", {}).get("mime_type", ""),
                summary=res.get("full_text", "")[:300],
            )
            await self._knowledge_index.index_entry(entry)

        return res

    async def search_local_knowledge(self, query: str, top_k: int = 10) -> List[KnowledgeIndexEntry]:
        """Query local knowledge index."""
        return await self._knowledge_index.search_index(query, top_k=top_k)

    async def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish domain event over AsyncEventBus."""
        if self._event_bus:
            try:
                from core.models.event import Event
                event_obj = Event(
                    event_type=event_type,
                    source="SearchToolFacade",
                    payload=payload,
                )
                await self._event_bus.publish(event_obj)
            except Exception as e:
                self._logger.warning(f"Error publishing event '{event_type}': {e}")
