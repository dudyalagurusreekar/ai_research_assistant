"""Risk Factor and Risk Assessment Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskCategory(str, Enum):
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    VENDOR_LOCKIN = "vendor_lockin"
    SCALABILITY = "scalability"


@dataclass
class RiskFactor:
    """Represents a specific risk factor associated with an option."""

    risk_id: str = field(default_factory=lambda: f"risk_{uuid.uuid4().hex[:8]}")
    option_id: str = ""
    title: str = ""
    description: str = ""
    category: RiskCategory = RiskCategory.TECHNICAL
    probability: float = 0.3  # 0.0 (impossible) to 1.0 (certain)
    impact: float = 3.0  # 1.0 (negligible) to 5.0 (catastrophic)
    severity_score: float = 0.9  # probability * impact (range 0.0 to 5.0)
    mitigation_strategy: str = ""
    residual_risk_score: float = 0.3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "option_id": self.option_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "probability": self.probability,
            "impact": self.impact,
            "severity_score": self.severity_score,
            "mitigation_strategy": self.mitigation_strategy,
            "residual_risk_score": self.residual_risk_score,
        }


@dataclass
class RiskProfile:
    """Aggregated risk assessment profile for an option."""

    option_id: str = ""
    overall_risk_score: float = 0.0  # Aggregate risk index (0.0 low to 5.0 high)
    risk_level: str = "low"  # low, medium, high, critical
    risk_factors: List[RiskFactor] = field(default_factory=list)
    primary_risk_category: RiskCategory = RiskCategory.TECHNICAL
    single_points_of_failure: List[str] = field(default_factory=list)
    mitigation_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "overall_risk_score": self.overall_risk_score,
            "risk_level": self.risk_level,
            "risk_factors": [rf.to_dict() for rf in self.risk_factors],
            "primary_risk_category": self.primary_risk_category.value,
            "single_points_of_failure": self.single_points_of_failure,
            "mitigation_summary": self.mitigation_summary,
        }
