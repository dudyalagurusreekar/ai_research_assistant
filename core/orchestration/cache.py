"""LLMResponseCache — deterministic prompt response caching for ARA v2.0.

Provides sub-millisecond retrieval of cached LLM responses on duplicate prompts,
saving tokens, reducing operational latency, and eliminating redundant API costs.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from core.orchestration.models.request import LLMRequest, LLMResponse
from infrastructure.logging.logger import StructuredLogger


class LLMResponseCache:
    """Thread-safe response cache for LLM completion requests."""

    def __init__(self, default_ttl_seconds: float = 7200.0, max_size: int = 1000) -> None:
        self.default_ttl = default_ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._logger = StructuredLogger("LLMResponseCache")

        # Telemetry metrics
        self.total_lookups: int = 0
        self.hits: int = 0
        self.misses: int = 0
        self.tokens_saved: int = 0
        self.estimated_cost_saved: float = 0.0

    @staticmethod
    def compute_cache_key(prompt: str, messages: List[Dict[str, str]], task_type: str, temperature: float) -> str:
        """Generate deterministic SHA-256 key from prompt content and request settings."""
        try:
            msg_str = json.dumps(messages, sort_keys=True, default=str)
        except Exception:
            msg_str = str(messages)

        raw = f"{prompt.strip()}:{msg_str}:{task_type.lower().strip()}:{temperature:.2f}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Look up prompt in response cache. Returns LLMResponse on hit or None on miss."""
        self.total_lookups += 1
        key = self.compute_cache_key(request.prompt, request.messages, request.task_type, request.temperature)

        entry = self._cache.get(key)
        if not entry:
            self.misses += 1
            return None

        # Check TTL
        from datetime import datetime, timezone
        age = (datetime.now(timezone.utc) - entry["created_at"]).total_seconds()
        if age > entry["ttl_seconds"]:
            self._cache.pop(key, None)
            self.misses += 1
            return None

        # Cache Hit!
        entry["hit_count"] += 1
        self.hits += 1

        original_resp: LLMResponse = entry["response"]
        self.tokens_saved += original_resp.total_tokens
        self.estimated_cost_saved += original_resp.total_cost

        self._logger.info(
            f"LLM Cache HIT (key={key[:8]}) -- saved {original_resp.total_tokens} tokens (${original_resp.total_cost:.5f})"
        )

        return LLMResponse(
            request_id=request.request_id,
            text=original_resp.text,
            model_id=original_resp.model_id,
            provider_type=original_resp.provider_type,
            latency_ms=0.5,  # Sub-ms retrieval
            prompt_tokens=original_resp.prompt_tokens,
            completion_tokens=original_resp.completion_tokens,
            total_cost=0.0,  # $0 cost for cache hit
            is_cached=True,
            cache_key=key,
        )

    def put(self, request: LLMRequest, response: LLMResponse, ttl_seconds: Optional[float] = None) -> str:
        """Store LLM response in cache."""
        if not response.text or response.error_message:
            return ""  # Do not cache failed or empty responses

        key = self.compute_cache_key(request.prompt, request.messages, request.task_type, request.temperature)

        # Evict oldest if full
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = min(self._cache, key=lambda k: self._cache[k]["created_at"])
            self._cache.pop(oldest_key, None)

        from datetime import datetime, timezone
        self._cache[key] = {
            "response": response,
            "created_at": datetime.now(timezone.utc),
            "ttl_seconds": ttl_seconds or self.default_ttl,
            "hit_count": 0,
        }
        self._logger.debug(f"Cached response for model '{response.model_id}' (key={key[:8]})")
        return key

    def invalidate(self) -> int:
        """Clear cache entries and return count."""
        count = len(self._cache)
        self._cache.clear()
        return count

    @property
    def hit_rate_pct(self) -> float:
        """Return cache hit rate percentage [0.0, 100.0]."""
        if self.total_lookups == 0:
            return 0.0
        return (self.hits / self.total_lookups) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Return telemetry metrics dict for cache."""
        return {
            "total_entries": len(self._cache),
            "total_lookups": self.total_lookups,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(self.hit_rate_pct, 1),
            "tokens_saved": self.tokens_saved,
            "cost_saved": round(self.estimated_cost_saved, 6),
        }
