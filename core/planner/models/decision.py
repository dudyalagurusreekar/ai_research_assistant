"""Decision and decision-log models for structured planner auditing.

Every significant planning decision (intent classification, tool selection, DAG
construction, constraint enforcement) is recorded as a PlannerDecision inside a
DecisionLog for full observability and post-hoc analysis.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class PlannerDecision:
    """A single structured decision made during planning."""

    decision_id: str = field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:8]}")
    stage: str = ""
    component: str = ""
    description: str = ""
    rationale: str = ""
    alternatives_considered: List[str] = field(default_factory=list)
    confidence: float = 1.0
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging."""
        return {
            "decision_id": self.decision_id,
            "stage": self.stage,
            "component": self.component,
            "description": self.description,
            "rationale": self.rationale,
            "alternatives_considered": self.alternatives_considered,
            "confidence": self.confidence,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DecisionLog:
    """Ordered collection of PlannerDecision entries for a single planning session."""

    log_id: str = field(default_factory=lambda: f"dlog_{uuid.uuid4().hex[:8]}")
    plan_id: str = ""
    decisions: List[PlannerDecision] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def record(
        self,
        stage: str,
        component: str,
        description: str,
        rationale: str = "",
        confidence: float = 1.0,
        alternatives: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> PlannerDecision:
        """Create and append a new decision entry."""
        decision = PlannerDecision(
            stage=stage,
            component=component,
            description=description,
            rationale=rationale,
            alternatives_considered=alternatives or [],
            confidence=confidence,
            data=data or {},
        )
        self.decisions.append(decision)
        return decision

    def get_by_stage(self, stage: str) -> List[PlannerDecision]:
        """Return all decisions for a given planning stage."""
        return [d for d in self.decisions if d.stage == stage]

    def get_by_component(self, component: str) -> List[PlannerDecision]:
        """Return all decisions from a given component."""
        return [d for d in self.decisions if d.component == component]

    @property
    def count(self) -> int:
        """Total number of recorded decisions."""
        return len(self.decisions)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for persistence."""
        return {
            "log_id": self.log_id,
            "plan_id": self.plan_id,
            "decision_count": self.count,
            "decisions": [d.to_dict() for d in self.decisions],
            "created_at": self.created_at.isoformat(),
        }
