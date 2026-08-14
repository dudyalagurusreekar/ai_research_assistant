"""Tool Capability Descriptor model for ARA v2.0 Adaptive Execution.

Enriches basic tool metadata with performance characteristics, cost models,
dynamic reliability tracking (0.0 to 1.0), health status, and assigned fallback chains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ToolHealthStatus(Enum):
    """Real-time operational status of a tool."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class ToolCapabilityDescriptor:
    """Enriched operational specification for a platform tool capability."""

    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    task_types: List[str] = field(default_factory=list)
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    returns_schema: Dict[str, Any] = field(default_factory=dict)

    # Cost & Performance metrics
    estimated_latency_ms: float = 1000.0
    cost_per_call: float = 0.001
    max_concurrency: int = 5

    # Dynamic Reliability Tracking (0.0 = completely unreliable, 1.0 = flawless)
    reliability_score: float = 0.95
    health_status: ToolHealthStatus = ToolHealthStatus.HEALTHY
    consecutive_failures: int = 0
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_actual_latency_ms: float = 1000.0

    # Fallback configuration
    fallback_tools: List[str] = field(default_factory=list)
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None

    def record_success(self, latency_ms: float) -> None:
        """Update reliability and latency metrics on a successful tool execution."""
        self.total_calls += 1
        self.successful_calls += 1
        self.consecutive_failures = 0
        self.last_success_at = datetime.now(timezone.utc)

        # Exponential moving average for latency
        self.avg_actual_latency_ms = (0.8 * self.avg_actual_latency_ms) + (0.2 * latency_ms)

        # Boost reliability score slightly toward 1.0
        self.reliability_score = min(1.0, self.reliability_score + 0.02)

        # Restore health if previously degraded
        if self.health_status == ToolHealthStatus.DEGRADED:
            self.health_status = ToolHealthStatus.HEALTHY

    def record_failure(self, error_message: str = "") -> None:
        """Update metrics and trigger health degradation on a tool execution failure."""
        self.total_calls += 1
        self.failed_calls += 1
        self.consecutive_failures += 1
        self.last_failure_at = datetime.now(timezone.utc)

        # Penalize reliability score
        penalty = 0.1 * self.consecutive_failures
        self.reliability_score = max(0.0, self.reliability_score - penalty)

        # Update health status based on failure threshold
        if self.consecutive_failures >= 3:
            self.health_status = ToolHealthStatus.UNAVAILABLE
        elif self.consecutive_failures >= 1:
            self.health_status = ToolHealthStatus.DEGRADED

    def is_available(self) -> bool:
        """Return True if tool is operational for selection."""
        return self.health_status != ToolHealthStatus.UNAVAILABLE

    def compute_score(
        self,
        capability_match: float = 1.0,
        weight_capability: float = 0.4,
        weight_reliability: float = 0.3,
        weight_latency: float = 0.2,
        weight_cost: float = 0.1,
    ) -> float:
        """Compute composite selection score (higher is better)."""
        if not self.is_available():
            return 0.0

        # Normalize latency (10,000ms = 0 score)
        norm_latency = max(0.0, 1.0 - (self.avg_actual_latency_ms / 10000.0))
        # Normalize cost ($0.10 = 0 score)
        norm_cost = max(0.0, 1.0 - (self.cost_per_call / 0.10))

        score = (
            (weight_capability * capability_match) +
            (weight_reliability * self.reliability_score) +
            (weight_latency * norm_latency) +
            (weight_cost * norm_cost)
        )
        return max(0.0, score)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize descriptor to JSON-friendly dict."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capabilities": self.capabilities,
            "task_types": self.task_types,
            "estimated_latency_ms": self.estimated_latency_ms,
            "actual_latency_ms": round(self.avg_actual_latency_ms, 1),
            "cost_per_call": self.cost_per_call,
            "reliability_score": round(self.reliability_score, 3),
            "health_status": self.health_status.value,
            "consecutive_failures": self.consecutive_failures,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "fallback_tools": self.fallback_tools,
        }
