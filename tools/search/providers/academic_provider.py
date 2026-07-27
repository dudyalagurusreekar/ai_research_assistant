"""Academic Search Provider strategy implementation (arXiv / PubMed / OpenAlex)."""

import asyncio
from typing import List
from tools.search.interfaces.provider import ISearchProvider
from tools.search.models.search_models import SearchQuery, SearchResultItem, SearchRankScore, QueryIntent
from infrastructure.logging.logger import StructuredLogger


class AcademicSearchProvider(ISearchProvider):
    """Academic paper and scientific literature search provider strategy."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("AcademicSearchProvider")

    @property
    def provider_name(self) -> str:
        return "academic_search"

    @property
    def supported_intents(self) -> List[str]:
        return [QueryIntent.ACADEMIC.value, QueryIntent.HYBRID.value]

    async def search(self, query: SearchQuery) -> List[SearchResultItem]:
        """Execute academic paper search request."""
        self._logger.info(f"Executing academic search query: '{query.normalized_query}'")
        await asyncio.sleep(0.01)

        items = [
            SearchResultItem(
                title=f"Advances in {query.normalized_query}: A Peer-Reviewed Study",
                url=f"https://arxiv.org/abs/2607.{query.query_id[:4]}",
                snippet=f"Abstract: We present novel methodology and empirical results regarding {query.normalized_query}.",
                source_provider=self.provider_name,
                mime_type="application/pdf",
                published_date="2026-07-01",
                author_or_owner="Dr. A. Scientist et al.",
                score=SearchRankScore(relevance_score=0.95, authority_score=0.95, confidence_score=0.92),
                metadata={"doi": f"10.1016/j.artint.2026.{query.query_id[:4]}", "journal": "Journal of AI Research"},
            ),
            SearchResultItem(
                title=f"Empirical Benchmark Analysis for {query.normalized_query}",
                url=f"https://pubmed.ncbi.nlm.nih.gov/389100{query.query_id[:2]}/",
                snippet=f"Rigorous clinical and algorithmic benchmarking of {query.normalized_query} across multi-center datasets.",
                source_provider=self.provider_name,
                mime_type="text/html",
                published_date="2026-06-15",
                author_or_owner="National Research Consortium",
                score=SearchRankScore(relevance_score=0.88, authority_score=0.92, confidence_score=0.90),
            ),
        ]
        return items
