"""Abstract interface contracts for Search & Knowledge Platform."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tools.search.models.search_models import (
    SearchQuery,
    SearchResultItem,
    NormalizedSearchResult,
    KnowledgeIndexEntry,
)


class ISearchProvider(ABC):
    """Abstract strategy interface for search providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the search provider."""

    @property
    @abstractmethod
    def supported_intents(self) -> List[str]:
        """List of intent types supported by this provider."""

    @abstractmethod
    async def search(self, query: SearchQuery) -> List[SearchResultItem]:
        """Execute search query and return normalized result items."""


class ISearchProviderRegistry(ABC):
    """Abstract registry interface for search providers."""

    @abstractmethod
    def register(self, provider: ISearchProvider) -> None:
        """Register a search provider."""

    @abstractmethod
    def get_provider(self, name: str) -> Optional[ISearchProvider]:
        """Get provider by name."""

    @abstractmethod
    def list_providers(self) -> List[ISearchProvider]:
        """List all registered providers."""


class IQueryPlanner(ABC):
    """Abstract query analysis and provider selection planner."""

    @abstractmethod
    async def plan_query(self, raw_query: str, options: Optional[Dict[str, Any]] = None) -> SearchQuery:
        """Analyze raw query string and construct an optimized SearchQuery plan."""


class ISearchExecutor(ABC):
    """Abstract search execution manager."""

    @abstractmethod
    async def execute_search(
        self,
        query: SearchQuery,
        providers: List[ISearchProvider],
    ) -> NormalizedSearchResult:
        """Execute parallel search across providers with retries, timeouts, and failover."""


class IRankingEngine(ABC):
    """Abstract ranking, deduplication, and scoring engine."""

    @abstractmethod
    async def rank_and_deduplicate(
        self,
        query: SearchQuery,
        raw_items: List[SearchResultItem],
    ) -> List[SearchResultItem]:
        """Deduplicate, score, and rank search result items."""


class IContentFetcher(ABC):
    """Abstract content fetcher and document routing interface."""

    @abstractmethod
    async def fetch_and_ingest(
        self,
        url_or_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fetch web page or document and route files to Document Tool if necessary."""


class IKnowledgeIndex(ABC):
    """Abstract local knowledge index interface."""

    @abstractmethod
    async def index_entry(self, entry: KnowledgeIndexEntry) -> str:
        """Add entry to knowledge index."""

    @abstractmethod
    async def search_index(self, query: str, top_k: int = 10) -> List[KnowledgeIndexEntry]:
        """Query knowledge index."""
