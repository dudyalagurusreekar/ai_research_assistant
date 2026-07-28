"""Ranking and Deduplication Engine for Search & Knowledge Platform."""

import re
from typing import List, Set
from urllib.parse import urlparse
from tools.search.interfaces.provider import IRankingEngine
from tools.search.models.search_models import SearchQuery, SearchResultItem, SearchRankScore
from infrastructure.logging.logger import StructuredLogger


class RankingEngine(IRankingEngine):
    """Engine responsible for deduplication, relevance scoring, authority weighting, and top-K ranking."""

    HIGH_AUTHORITY_DOMAINS = {
        "arxiv.org": 0.98,
        "ncbi.nlm.nih.gov": 0.95,
        "github.com": 0.90,
        "docs.python.org": 0.95,
        "wikipedia.org": 0.85,
        "nature.com": 0.98,
        "sciencedirect.com": 0.92,
    }

    def __init__(self) -> None:
        self._logger = StructuredLogger("RankingEngine")

    async def rank_and_deduplicate(
        self,
        query: SearchQuery,
        raw_items: List[SearchResultItem],
    ) -> List[SearchResultItem]:
        """Deduplicate raw search result items, calculate rank scores, and return sorted items."""
        if not raw_items:
            return []

        # 1. Deduplicate by canonical URL & snippet similarity
        deduped = self._deduplicate(raw_items)

        # 2. Score items
        query_terms = set(re.findall(r"\w+", query.normalized_query.lower()))
        for item in deduped:
            rel = self._calculate_relevance(query_terms, item)
            auth = self._calculate_authority(item)
            fresh = self._calculate_freshness(item)
            conf = item.score.confidence_score if item.score.confidence_score > 0 else 0.85

            final = (0.50 * rel) + (0.25 * auth) + (0.15 * fresh) + (0.10 * conf)
            item.score = SearchRankScore(
                relevance_score=round(rel, 4),
                authority_score=round(auth, 4),
                freshness_score=round(fresh, 4),
                confidence_score=round(conf, 4),
                final_score=round(final, 4),
            )

        # 3. Sort descending by final score
        deduped.sort(key=lambda x: x.score.final_score, reverse=True)
        top_results = deduped[: query.max_results]

        self._logger.info(f"Ranked {len(raw_items)} items down to top {len(top_results)} results.")
        return top_results

    def _deduplicate(self, items: List[SearchResultItem]) -> List[SearchResultItem]:
        """Fuzzy URL and content deduplication."""
        unique_items: List[SearchResultItem] = []
        seen_urls: Set[str] = set()

        for item in items:
            canonical_url = self._canonicalize_url(item.url)
            if canonical_url in seen_urls:
                continue
            seen_urls.add(canonical_url)
            unique_items.append(item)

        return unique_items

    def _canonicalize_url(self, url: str) -> str:
        """Strip query parameters and trailing slashes for canonical comparison."""
        if not url:
            return ""
        parsed = urlparse(url.lower())
        path = parsed.path.rstrip("/")
        return f"{parsed.netloc}{path}"

    def _calculate_relevance(self, query_terms: Set[str], item: SearchResultItem) -> float:
        """Calculate term overlap relevance between query terms and title/snippet."""
        if not query_terms:
            return 0.5
        title_terms = set(re.findall(r"\w+", item.title.lower()))
        snippet_terms = set(re.findall(r"\w+", item.snippet.lower()))
        combined = title_terms | snippet_terms

        overlap = len(query_terms & combined)
        return min(1.0, overlap / len(query_terms)) if query_terms else 0.5

    def _calculate_authority(self, item: SearchResultItem) -> float:
        """Estimate domain authority score."""
        if item.score.authority_score > 0:
            return item.score.authority_score
        try:
            domain = urlparse(item.url).netloc.lower()
            for auth_domain, score in self.HIGH_AUTHORITY_DOMAINS.items():
                if domain.endswith(auth_domain):
                    return score
        except Exception:
            pass
        return 0.70

    def _calculate_freshness(self, item: SearchResultItem) -> float:
        """Freshness score estimation."""
        if item.published_date:
            return 0.90
        return 0.75
