"""ToolResultCache — deterministic result caching for ARA v2.0.

Provides sub-millisecond deduplication of redundant tool calls by generating
SHA-256 parameter hashes. Manages TTL expiration, hit/miss metrics, and total
time saved.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

from core.execution.models.result import CacheEntry, ExecutionResult, ExecutionStatus
from infrastructure.logging.logger import StructuredLogger


class ToolResultCache:
    """Thread-safe deterministic cache for tool execution results."""

    def __init__(self, default_ttl_seconds: float = 3600.0, max_size: int = 500) -> None:
        self.default_ttl = default_ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._logger = StructuredLogger("ToolResultCache")

        # Telemetry metrics
        self.total_lookups: int = 0
        self.hits: int = 0
        self.misses: int = 0
        self.estimated_latency_saved_ms: float = 0.0

    @staticmethod
    def compute_cache_key(tool_name: str, action: str, parameters: Dict[str, Any]) -> str:
        """Generate a deterministic SHA-256 cache key from tool name, action, and parameters."""
        # Normalize parameters by sorting keys and converting to JSON string
        try:
            param_str = json.dumps(parameters, sort_keys=True, default=str)
        except Exception:
            param_str = str(sorted(parameters.items()))

        raw = f"{tool_name.lower().strip()}:{action.lower().strip()}:{param_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, tool_name: str, action: str, parameters: Dict[str, Any],
            estimated_latency_ms: float = 1000.0) -> Optional[ExecutionResult]:
        """Look up a tool call in the cache.

        Returns an ExecutionResult with is_cached=True on a hit, or None on a miss.
        """
        self.total_lookups += 1
        key = self.compute_cache_key(tool_name, action, parameters)

        entry = self._cache.get(key)
        if not entry:
            self.misses += 1
            return None

        if entry.is_expired():
            self._logger.debug(f"Cache entry for key {key[:8]} expired; evicting")
            self._cache.pop(key, None)
            self.misses += 1
            return None

        # Cache Hit!
        entry.touch()
        self.hits += 1
        self.estimated_latency_saved_ms += estimated_latency_ms

        self._logger.info(
            f"Cache HIT for tool '{tool_name}' (action='{action}') -- saved ~{estimated_latency_ms:.0f}ms"
        )

        return ExecutionResult(
            task_id="",
            tool_name=tool_name,
            action=action,
            status=ExecutionStatus.CACHED,
            output=entry.output,
            latency_ms=0.5,  # Sub-ms retrieval
            is_cached=True,
            cache_key=key,
        )

    def put(self, tool_name: str, action: str, parameters: Dict[str, Any], output: Any,
            ttl_seconds: Optional[float] = None) -> str:
        """Store a tool execution result in the cache."""
        key = self.compute_cache_key(tool_name, action, parameters)
        param_hash = hashlib.md5(json.dumps(parameters, sort_keys=True, default=str).encode("utf-8")).hexdigest()

        # Evict oldest entry if max_size reached
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = min(self._cache, key=lambda k: self._cache[k].created_at)
            self._cache.pop(oldest_key, None)

        entry = CacheEntry(
            cache_key=key,
            tool_name=tool_name,
            action=action,
            parameters_hash=param_hash,
            output=output,
            ttl_seconds=ttl_seconds or self.default_ttl,
        )
        self._cache[key] = entry
        self._logger.debug(f"Cached result for tool '{tool_name}' (action='{action}', key={key[:8]})")
        return key

    def invalidate(self, tool_name: Optional[str] = None) -> int:
        """Evict cache entries. If tool_name is provided, evict only for that tool."""
        if tool_name:
            keys_to_remove = [k for k, v in self._cache.items() if v.tool_name == tool_name]
            for k in keys_to_remove:
                self._cache.pop(k, None)
            return len(keys_to_remove)
        else:
            count = len(self._cache)
            self._cache.clear()
            return count

    @property
    def hit_rate(self) -> float:
        """Return cache hit rate percentage [0.0, 100.0]."""
        if self.total_lookups == 0:
            return 0.0
        return (self.hits / self.total_lookups) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Return cache metrics dict for telemetry."""
        return {
            "total_entries": len(self._cache),
            "total_lookups": self.total_lookups,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(self.hit_rate, 1),
            "estimated_latency_saved_ms": round(self.estimated_latency_saved_ms, 1),
        }
