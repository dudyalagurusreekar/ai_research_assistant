"""Evaluation Task Result and Execution Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from evaluation.models.task import TaskCategory


@dataclass
class MetricScore:
    """Individual metric evaluation score."""

    metric_name: str = ""  # e.g., "planning_score", "citation_accuracy"
    raw_score: float = 0.0  # Normalized to 0.0 .. 1.0 or scale
    weight: float = 1.0
    passed: bool = True
    target_threshold: float = 0.0
    justification: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "raw_score": self.raw_score,
            "weight": self.weight,
            "passed": self.passed,
            "target_threshold": self.target_threshold,
            "justification": self.justification,
        }


@dataclass
class TaskResult:
    """Result of executing a single benchmark task."""

    result_id: str = field(default_factory=lambda: f"res_{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    task_name: str = ""
    category: TaskCategory = TaskCategory.RESEARCH
    status: str = "passed"  # passed, failed, error, skipped
    overall_quality_score: float = 1.0  # 0.0 to 1.0
    execution_time_ms: float = 0.0
    latency_score: float = 1.0
    token_usage: int = 0
    cost_usd: float = 0.0
    memory_mb: float = 0.0
    metrics: Dict[str, MetricScore] = field(default_factory=dict)
    actual_output: Optional[Any] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "category": self.category.value,
            "status": self.status,
            "overall_quality_score": self.overall_quality_score,
            "execution_time_ms": self.execution_time_ms,
            "latency_score": self.latency_score,
            "token_usage": self.token_usage,
            "cost_usd": self.cost_usd,
            "memory_mb": self.memory_mb,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CategorySummary:
    """Aggregated summary of results for a single category."""

    category: TaskCategory = TaskCategory.RESEARCH
    total_tasks: int = 0
    passed_tasks: int = 0
    failed_tasks: int = 0
    pass_rate: float = 100.0  # 0.0 to 100.0
    avg_quality_score: float = 1.0
    avg_latency_ms: float = 0.0
    metrics_avg: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "total_tasks": self.total_tasks,
            "passed_tasks": self.passed_tasks,
            "failed_tasks": self.failed_tasks,
            "pass_rate": self.pass_rate,
            "avg_quality_score": self.avg_quality_score,
            "avg_latency_ms": self.avg_latency_ms,
            "metrics_avg": self.metrics_avg,
        }
