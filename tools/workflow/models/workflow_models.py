"""Data models for the Research Workflow Engine."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now, utc_isoformat


class TaskStatus(str, Enum):
    """Execution status of a workflow task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowState(str, Enum):
    """Overall execution status of a workflow."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    CHECKPOINTED = "checkpointed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskDependency:
    """Dependency constraint between workflow tasks."""
    parent_task_id: str
    child_task_id: str
    condition: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parent_task_id": self.parent_task_id,
            "child_task_id": self.child_task_id,
            "condition": self.condition,
        }


@dataclass
class WorkflowTask:
    """Individual executable unit of work in a research workflow."""
    task_id: str = field(default_factory=lambda: generate_id("wftask_"))
    title: str = ""
    description: str = ""
    tool_name: str = ""  # e.g., 'search_tool', 'document_tool', 'code_tool'
    action: str = ""     # e.g., 'search', 'parse', 'analyze'
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)  # list of parent task_ids
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "tool_name": self.tool_name,
            "action": self.action,
            "parameters": self.parameters,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class WorkflowCheckpoint:
    """Saved execution snapshot for workflow pause/resume recovery."""
    checkpoint_id: str = field(default_factory=lambda: generate_id("chk_"))
    workflow_id: str = ""
    completed_task_ids: List[str] = field(default_factory=list)
    state_context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "workflow_id": self.workflow_id,
            "completed_task_ids": self.completed_task_ids,
            "state_context": self.state_context,
            "timestamp": self.timestamp,
        }


@dataclass
class WorkflowMetrics:
    """Telemetry metrics for workflow execution."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_duration_ms: float = 0.0
    progress_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_duration_ms": self.total_duration_ms,
            "progress_percentage": self.progress_percentage,
        }


@dataclass
class NormalizedWorkflow:
    """Unified container model representing a multi-step research workflow."""
    workflow_id: str = field(default_factory=lambda: generate_id("wf_"))
    objective: str = ""
    state: WorkflowState = WorkflowState.IDLE
    tasks: List[WorkflowTask] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metrics: WorkflowMetrics = field(default_factory=WorkflowMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "objective": self.objective,
            "state": self.state.value,
            "tasks": [t.to_dict() for t in self.tasks],
            "context": self.context,
            "metrics": self.metrics.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
