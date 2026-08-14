"""Decision Request Package."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.objective import Constraint, Objective


@dataclass
class DecisionRequest:
    """Input parameters requesting structured decision intelligence analysis."""

    decision_id: str = field(default_factory=lambda: f"dreq_{uuid.uuid4().hex[:8]}")
    user_query: str = ""
    topic: str = ""
    domain: str = "general"
    explicit_objectives: List[Objective] = field(default_factory=list)
    explicit_constraints: List[Constraint] = field(default_factory=list)
    preset_options: List[Dict[str, Any]] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    subsystem_evidence_sources: List[str] = field(default_factory=list)
    risk_tolerance: float = 0.5
    urgency_level: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "user_query": self.user_query,
            "topic": self.topic,
            "domain": self.domain,
            "explicit_objectives": [o.to_dict() for o in self.explicit_objectives],
            "explicit_constraints": [c.to_dict() for c in self.explicit_constraints],
            "preset_options": self.preset_options,
            "context_data": self.context_data,
            "subsystem_evidence_sources": self.subsystem_evidence_sources,
            "risk_tolerance": self.risk_tolerance,
            "urgency_level": self.urgency_level,
        }
