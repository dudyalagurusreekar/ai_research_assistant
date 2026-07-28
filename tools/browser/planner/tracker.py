"""Objective Tracker Subsystem (`tools/browser/planner/tracker.py`).

Explicitly tracks required task outcomes and milestones (e.g., "definition extracted",
"PDF downloaded", "summary completed"). The planner queries the tracker to determine
whether the task is complete rather than deciding on its own.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("ObjectiveTracker")


class MilestoneStatus(Enum):
    """Status of a tracked task milestone."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    FAILED = "failed"


@dataclass
class Milestone:
    """Represents a specific required outcome for task completion."""

    name: str
    description: str
    status: MilestoneStatus = MilestoneStatus.PENDING
    evidence: Optional[Any] = None
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize milestone to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "evidence": str(self.evidence) if self.evidence else None,
            "required": self.required,
        }


class ObjectiveTracker:
    """Dedicated tracker for required task outcomes and milestones.

    Decouples completion reasoning from the planner: the planner reports evidence
    and queries the tracker to determine if all required outcomes are achieved.
    """

    def __init__(self, objective: str) -> None:
        """Initialize ObjectiveTracker.

        Args:
            objective (str): Overall task objective description.
        """
        self.objective = objective
        self.milestones: Dict[str, Milestone] = {}
        self._logger = logger

    def add_milestone(
        self,
        name: str,
        description: str,
        required: bool = True,
    ) -> Milestone:
        """Register a required outcome milestone.

        Args:
            name (str): Unique milestone identifier.
            description (str): Human-readable outcome description.
            required (bool): Whether milestone is mandatory for completion.

        Returns:
            Milestone: Created milestone instance.
        """
        milestone = Milestone(
            name=name,
            description=description,
            status=MilestoneStatus.PENDING,
            required=required,
        )
        self.milestones[name] = milestone
        return milestone

    def mark_achieved(self, name: str, evidence: Optional[Any] = None) -> bool:
        """Mark a milestone as achieved with supporting evidence.

        Args:
            name (str): Name of the milestone.
            evidence (Optional[Any]): Verification evidence (e.g., extracted text, file path).

        Returns:
            bool: True if milestone found and marked achieved.
        """
        milestone = self.milestones.get(name)
        if not milestone:
            self._logger.warning(f"Attempted to mark unknown milestone: {name}")
            return False

        milestone.status = MilestoneStatus.ACHIEVED
        milestone.evidence = evidence
        self._logger.info(f"Milestone achieved: '{name}' (Evidence: {evidence})")
        return True

    def mark_failed(self, name: str, reason: str) -> bool:
        """Mark a milestone as failed."""
        milestone = self.milestones.get(name)
        if not milestone:
            return False
        milestone.status = MilestoneStatus.FAILED
        milestone.evidence = reason
        return True

    def is_complete(self) -> bool:
        """Check whether all mandatory milestones have been achieved.

        Returns:
            bool: True if every required milestone is ACHIEVED.
        """
        if not self.milestones:
            return False

        for milestone in self.milestones.values():
            if milestone.required and milestone.status != MilestoneStatus.ACHIEVED:
                return False
        return True

    def get_pending_milestones(self) -> List[Milestone]:
        """Return a list of all milestones that are not yet achieved."""
        return [
            m for m in self.milestones.values()
            if m.status in (MilestoneStatus.PENDING, MilestoneStatus.IN_PROGRESS)
        ]

    def get_status_summary(self) -> str:
        """Return a compact human-readable progress summary."""
        if not self.milestones:
            return "No milestones registered."
        completed = sum(1 for m in self.milestones.values() if m.status == MilestoneStatus.ACHIEVED)
        total = len(self.milestones)
        return f"Objective Progress: {completed}/{total} milestones achieved."
