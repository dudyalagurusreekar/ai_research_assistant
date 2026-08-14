"""Execution Policy configuration model for ARA v2.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ExecutionPolicy:
    """Policy rules governing parallel execution, caching, retries, and fallbacks."""

    max_parallel_workers: int = 4
    enable_caching: bool = True
    default_ttl_seconds: float = 3600.0
    enable_fallbacks: bool = True
    max_retries_per_tool: int = 2
    circuit_breaker_threshold: int = 3
    cost_budget_per_plan: float = 0.50
    latency_budget_seconds: float = 120.0
    weight_capability: float = 0.4
    weight_reliability: float = 0.3
    weight_latency: float = 0.2
    weight_cost: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        """Serialize policy configuration."""
        return {
            "max_parallel_workers": self.max_parallel_workers,
            "enable_caching": self.enable_caching,
            "default_ttl_seconds": self.default_ttl_seconds,
            "enable_fallbacks": self.enable_fallbacks,
            "max_retries_per_tool": self.max_retries_per_tool,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "cost_budget_per_plan": self.cost_budget_per_plan,
            "latency_budget_seconds": self.latency_budget_seconds,
        }
