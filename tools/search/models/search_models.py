"""Data models for Search & Knowledge Platform."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now, utc_isoformat


class QueryIntent(str, Enum):
    """Search query intent categorization."""
    GENERAL_WEB = "general_web"
    ACADEMIC = "academic"
    CODE_GITHUB = "code_github"
    LOCAL_DOCUMENT = "local_document"
    HYBRID = "hybrid"


@dataclass
class SearchQuery:
    """Standardized search query request model."""
    raw_query: str
    normalized_query: str = ""
    intent: QueryIntent = QueryIntent.GENERAL_WEB
    target_providers: List[str] = field(default_factory=list)
    domain_filters: List[str] = field(default_factory=list)
    file_type_filters: List[str] = field(default_factory=list)
    max_results: int = 10
    timeout_seconds: float = 15.0
    enable_cache: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)
    query_id: str = field(default_factory=lambda: generate_id("qry_"))


@dataclass
class SearchRankScore:
    """Granular ranking score breakdown."""
    relevance_score: float = 0.0
    freshness_score: float = 0.0
    authority_score: float = 0.0
    confidence_score: float = 0.0
    final_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relevance_score": self.relevance_score,
            "freshness_score": self.freshness_score,
            "authority_score": self.authority_score,
            "confidence_score": self.confidence_score,
            "final_score": self.final_score,
        }


@dataclass
class SearchResultItem:
    """Individual normalized search result item."""
    result_id: str = field(default_factory=lambda: generate_id("sitem_"))
    title: str = ""
    url: str = ""
    snippet: str = ""
    source_provider: str = ""
    mime_type: str = "text/html"
    published_date: Optional[str] = None
    author_or_owner: Optional[str] = None
    score: SearchRankScore = field(default_factory=SearchRankScore)
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source_provider": self.source_provider,
            "mime_type": self.mime_type,
            "published_date": self.published_date,
            "author_or_owner": self.author_or_owner,
            "score": self.score.to_dict(),
            "metadata": self.metadata,
        }


@dataclass
class SearchMetrics:
    """Telemetry metrics for a search execution."""
    total_execution_time_ms: float = 0.0
    provider_latencies_ms: Dict[str, float] = field(default_factory=dict)
    total_raw_results: int = 0
    total_deduplicated_results: int = 0
    cached_hit: bool = False
    providers_attempted: List[str] = field(default_factory=list)
    providers_failed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_execution_time_ms": self.total_execution_time_ms,
            "provider_latencies_ms": self.provider_latencies_ms,
            "total_raw_results": self.total_raw_results,
            "total_deduplicated_results": self.total_deduplicated_results,
            "cached_hit": self.cached_hit,
            "providers_attempted": self.providers_attempted,
            "providers_failed": self.providers_failed,
        }


@dataclass
class NormalizedSearchResult:
    """Unified container for normalized multi-provider search results."""
    query: SearchQuery
    results: List[SearchResultItem] = field(default_factory=list)
    metrics: SearchMetrics = field(default_factory=SearchMetrics)
    search_id: str = field(default_factory=lambda: generate_id("srch_"))
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "search_id": self.search_id,
            "query": {
                "raw_query": self.query.raw_query,
                "normalized_query": self.query.normalized_query,
                "intent": self.query.intent.value,
            },
            "results": [r.to_dict() for r in self.results],
            "metrics": self.metrics.to_dict(),
            "created_at": self.created_at,
        }


@dataclass
class KnowledgeIndexEntry:
    """Indexed local knowledge item metadata."""
    entry_id: str = field(default_factory=lambda: generate_id("kie_"))
    document_id: str = ""
    title: str = ""
    source_url_or_path: str = ""
    mime_type: str = ""
    summary: str = ""
    keywords: List[str] = field(default_factory=list)
    indexed_at: str = field(default_factory=utc_isoformat)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "document_id": self.document_id,
            "title": self.title,
            "source_url_or_path": self.source_url_or_path,
            "mime_type": self.mime_type,
            "summary": self.summary,
            "keywords": self.keywords,
            "indexed_at": self.indexed_at,
            "metadata": self.metadata,
        }
