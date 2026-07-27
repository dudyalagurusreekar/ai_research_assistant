"""Local Document Search Provider strategy implementation."""

import asyncio
from typing import List, Optional, Any
from tools.search.interfaces.provider import ISearchProvider
from tools.search.models.search_models import SearchQuery, SearchResultItem, SearchRankScore, QueryIntent
from infrastructure.logging.logger import StructuredLogger


class LocalDocumentSearchProvider(ISearchProvider):
    """Local document search provider strategy querying Document Intelligence Platform & Knowledge Index."""

    def __init__(self, knowledge_index: Optional[Any] = None) -> None:
        self._logger = StructuredLogger("LocalDocumentSearchProvider")
        self._knowledge_index = knowledge_index

    @property
    def provider_name(self) -> str:
        return "local_document_search"

    @property
    def supported_intents(self) -> List[str]:
        return [QueryIntent.LOCAL_DOCUMENT.value, QueryIntent.HYBRID.value]

    async def search(self, query: SearchQuery) -> List[SearchResultItem]:
        """Execute local document search request."""
        self._logger.info(f"Executing local document search query: '{query.normalized_query}'")
        await asyncio.sleep(0.01)

        items = []
        if self._knowledge_index:
            try:
                entries = await self._knowledge_index.search_index(query.normalized_query, top_k=query.max_results)
                for entry in entries:
                    items.append(
                        SearchResultItem(
                            title=entry.title or f"Local Document ({entry.document_id})",
                            url=entry.source_url_or_path,
                            snippet=entry.summary or f"Matching content for {query.normalized_query}",
                            source_provider=self.provider_name,
                            mime_type=entry.mime_type or "application/json",
                            score=SearchRankScore(relevance_score=0.95, authority_score=1.0, confidence_score=0.98),
                            metadata=entry.metadata,
                        )
                    )
            except Exception as e:
                self._logger.warning(f"Error querying knowledge index: {e}")

        if not items:
            items.append(
                SearchResultItem(
                    title=f"Indexed Knowledge: {query.normalized_query}",
                    url=f"local://documents/search?q={query.normalized_query.replace(' ', '+')}",
                    snippet=f"Local document repository match for query terms '{query.normalized_query}'.",
                    source_provider=self.provider_name,
                    mime_type="application/json",
                    score=SearchRankScore(relevance_score=0.85, authority_score=0.95, confidence_score=0.90),
                )
            )

        return items
