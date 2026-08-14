"""Workflow Context models — Shared state container for autonomous research execution."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.workflow.models.citation import CitationRecord
from core.workflow.models.conflict import ConflictReport
from core.workflow.models.evidence import EvidenceRecord
from core.workflow.models.goal import ResearchGoal
from core.workflow.models.metrics import WorkflowMetrics
from core.workflow.models.question import ResearchQuestion
from core.workflow.models.report import ResearchReport


class WorkflowStage(Enum):
    """Pipeline stages through which an autonomous research workflow progresses."""

    INITIALIZED = "initialized"
    GOAL_ANALYZED = "goal_analyzed"
    QUESTIONS_GENERATED = "questions_generated"
    WORKFLOW_GENERATED = "workflow_generated"
    MULTI_AGENT_EXECUTING = "multi_agent_executing"
    EVIDENCE_AGGREGATED = "evidence_aggregated"
    CONFLICTS_ANALYZED = "conflicts_analyzed"
    CITATIONS_MANAGED = "citations_managed"
    REPORT_COMPOSED = "report_composed"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(Enum):
    """Overall status of an autonomous research workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REPLANNING = "replanning"


@dataclass
class ResearchWorkflowContext:
    """Shared state container flowing through the Autonomous Research Workflow Engine."""

    session_id: str = field(default_factory=lambda: f"rwf_{uuid.uuid4().hex[:8]}")
    goal: Optional[ResearchGoal] = None
    stage: WorkflowStage = WorkflowStage.INITIALIZED
    status: WorkflowStatus = WorkflowStatus.PENDING
    questions: List[ResearchQuestion] = field(default_factory=list)
    evidence: List[EvidenceRecord] = field(default_factory=list)
    conflicts: List[ConflictReport] = field(default_factory=list)
    citations: List[CitationRecord] = field(default_factory=list)
    report: Optional[ResearchReport] = None
    metrics: WorkflowMetrics = field(default_factory=lambda: WorkflowMetrics(session_id=""))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.metrics.session_id:
            self.metrics.session_id = self.session_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "stage": self.stage.value,
            "status": self.status.value,
            "goal": self.goal.to_dict() if self.goal else None,
            "questions_count": len(self.questions),
            "evidence_count": len(self.evidence),
            "conflicts_count": len(self.conflicts),
            "citations_count": len(self.citations),
            "report_generated": self.report is not None,
            "metrics": self.metrics.to_dict(),
        }
