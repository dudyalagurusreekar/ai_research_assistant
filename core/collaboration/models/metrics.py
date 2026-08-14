"""Metrics models — Collaboration, Orchestration, and Agent Performance Metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentMetrics:
    """Per-agent execution performance metrics."""

    agent_id: str
    tasks_assigned: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_latency_ms: float = 0.0
    average_confidence_score: float = 0.0
    conflicts_involved: int = 0
    tokens_used: int = 0

    @property
    def success_rate(self) -> float:
        if self.tasks_assigned == 0:
            return 1.0
        return self.tasks_completed / self.tasks_assigned

    @property
    def avg_latency_ms(self) -> float:
        if self.tasks_completed == 0:
            return 0.0
        return self.total_execution_latency_ms / self.tasks_completed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "tasks_assigned": self.tasks_assigned,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "average_confidence_score": self.average_confidence_score,
            "conflicts_involved": self.conflicts_involved,
            "tokens_used": self.tokens_used,
        }


@dataclass
class OrchestratorMetrics:
    """Aggregated orchestration metrics for a multi-agent collaboration session."""

    session_id: str
    total_latency_ms: float = 0.0
    sequential_estimated_latency_ms: float = 0.0
    parallel_speedup_ratio: float = 1.0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    retried_tasks: int = 0
    agents_used: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    agent_metrics: Dict[str, AgentMetrics] = field(default_factory=dict)

    def calculate_speedup(self) -> float:
        if self.total_latency_ms > 0 and self.sequential_estimated_latency_ms > 0:
            self.parallel_speedup_ratio = round(
                self.sequential_estimated_latency_ms / self.total_latency_ms, 2
            )
        else:
            self.parallel_speedup_ratio = 1.0
        return self.parallel_speedup_ratio

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "total_latency_ms": self.total_latency_ms,
            "sequential_estimated_latency_ms": self.sequential_estimated_latency_ms,
            "parallel_speedup_ratio": self.calculate_speedup(),
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "retried_tasks": self.retried_tasks,
            "agents_used": self.agents_used,
            "conflicts_detected": self.conflicts_detected,
            "conflicts_resolved": self.conflicts_resolved,
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": self.total_cost_usd,
            "agent_metrics": {k: v.to_dict() for k, v in self.agent_metrics.items()},
        }
