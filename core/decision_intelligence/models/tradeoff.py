"""Multi-Criteria Trade-off and Pareto Evaluation Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CriterionScore:
    """Evaluation score of a single option against a single objective/criterion."""

    criterion_id: str = ""
    criterion_name: str = ""
    raw_value: Any = 0.0
    normalized_score: float = 0.0  # Normalized to [0.0, 1.0] where 1.0 is best
    weighted_score: float = 0.0  # normalized_score * weight
    justification: str = ""
    supporting_evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "criterion_name": self.criterion_name,
            "raw_value": self.raw_value,
            "normalized_score": self.normalized_score,
            "weighted_score": self.weighted_score,
            "justification": self.justification,
            "supporting_evidence_ids": self.supporting_evidence_ids,
        }


@dataclass
class OptionEvaluation:
    """Complete evaluation score summary for an option across all criteria."""

    option_id: str = ""
    option_title: str = ""
    total_weighted_score: float = 0.0
    criteria_scores: Dict[str, CriterionScore] = field(default_factory=dict)
    rank: int = 1
    is_pareto_optimal: bool = False
    dominates_option_ids: List[str] = field(default_factory=list)
    dominated_by_option_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "option_title": self.option_title,
            "total_weighted_score": self.total_weighted_score,
            "criteria_scores": {k: v.to_dict() for k, v in self.criteria_scores.items()},
            "rank": self.rank,
            "is_pareto_optimal": self.is_pareto_optimal,
            "dominates_option_ids": self.dominates_option_ids,
            "dominated_by_option_ids": self.dominated_by_option_ids,
        }


@dataclass
class TradeOffMatrix:
    """Full multi-criteria decision matrix and Pareto frontier analysis."""

    matrix_id: str = field(default_factory=lambda: f"tom_{uuid.uuid4().hex[:8]}")
    option_evaluations: Dict[str, OptionEvaluation] = field(default_factory=dict)
    criteria_weights: Dict[str, float] = field(default_factory=dict)
    pareto_frontier_option_ids: List[str] = field(default_factory=list)
    tradeoff_summaries: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matrix_id": self.matrix_id,
            "option_evaluations": {k: v.to_dict() for k, v in self.option_evaluations.items()},
            "criteria_weights": self.criteria_weights,
            "pareto_frontier_option_ids": self.pareto_frontier_option_ids,
            "tradeoff_summaries": self.tradeoff_summaries,
        }
