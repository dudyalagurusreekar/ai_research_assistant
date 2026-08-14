"""LLM Provider Descriptor model for ARA v2.0 LLM Orchestration Layer.

Enriches model metadata with provider type, tier classification, context window sizes,
token pricing, dynamic reliability tracking (0.0 to 1.0), and assigned fallback chains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ProviderType(Enum):
    """Categorization of LLM hosting infrastructure."""

    LOCAL = "local"                 # Ollama, vLLM, Local Runtime
    CLOUD_GEMINI = "cloud_gemini"   # Google Gemini API
    CLOUD_OPENAI = "cloud_openai"   # OpenAI API
    CLOUD_ANTHROPIC = "cloud_anthropic" # Anthropic Claude API
    CLOUD_DEEPSEEK = "cloud_deepseek"  # DeepSeek API


class ModelTier(Enum):
    """Model performance and complexity classification tier."""

    ROUTINE = "routine"      # Simple planning, summarization, basic QA (Local/Small)
    BALANCED = "balanced"    # Standard research, code generation (Flash/Mini)
    ADVANCED = "advanced"    # Multi-step reasoning, complex document analysis (Pro/Sonnet)
    REASONING = "reasoning"  # High-depth reasoning, mathematical/logic tasks (Opus/o3)


class ProviderHealthStatus(Enum):
    """Operational health state of an LLM provider endpoint."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CIRCUIT_OPEN = "circuit_open"
    UNAVAILABLE = "unavailable"


@dataclass
class LLMProviderDescriptor:
    """Descriptor model defining operational specs and metrics for an LLM endpoint."""

    model_id: str = ""
    name: str = ""
    provider_type: ProviderType = ProviderType.CLOUD_GEMINI
    tier: ModelTier = ModelTier.BALANCED
    description: str = ""

    # Capabilities & Limits
    capabilities: List[str] = field(default_factory=list)
    supported_task_types: List[str] = field(default_factory=list)
    context_window: int = 128000
    max_tokens: int = 4096

    # Pricing per 1K Tokens ($)
    input_cost_per_1k: float = 0.0001
    output_cost_per_1k: float = 0.0004

    # Performance & Latency
    estimated_latency_ms: float = 1000.0
    avg_actual_latency_ms: float = 1000.0
    rate_limit_rpm: int = 60

    # Dynamic Reliability Tracking (0.0 = failing, 1.0 = flawless)
    reliability_score: float = 0.98
    health_status: ProviderHealthStatus = ProviderHealthStatus.HEALTHY
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_processed: int = 0
    total_cost_accumulated: float = 0.0

    # Assigned Fallback Model IDs
    fallback_models: List[str] = field(default_factory=list)

    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None

    def is_available(self) -> bool:
        """Return True if provider endpoint is available for routing."""
        return self.health_status in (ProviderHealthStatus.HEALTHY, ProviderHealthStatus.DEGRADED)

    def record_success(self, latency_ms: float, tokens: int, cost: float) -> None:
        """Update metrics and reliability score on successful completion."""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_tokens_processed += tokens
        self.total_cost_accumulated += cost
        self.consecutive_failures = 0
        self.last_success_at = datetime.now(timezone.utc)

        # Exponential moving average for latency
        self.avg_actual_latency_ms = (0.8 * self.avg_actual_latency_ms) + (0.2 * latency_ms)

        # Boost reliability score slightly
        self.reliability_score = min(1.0, self.reliability_score + 0.02)

        # Restore health if degraded
        if self.health_status == ProviderHealthStatus.DEGRADED:
            self.health_status = ProviderHealthStatus.HEALTHY

    def record_failure(self, error_message: str = "") -> None:
        """Update metrics and trigger health degradation on error (e.g. 429/500)."""
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_failure_at = datetime.now(timezone.utc)

        # Penalize reliability score
        penalty = 0.15 * self.consecutive_failures
        self.reliability_score = max(0.0, self.reliability_score - penalty)

        # Degrade health status based on failure count
        if self.consecutive_failures >= 3:
            self.health_status = ProviderHealthStatus.CIRCUIT_OPEN
        elif self.consecutive_failures >= 1:
            self.health_status = ProviderHealthStatus.DEGRADED

    def reset_circuit_breaker(self) -> None:
        """Reset consecutive failures and restore health status."""
        self.consecutive_failures = 0
        self.health_status = ProviderHealthStatus.HEALTHY
        self.reliability_score = max(self.reliability_score, 0.90)

    def compute_routing_score(
        self,
        target_tier: ModelTier,
        complexity_score: int = 5,
        weight_tier: float = 0.4,
        weight_reliability: float = 0.3,
        weight_cost: float = 0.15,
        weight_latency: float = 0.15,
    ) -> float:
        """Calculate composite utility score for routing candidate selection."""
        if not self.is_available():
            return 0.0

        # Tier match bonus
        tier_match = 1.0 if self.tier == target_tier else (0.7 if abs(self._tier_rank(self.tier) - self._tier_rank(target_tier)) == 1 else 0.4)

        # Local preference for low complexity tasks
        local_bonus = 0.15 if (self.provider_type == ProviderType.LOCAL and complexity_score <= 3) else 0.0

        # Latency & Cost normalizations
        norm_latency = max(0.0, 1.0 - (self.avg_actual_latency_ms / 10000.0))
        norm_cost = max(0.0, 1.0 - ((self.input_cost_per_1k + self.output_cost_per_1k) / 0.05))

        score = (
            (weight_tier * tier_match) +
            (weight_reliability * self.reliability_score) +
            (weight_cost * norm_cost) +
            (weight_latency * norm_latency) +
            local_bonus
        )
        return max(0.0, score)

    @staticmethod
    def _tier_rank(tier: ModelTier) -> int:
        mapping = {ModelTier.ROUTINE: 1, ModelTier.BALANCED: 2, ModelTier.ADVANCED: 3, ModelTier.REASONING: 4}
        return mapping.get(tier, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize descriptor to JSON dict."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "provider_type": self.provider_type.value,
            "tier": self.tier.value,
            "context_window": self.context_window,
            "input_cost_per_1k": self.input_cost_per_1k,
            "output_cost_per_1k": self.output_cost_per_1k,
            "estimated_latency_ms": self.estimated_latency_ms,
            "actual_latency_ms": round(self.avg_actual_latency_ms, 1),
            "reliability_score": round(self.reliability_score, 3),
            "health_status": self.health_status.value,
            "consecutive_failures": self.consecutive_failures,
            "total_requests": self.total_requests,
            "total_tokens_processed": self.total_tokens_processed,
            "total_cost_accumulated": round(self.total_cost_accumulated, 6),
            "fallback_models": self.fallback_models,
        }
