"""Decision Option and Feasibility Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class OptionStatus(str, Enum):
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    CONDITIONAL = "conditional"


@dataclass
class ResourceRequirement:
    """Resource requirement for implementing an option."""

    resource_type: str = ""  # e.g., "Engineering Hours", "Cloud Budget", "Hardware"
    quantity: float = 0.0
    unit: str = ""
    is_critical: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": self.resource_type,
            "quantity": self.quantity,
            "unit": self.unit,
            "is_critical": self.is_critical,
        }


@dataclass
class FeasibilityAssessment:
    """Details constraint checking results for an option."""

    is_feasible: bool = True
    status: OptionStatus = OptionStatus.FEASIBLE
    hard_constraints_passed: List[str] = field(default_factory=list)
    hard_constraints_failed: List[str] = field(default_factory=list)
    soft_constraint_violations: List[str] = field(default_factory=list)
    violation_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_feasible": self.is_feasible,
            "status": self.status.value,
            "hard_constraints_passed": self.hard_constraints_passed,
            "hard_constraints_failed": self.hard_constraints_failed,
            "soft_constraint_violations": self.soft_constraint_violations,
            "violation_notes": self.violation_notes,
        }


@dataclass
class Option:
    """Represents a candidate decision option/alternative."""

    option_id: str = field(default_factory=lambda: f"opt_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    category: str = "general"
    status: OptionStatus = OptionStatus.FEASIBLE
    feasibility: FeasibilityAssessment = field(default_factory=FeasibilityAssessment)
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    implementation_complexity: str = "medium"  # low, medium, high, extreme
    time_to_value_days: int = 30
    resource_requirements: List[ResourceRequirement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "status": self.status.value,
            "feasibility": self.feasibility.to_dict(),
            "pros": self.pros,
            "cons": self.cons,
            "estimated_cost": self.estimated_cost,
            "implementation_complexity": self.implementation_complexity,
            "time_to_value_days": self.time_to_value_days,
            "resource_requirements": [r.to_dict() for r in self.resource_requirements],
            "metadata": self.metadata,
        }
