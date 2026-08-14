"""Evaluation Report, Dashboard, and Leaderboard Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from evaluation.models.gate import ReleaseGateVerdict
from evaluation.models.result import CategorySummary, TaskResult


@dataclass
class DashboardMetrics:
    """Snapshot metrics formatted for the interactive HTML/JSON Dashboard."""

    total_tasks_run: int = 0
    passed_tasks_count: int = 0
    failed_tasks_count: int = 0
    overall_pass_rate: float = 100.0
    overall_quality_score: float = 1.0
    avg_latency_ms: float = 0.0
    category_scores: Dict[str, float] = field(default_factory=dict)
    key_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks_run": self.total_tasks_run,
            "passed_tasks_count": self.passed_tasks_count,
            "failed_tasks_count": self.failed_tasks_count,
            "overall_pass_rate": self.overall_pass_rate,
            "overall_quality_score": self.overall_quality_score,
            "avg_latency_ms": self.avg_latency_ms,
            "category_scores": self.category_scores,
            "key_metrics": self.key_metrics,
        }


@dataclass
class LeaderboardEntry:
    """Historical version entry in the evaluation leaderboard."""

    entry_id: str = field(default_factory=lambda: f"lead_{uuid.uuid4().hex[:8]}")
    version: str = "v3.5"
    sprint: str = "Sprint 14"
    run_timestamp: str = ""
    pass_rate: float = 100.0
    quality_score: float = 1.0
    security_pass_rate: float = 100.0
    verdict: str = "APPROVED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "version": self.version,
            "sprint": self.sprint,
            "run_timestamp": self.run_timestamp,
            "pass_rate": self.pass_rate,
            "quality_score": self.quality_score,
            "security_pass_rate": self.security_pass_rate,
            "verdict": self.verdict,
        }


@dataclass
class EvaluationReport:
    """Comprehensive Sprint 14 Evaluation & Quality Assurance Report."""

    report_id: str = field(default_factory=lambda: f"eval_rep_{uuid.uuid4().hex[:8]}")
    version: str = "v3.5"
    sprint: str = "Sprint 14 - Comprehensive Evaluation Platform"
    verdict: Optional[ReleaseGateVerdict] = None
    dashboard_metrics: Optional[DashboardMetrics] = None
    category_summaries: Dict[str, CategorySummary] = field(default_factory=dict)
    task_results: List[TaskResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "version": self.version,
            "sprint": self.sprint,
            "verdict": self.verdict.to_dict() if self.verdict else None,
            "dashboard_metrics": self.dashboard_metrics.to_dict() if self.dashboard_metrics else None,
            "category_summaries": {k: v.to_dict() for k, v in self.category_summaries.items()},
            "task_results": [tr.to_dict() for tr in self.task_results],
            "created_at": self.created_at.isoformat(),
        }
