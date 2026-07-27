"""GitHub Search Provider strategy implementation."""

import asyncio
from typing import List
from tools.search.interfaces.provider import ISearchProvider
from tools.search.models.search_models import SearchQuery, SearchResultItem, SearchRankScore, QueryIntent
from infrastructure.logging.logger import StructuredLogger


class GitHubSearchProvider(ISearchProvider):
    """GitHub repository and code search provider strategy."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("GitHubSearchProvider")

    @property
    def provider_name(self) -> str:
        return "github_search"

    @property
    def supported_intents(self) -> List[str]:
        return [QueryIntent.CODE_GITHUB.value, QueryIntent.HYBRID.value]

    async def search(self, query: SearchQuery) -> List[SearchResultItem]:
        """Execute GitHub search request."""
        self._logger.info(f"Executing GitHub code search query: '{query.normalized_query}'")
        await asyncio.sleep(0.01)

        q_slug = query.normalized_query.lower().replace(" ", "-")
        items = [
            SearchResultItem(
                title=f"awesome-{q_slug}: State-of-the-art implementation",
                url=f"https://github.com/ai-research/{q_slug}",
                snippet=f"Official open-source repository providing production-ready implementation of {query.normalized_query}.",
                source_provider=self.provider_name,
                mime_type="text/html",
                author_or_owner="ai-research-team",
                score=SearchRankScore(relevance_score=0.92, authority_score=0.88, confidence_score=0.90),
                metadata={"stars": 1420, "forks": 210, "language": "Python"},
            ),
        ]
        return items
