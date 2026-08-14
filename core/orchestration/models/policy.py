"""LLM Routing Policy configuration model for ARA v2.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class LLMRoutingPolicy:
    """Policy configuration controlling local vs cloud routing, caching, and failover."""

    prefer_local_for_routine: bool = True
    enable_response_caching: bool = True
    default_ttl_seconds: float = 7200.0
    enable_fallback_chain: bool = True
    max_fallback_attempts: int = 3
    circuit_breaker_threshold: int = 3
    cost_budget_per_request: float = 0.05
    latency_budget_seconds: float = 30.0

    # Model Tier Selection Thresholds (Complexity Score 1 to 10)
    routine_complexity_max: int = 3
    balanced_complexity_max: int = 6
    advanced_complexity_max: int = 8

    # Scoring Weights
    weight_tier: float = 0.4
    weight_reliability: float = 0.3
    weight_cost: float = 0.15
    weight_latency: float = 0.15

    def to_dict(self) -> Dict[str, Any]:
        """Serialize policy dict."""
        return {
            "prefer_local_for_routine": self.prefer_local_for_routine,
            "enable_response_caching": self.enable_response_caching,
            "default_ttl_seconds": self.default_ttl_seconds,
            "enable_fallback_chain": self.enable_fallback_chain,
            "max_fallback_attempts": self.max_fallback_attempts,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "routine_complexity_max": self.routine_complexity_max,
            "balanced_complexity_max": self.balanced_complexity_max,
            "advanced_complexity_max": self.advanced_complexity_max,
        }
