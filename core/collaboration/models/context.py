"""Collaboration Context models — Shared state container and task delegation objects."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.collaboration.models.agent_info import AgentRole
from core.collaboration.models.conflict import ConflictRecord
from core.collaboration.models.message import AgentMessage
from core.collaboration.models.metrics import OrchestratorMetrics


class CollaborationStatus(Enum):
    """Overall status of a multi-agent collaboration session."""

    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REPLANNING = "replanning"
    CONFLICT_RESOLVING = "conflict_resolving"


class ExecutionMode(Enum):
    """Execution dispatch mode for sub-tasks."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


@dataclass
class TaskAssignment:
    """Delegated unit of work assigned to a specialized agent."""

    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    target_role: AgentRole = AgentRole.RESEARCH
    required_capabilities: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    input_keys: List[str] = field(default_factory=list)
    output_keys: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # task_ids
    assigned_agent_id: Optional[str] = None
    status: str = "pending"  # pending, assigned, running, completed, failed, skipped
    timeout_seconds: float = 60.0
    estimated_latency_seconds: float = 1.0
    parallel_wave: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "target_role": self.target_role.value,
            "required_capabilities": self.required_capabilities,
            "assigned_agent_id": self.assigned_agent_id,
            "status": self.status,
            "parallel_wave": self.parallel_wave,
        }


@dataclass
class AgentOutput:
    """Result payload produced by an agent execution task."""

    task_id: str
    agent_id: str
    status: str  # completed, failed, error
    result: Any = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 1.0
    execution_latency_ms: float = 0.0
    error_message: Optional[str] = None
    messages_sent: List[AgentMessage] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "confidence_score": self.confidence_score,
            "execution_latency_ms": self.execution_latency_ms,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }


@dataclass
class CollaborationContext:
    """Shared state container flowing through the multi-agent collaboration framework."""

    session_id: str = field(default_factory=lambda: f"collab_{uuid.uuid4().hex[:8]}")
    query: str = ""
    intent: str = "multi_step_research"
    status: CollaborationStatus = CollaborationStatus.INITIALIZED
    execution_mode: ExecutionMode = ExecutionMode.HYBRID
    task_assignments: List[TaskAssignment] = field(default_factory=list)
    task_outputs: Dict[str, AgentOutput] = field(default_factory=dict)
    conflicts: List[ConflictRecord] = field(default_factory=list)
    metrics: OrchestratorMetrics = field(default_factory=lambda: OrchestratorMetrics(session_id=""))
    shared_workspace_id: str = field(default_factory=lambda: f"ws_{uuid.uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.metrics.session_id:
            self.metrics.session_id = self.session_id

    def get_assignment(self, task_id: str) -> Optional[TaskAssignment]:
        for assignment in self.task_assignments:
            if assignment.task_id == task_id:
                return assignment
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "query": self.query,
            "intent": self.intent,
            "status": self.status.value,
            "execution_mode": self.execution_mode.value,
            "tasks_count": len(self.task_assignments),
            "completed_outputs": len(self.task_outputs),
            "conflicts_count": len(self.conflicts),
            "metrics": self.metrics.to_dict(),
        }
