"""Web Search Provider strategy implementation."""

import time
import asyncio
from typing import List
from tools.search.interfaces.provider import ISearchProvider
from tools.search.models.search_models import SearchQuery, SearchResultItem, SearchRankScore, QueryIntent
from infrastructure.logging.logger import StructuredLogger


class WebSearchProvider(ISearchProvider):
    """Web search provider strategy supporting general web search requests."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("WebSearchProvider")

    @property
    def provider_name(self) -> str:
        return "web_search"

    @property
    def supported_intents(self) -> List[str]:
        return [QueryIntent.GENERAL_WEB.value, QueryIntent.HYBRID.value, QueryIntent.ACADEMIC.value, QueryIntent.CODE_GITHUB.value]

    async def search(self, query: SearchQuery) -> List[SearchResultItem]:
        """Execute web search request and return normalized items."""
        self._logger.info(f"Executing web search query: '{query.normalized_query}'")
        
        # Simulate quick async network execution
        await asyncio.sleep(0.01)

        raw_q = query.normalized_query.lower()
        items = [
            SearchResultItem(
                title=f"Comprehensive Overview: {query.normalized_query}",
                url=f"https://example.org/search?q={query.normalized_query.replace(' ', '+')}",
                snippet=f"Latest updates, news, and technical documentation regarding {query.normalized_query}.",
                source_provider=self.provider_name,
                mime_type="text/html",
                score=SearchRankScore(relevance_score=0.9, authority_score=0.8, confidence_score=0.85),
            ),
            SearchResultItem(
                title=f"Reference Documentation on {query.normalized_query}",
                url=f"https://docs.example.com/ref/{query.normalized_query.replace(' ', '_')}",
                snippet=f"Detailed reference guides, standard implementations, and specifications for {query.normalized_query}.",
                source_provider=self.provider_name,
                mime_type="text/html",
                score=SearchRankScore(relevance_score=0.85, authority_score=0.9, confidence_score=0.88),
            ),
        ]
        return items
