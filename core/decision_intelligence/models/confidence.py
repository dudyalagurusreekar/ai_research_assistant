"""Confidence Engine and Uncertainty Quantification Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


@dataclass
class UncertaintyFactor:
    """Identifies a specific source of uncertainty impacting a decision evaluation."""

    factor_id: str = field(default_factory=lambda: f"unc_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    source: str = ""  # e.g., "missing empirical benchmark", "conflicting source data"
    impact_magnitude: float = 0.2  # 0.0 to 1.0 drop in overall confidence
    mitigation_suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "impact_magnitude": self.impact_magnitude,
            "mitigation_suggestion": self.mitigation_suggestion,
        }


@dataclass
class ConfidenceAssessment:
    """Uncertainty quantification assessment for an option."""

    option_id: str = ""
    overall_confidence_score: float = 0.85  # 0.0 to 1.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    evidence_coverage_pct: float = 85.0
    data_source_authority_score: float = 0.90
    uncertainty_factors: List[UncertaintyFactor] = field(default_factory=list)
    confidence_interval: List[float] = field(default_factory=lambda: [0.78, 0.92])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "overall_confidence_score": self.overall_confidence_score,
            "confidence_level": self.confidence_level.value,
            "evidence_coverage_pct": self.evidence_coverage_pct,
            "data_source_authority_score": self.data_source_authority_score,
            "uncertainty_factors": [uf.to_dict() for uf in self.uncertainty_factors],
            "confidence_interval": self.confidence_interval,
        }
