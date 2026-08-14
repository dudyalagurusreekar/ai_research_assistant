"""Recommendation and Human Decision Boundary Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.confidence import ConfidenceAssessment
from core.decision_intelligence.models.evidence import EvidenceItem
from core.decision_intelligence.models.option import Option
from core.decision_intelligence.models.risk import RiskProfile
from core.decision_intelligence.models.scenario import ScenarioSimulationResult
from core.decision_intelligence.models.tradeoff import TradeOffMatrix


class RecommendationType(str, Enum):
    PRIMARY_RECOMMENDATION = "primary_recommendation"
    STRONG_ALTERNATIVE = "strong_alternative"
    CONTINGENCY_OPTION = "contingency_option"
    NOT_RECOMMENDED = "not_recommended"


@dataclass
class HumanChoiceBoundary:
    """Defines explicit boundaries where human judgment must override automated models."""

    boundary_id: str = field(default_factory=lambda: f"hcb_{uuid.uuid4().hex[:8]}")
    category: str = ""  # e.g., "Ethics", "Policy", "Organizational Strategy", "Budget Approval"
    description: str = ""
    tradeoff_condition: str = ""
    human_action_required: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "category": self.category,
            "description": self.description,
            "tradeoff_condition": self.tradeoff_condition,
            "human_action_required": self.human_action_required,
        }


@dataclass
class RecommendationItem:
    """Detailed recommendation item for an evaluated option."""

    recommendation_id: str = field(default_factory=lambda: f"rec_{uuid.uuid4().hex[:8]}")
    option_id: str = ""
    option_title: str = ""
    recommendation_type: RecommendationType = RecommendationType.PRIMARY_RECOMMENDATION
    rank: int = 1
    executive_summary: str = ""
    detailed_rationale: str = ""
    key_tradeoffs: List[str] = field(default_factory=list)
    primary_risks: List[str] = field(default_factory=list)
    mitigation_plan: str = ""
    supporting_evidence_count: int = 0
    traceability_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "option_id": self.option_id,
            "option_title": self.option_title,
            "recommendation_type": self.recommendation_type.value,
            "rank": self.rank,
            "executive_summary": self.executive_summary,
            "detailed_rationale": self.detailed_rationale,
            "key_tradeoffs": self.key_tradeoffs,
            "primary_risks": self.primary_risks,
            "mitigation_plan": self.mitigation_plan,
            "supporting_evidence_count": self.supporting_evidence_count,
            "traceability_sources": self.traceability_sources,
        }


@dataclass
class DecisionRecommendationReport:
    """Final comprehensive Decision Intelligence & Recommendation Report."""

    report_id: str = field(default_factory=lambda: f"dec_report_{uuid.uuid4().hex[:8]}")
    decision_id: str = ""
    topic: str = ""
    user_query: str = ""
    top_recommendation: Optional[RecommendationItem] = None
    all_recommendations: List[RecommendationItem] = field(default_factory=list)
    tradeoff_matrix: Optional[TradeOffMatrix] = None
    risk_profiles: Dict[str, RiskProfile] = field(default_factory=dict)
    simulation_results: Dict[str, ScenarioSimulationResult] = field(default_factory=dict)
    confidence_assessments: Dict[str, ConfidenceAssessment] = field(default_factory=dict)
    human_choice_boundaries: List[HumanChoiceBoundary] = field(default_factory=list)
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "decision_id": self.decision_id,
            "topic": self.topic,
            "user_query": self.user_query,
            "top_recommendation": self.top_recommendation.to_dict() if self.top_recommendation else None,
            "all_recommendations": [rec.to_dict() for rec in self.all_recommendations],
            "tradeoff_matrix": self.tradeoff_matrix.to_dict() if self.tradeoff_matrix else None,
            "risk_profiles": {k: v.to_dict() for k, v in self.risk_profiles.items()},
            "simulation_results": {k: v.to_dict() for k, v in self.simulation_results.items()},
            "confidence_assessments": {k: v.to_dict() for k, v in self.confidence_assessments.items()},
            "human_choice_boundaries": [hcb.to_dict() for hcb in self.human_choice_boundaries],
            "evidence_items": [evi.to_dict() for evi in self.evidence_items],
            "created_at": self.created_at.isoformat(),
        }
