"""Objective and Constraint Models for Decision Intelligence."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ObjectiveType(str, Enum):
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    COMPLIANCE = "compliance"
    QUALITY = "quality"
    USER_EXPERIENCE = "user_experience"


class ConstraintType(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class ComparisonOperator(str, Enum):
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN_OR_EQUAL = ">="
    EQUAL = "=="
    NOT_EQUAL = "!="
    CONTAINS = "contains"


@dataclass
class Constraint:
    """Represents a hard or soft boundary rule governing viable decision options."""

    constraint_id: str = field(default_factory=lambda: f"const_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    constraint_type: ConstraintType = ConstraintType.HARD
    metric: str = ""
    threshold_value: Any = None
    operator: ComparisonOperator = ComparisonOperator.LESS_THAN_OR_EQUAL
    unit: str = ""
    weight: float = 1.0  # Used for soft constraints penalty/scoring

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "name": self.name,
            "description": self.description,
            "constraint_type": self.constraint_type.value,
            "metric": self.metric,
            "threshold_value": self.threshold_value,
            "operator": self.operator.value,
            "unit": self.unit,
            "weight": self.weight,
        }


@dataclass
class Objective:
    """Represents a target goal against which decision options are scored."""

    objective_id: str = field(default_factory=lambda: f"obj_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    category: ObjectiveType = ObjectiveType.TECHNICAL
    weight: float = 1.0  # Relative importance in MCDA (0.0 to 1.0)
    target_direction: str = "MAXIMIZE"  # MAXIMIZE or MINIMIZE
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "weight": self.weight,
            "target_direction": self.target_direction,
            "unit": self.unit,
        }


@dataclass
class DecisionContext:
    """Captures the full contextual framing for a decision intelligence evaluation."""

    context_id: str = field(default_factory=lambda: f"ctx_{uuid.uuid4().hex[:8]}")
    topic: str = ""
    domain: str = "general"
    user_query: str = ""
    target_audience: str = "stakeholders"
    objectives: List[Objective] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    urgency_level: str = "medium"  # low, medium, high, critical
    risk_tolerance: float = 0.5  # 0.0 (risk averse) to 1.0 (risk seeking)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "topic": self.topic,
            "domain": self.domain,
            "user_query": self.user_query,
            "target_audience": self.target_audience,
            "objectives": [obj.to_dict() for obj in self.objectives],
            "constraints": [const.to_dict() for const in self.constraints],
            "urgency_level": self.urgency_level,
            "risk_tolerance": self.risk_tolerance,
            "created_at": self.created_at.isoformat(),
        }
