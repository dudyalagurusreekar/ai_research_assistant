"""Workflow Metrics models — Autonomous Research Performance Counters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class WorkflowMetrics:
    """Performance recorder for an autonomous research workflow."""

    session_id: str
    total_latency_ms: float = 0.0
    questions_generated: int = 0
    questions_resolved: int = 0
    evidence_records_count: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    citations_generated: int = 0
    tokens_consumed: int = 0
    cost_usd: float = 0.0

    @property
    def resolution_rate(self) -> float:
        if self.questions_generated == 0:
            return 1.0
        return self.questions_resolved / self.questions_generated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "total_latency_ms": self.total_latency_ms,
            "questions_generated": self.questions_generated,
            "questions_resolved": self.questions_resolved,
            "resolution_rate": self.resolution_rate,
            "evidence_records_count": self.evidence_records_count,
            "conflicts_detected": self.conflicts_detected,
            "conflicts_resolved": self.conflicts_resolved,
            "citations_generated": self.citations_generated,
            "tokens_consumed": self.tokens_consumed,
            "cost_usd": self.cost_usd,
        }
