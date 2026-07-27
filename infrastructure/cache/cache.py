"""Multi-Domain Cache implementation supporting TTL expiration."""

import time
from typing import Any, Dict, Optional, Tuple


class CacheEntry:
    """Internal cache container holding data and expiration timestamp."""

    def __init__(self, value: Any, ttl_seconds: float) -> None:
        self.value = value
        self.expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else float("inf")

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() > self.expires_at


class MultiDomainCache:
    """In-memory multi-domain cache for LLM responses, prompts, search, docs, and embeddings."""

    def __init__(self, default_ttl_seconds: float = 300.0) -> None:
        self._domains: Dict[str, Dict[str, CacheEntry]] = {
            "llm": {},
            "prompt": {},
            "search": {},
            "doc": {},
            "embedding": {},
        }
        self.default_ttl = default_ttl_seconds
        self.hits = 0
        self.misses = 0

    def set(self, domain: str, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Store a value in a specific domain cache."""
        if domain not in self._domains:
            self._domains[domain] = {}

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._domains[domain][key] = CacheEntry(value=value, ttl_seconds=ttl)

    def get(self, domain: str, key: str) -> Optional[Any]:
        """Retrieve a value from a specific domain cache. Returns None if missing or expired."""
        if domain not in self._domains or key not in self._domains[domain]:
            self.misses += 1
            return None

        entry = self._domains[domain][key]
        if entry.is_expired():
            del self._domains[domain][key]
            self.misses += 1
            return None

        self.hits += 1
        return entry.value

    def delete(self, domain: str, key: str) -> bool:
        """Delete an entry from a domain cache."""
        if domain in self._domains and key in self._domains[domain]:
            del self._domains[domain][key]
            return True
        return False

    def clear_domain(self, domain: str) -> None:
        """Clear all entries in a specific domain."""
        if domain in self._domains:
            self._domains[domain].clear()

    def get_hit_rate(self) -> float:
        """Return the overall cache hit rate percentage."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100.0
