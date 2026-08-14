"""Models package for Autonomous Research Workflow Engine."""

from core.workflow.models.citation import CitationRecord, CitationStyle
from core.workflow.models.conflict import ConflictReport, ConflictSeverity, ResolutionAction
from core.workflow.models.context import (
    ResearchWorkflowContext,
    WorkflowStage,
    WorkflowStatus,
)
from core.workflow.models.evidence import (
    EvidenceConfidence,
    EvidenceRecord,
    EvidenceSourceType,
)
from core.workflow.models.goal import ConstraintSpec, GoalDomain, GoalPriority, ResearchGoal
from core.workflow.models.metrics import WorkflowMetrics
from core.workflow.models.question import QuestionPriority, QuestionStatus, ResearchQuestion
from core.workflow.models.report import ReportFormat, ReportSection, ResearchReport

__all__ = [
    "ResearchGoal",
    "GoalDomain",
    "GoalPriority",
    "ConstraintSpec",
    "ResearchQuestion",
    "QuestionPriority",
    "QuestionStatus",
    "EvidenceRecord",
    "EvidenceSourceType",
    "EvidenceConfidence",
    "ConflictReport",
    "ConflictSeverity",
    "ResolutionAction",
    "CitationRecord",
    "CitationStyle",
    "ResearchReport",
    "ReportSection",
    "ReportFormat",
    "ResearchWorkflowContext",
    "WorkflowStage",
    "WorkflowStatus",
    "WorkflowMetrics",
]
