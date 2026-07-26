"""Objective Model tracking user goals, constraints, priority, and progress."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, unique
from typing import Any, Dict, List, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now


@unique
class Priority(Enum):
    """Priority level for an objective."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@unique
class ObjectiveStatus(Enum):
    """Lifecycle status of an objective."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Constraint:
    """Represents an execution boundary or rule associated with an objective."""

    name: str
    description: str
    is_hard_constraint: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectiveProgress:
    """Tracks completion percentage and milestone outcomes for an objective."""

    total_milestones: int = 0
    completed_milestones: int = 0
    percentage: float = 0.0
    milestone_details: Dict[str, str] = field(default_factory=dict)

    def update_progress(self, completed: int, total: int, details: Optional[Dict[str, str]] = None) -> None:
        """Update progress metrics."""
        self.completed_milestones = completed
        self.total_milestones = total
        self.percentage = (completed / max(1, total)) * 100.0
        if details:
            self.milestone_details.update(details)


@dataclass
class Objective:
    """Represents a structured user goal with constraints, priority, and progress metrics."""

    goal: str
    objective_id: str = field(default_factory=lambda: generate_id("obj_"))
    priority: Priority = Priority.MEDIUM
    status: ObjectiveStatus = ObjectiveStatus.NOT_STARTED
    constraints: List[Constraint] = field(default_factory=list)
    progress: ObjectiveProgress = field(default_factory=ObjectiveProgress)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_constraint(self, name: str, description: str, is_hard: bool = True) -> None:
        """Add a constraint boundary to the objective."""
        self.constraints.append(Constraint(name=name, description=description, is_hard_constraint=is_hard))
        self.updated_at = utc_now()

    def update_status(self, new_status: ObjectiveStatus) -> None:
        """Update completion status."""
        self.status = new_status
        self.updated_at = utc_now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize objective model to dictionary representation."""
        return {
            "objective_id": self.objective_id,
            "goal": self.goal,
            "priority": self.priority.value,
            "status": self.status.value,
            "constraints": [
                {"name": c.name, "description": c.description, "is_hard": c.is_hard_constraint}
                for c in self.constraints
            ],
            "progress": {
                "percentage": round(self.progress.percentage, 2),
                "completed": self.progress.completed_milestones,
                "total": self.progress.total_milestones,
                "details": self.progress.milestone_details,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
