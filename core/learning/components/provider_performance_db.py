"""ProviderPerformanceDatabase for tracking LLM provider reliability, cost, and rate-limit trends."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from utils.logger import get_logger
from core.learning.models.context import ProviderPerformanceMetrics

logger = get_logger("ProviderPerformanceDB")


class ProviderPerformanceDatabase:
    """Tracks historical performance metrics per LLM provider endpoint."""

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), ".storage", "experience")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.storage_dir / "provider_performance.json"
        self._metrics: Dict[str, ProviderPerformanceMetrics] = {}
        self.load()

    def load(self) -> None:
        """Loads provider metrics from disk."""
        if not self.db_file.exists():
            self._metrics = {}
            return

        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for pid, m_data in data.items():
                    self._metrics[pid] = ProviderPerformanceMetrics(
                        provider_id=m_data.get("provider_id", pid),
                        total_requests=m_data.get("total_requests", 0),
                        successful_requests=m_data.get("successful_requests", 0),
                        failed_requests=m_data.get("failed_requests", 0),
                        rate_limit_count=m_data.get("rate_limit_count", 0),
                        total_tokens=m_data.get("total_tokens", 0),
                        total_cost_usd=m_data.get("total_cost_usd", 0.0),
                        avg_latency_ms=m_data.get("avg_latency_ms", 0.0),
                        reliability_score=m_data.get("reliability_score", 1.0),
                        last_updated=m_data.get("last_updated", ""),
                    )
            logger.info(f"Loaded provider performance metrics for {len(self._metrics)} providers")
        except Exception as e:
            logger.error(f"Failed to load provider performance metrics: {e}")
            self._metrics = {}

    def save(self) -> None:
        """Saves provider metrics to disk."""
        try:
            data = {
                pid: {
                    "provider_id": m.provider_id,
                    "total_requests": m.total_requests,
                    "successful_requests": m.successful_requests,
                    "failed_requests": m.failed_requests,
                    "rate_limit_count": m.rate_limit_count,
                    "total_tokens": m.total_tokens,
                    "total_cost_usd": m.total_cost_usd,
                    "avg_latency_ms": m.avg_latency_ms,
                    "reliability_score": m.reliability_score,
                    "last_updated": m.last_updated,
                }
                for pid, m in self._metrics.items()
            }
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save provider performance metrics: {e}")

    def record_request(
        self,
        provider_id: str,
        success: bool,
        latency_ms: float,
        tokens: int = 0,
        cost_usd: float = 0.0,
        is_rate_limit: bool = False,
    ) -> ProviderPerformanceMetrics:
        """Records an LLM request completion and updates provider metrics."""
        if provider_id not in self._metrics:
            self._metrics[provider_id] = ProviderPerformanceMetrics(provider_id=provider_id)

        m = self._metrics[provider_id]
        m.update(success, latency_ms, tokens, cost_usd, is_rate_limit)
        self.save()
        return m

    def get_provider_metrics(self, provider_id: str) -> ProviderPerformanceMetrics:
        """Retrieves metrics for a provider ID."""
        if provider_id not in self._metrics:
            self._metrics[provider_id] = ProviderPerformanceMetrics(provider_id=provider_id)
        return self._metrics[provider_id]

    def rank_providers(self, candidate_providers: List[str]) -> List[str]:
        """Ranks candidate provider IDs by reliability, cost, and latency."""
        def score(pid: str):
            m = self.get_provider_metrics(pid)
            # High reliability score, penalized by rate limits and latency
            rate_limit_penalty = min(m.rate_limit_count * 0.1, 0.5)
            latency_penalty = min(m.avg_latency_ms / 5000.0, 0.3) if m.avg_latency_ms > 0 else 0.0
            return m.reliability_score - rate_limit_penalty - latency_penalty

        return sorted(candidate_providers, key=score, reverse=True)

    def clear(self) -> None:
        self._metrics.clear()
        if self.db_file.exists():
            try:
                os.remove(self.db_file)
            except Exception as e:
                logger.error(f"Failed to remove provider performance db file: {e}")
