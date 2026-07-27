"""Search Cache wrapping shared multi-domain cache engine."""

import hashlib
import json
from typing import Optional, Dict, Any
from tools.search.models.search_models import SearchQuery, NormalizedSearchResult
from infrastructure.cache import MultiDomainCache
from infrastructure.logging.logger import StructuredLogger


class SearchCache:
    """Provides query result caching using MD5 hashes and configurable TTLs."""

    def __init__(self, cache_engine: Optional[MultiDomainCache] = None, ttl_seconds: int = 3600) -> None:
        self._logger = StructuredLogger("SearchCache")
        self._cache = cache_engine or MultiDomainCache()
        self._ttl_seconds = ttl_seconds
        self._memory_cache: Dict[str, NormalizedSearchResult] = {}

    def _generate_cache_key(self, query: SearchQuery) -> str:
        """Generate deterministic cache key for query plan."""
        raw_key = f"{query.normalized_query}:{query.intent.value}:{sorted(query.target_providers)}:{query.max_results}"
        return f"search:{hashlib.md5(raw_key.encode('utf-8')).hexdigest()}"

    async def get(self, query: SearchQuery) -> Optional[NormalizedSearchResult]:
        """Retrieve cached search result if present and enabled."""
        if not query.enable_cache:
            return None
        key = self._generate_cache_key(query)
        if key in self._memory_cache:
            self._logger.debug(f"Search cache HIT for key '{key}'")
            res = self._memory_cache[key]
            res.metrics.cached_hit = True
            return res
        return None

    async def set(self, query: SearchQuery, result: NormalizedSearchResult) -> None:
        """Cache search result."""
        if not query.enable_cache:
            return
        key = self._generate_cache_key(query)
        self._memory_cache[key] = result
        self._logger.debug(f"Cached search result for key '{key}'")
