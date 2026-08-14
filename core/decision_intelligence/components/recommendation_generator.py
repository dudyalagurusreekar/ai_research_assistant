"""Recommendation Generator Component — Synthesizes transparent, explainable recommendations with human choice boundaries."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.confidence import ConfidenceAssessment
from core.decision_intelligence.models.evidence import EvidenceItem
from core.decision_intelligence.models.objective import DecisionContext
from core.decision_intelligence.models.option import Option, OptionStatus
from core.decision_intelligence.models.recommendation import (
    DecisionRecommendationReport,
    HumanChoiceBoundary,
    RecommendationItem,
    RecommendationType,
)
from core.decision_intelligence.models.risk import RiskProfile
from core.decision_intelligence.models.scenario import ScenarioSimulationResult
from core.decision_intelligence.models.tradeoff import TradeOffMatrix
from utils.logger import get_logger

logger = get_logger("RecommendationGenerator")


class RecommendationGenerator:
    """Component responsible for synthesizing transparent, explainable, evidence-backed decision support reports."""

    def __init__(self) -> None:
        pass

    def generate_recommendation_report(
        self,
        context: DecisionContext,
        options: List[Option],
        tradeoff_matrix: TradeOffMatrix,
        risk_profiles: Dict[str, RiskProfile],
        simulation_results: Dict[str, ScenarioSimulationResult],
        confidence_assessments: Dict[str, ConfidenceAssessment],
        evidence_items: List[EvidenceItem],
    ) -> DecisionRecommendationReport:
        """Synthesize final structured decision recommendation report."""
        logger.info(f"Synthesizing decision recommendation report for topic: '{context.topic}'")

        # 1. Build RecommendationItems for each option sorted by rank
        sorted_evals = sorted(tradeoff_matrix.option_evaluations.values(), key=lambda x: x.rank)
        recommendations: List[RecommendationItem] = []

        for eval_item in sorted_evals:
            opt = next((o for o in options if o.option_id == eval_item.option_id), None)
            if not opt:
                continue

            r_profile = risk_profiles.get(opt.option_id, RiskProfile())
            c_assess = confidence_assessments.get(opt.option_id, ConfidenceAssessment())
            s_res = simulation_results.get(opt.option_id)

            rec_type = (
                RecommendationType.PRIMARY_RECOMMENDATION
                if eval_item.rank == 1 and opt.status == OptionStatus.FEASIBLE
                else (
                    RecommendationType.STRONG_ALTERNATIVE
                    if eval_item.rank == 2 and opt.status == OptionStatus.FEASIBLE
                    else (
                        RecommendationType.CONTINGENCY_OPTION
                        if opt.status == OptionStatus.CONDITIONAL
                        else RecommendationType.NOT_RECOMMENDED
                    )
                )
            )

            # Key tradeoffs
            tradeoffs = [
                f"Weighted score: {eval_item.total_weighted_score:.3f} across {len(eval_item.criteria_scores)} criteria.",
                f"Pareto status: {'Pareto Optimal (Non-dominated)' if eval_item.is_pareto_optimal else 'Dominated by higher-ranking options'}.",
                f"Cost: ${opt.estimated_cost:,.2f} | Complexity: {opt.implementation_complexity} | Time to value: {opt.time_to_value_days} days.",
            ]

            # Primary risks
            risks = [f"[{rf.category.value.upper()}] {rf.title}: {rf.description}" for rf in r_profile.risk_factors[:3]]

            # Traceability sources
            opt_evidence = [e for e in evidence_items if e.option_id == opt.option_id or not e.option_id]
            sources = list(set(e.source_reference for e in opt_evidence if e.source_reference))

            exec_summary = (
                f"Rank #{eval_item.rank}: '{opt.title}' achieves a overall weighted score of {eval_item.total_weighted_score:.3f} "
                f"with {c_assess.confidence_level.value.upper()} confidence ({c_assess.overall_confidence_score * 100:.0f}%) "
                f"and {r_profile.risk_level.upper()} risk index ({r_profile.overall_risk_score})."
            )

            detailed_rationale = (
                f"Option '{opt.title}' ({opt.category}) offers strong alignment with user objectives. "
                f"Feasibility status is {opt.status.value.upper()}. "
                f"Supported by {len(opt_evidence)} verified evidence items across subsystem sources. "
                f"{r_profile.mitigation_summary}"
            )

            rec_item = RecommendationItem(
                option_id=opt.option_id,
                option_title=opt.title,
                recommendation_type=rec_type,
                rank=eval_item.rank,
                executive_summary=exec_summary,
                detailed_rationale=detailed_rationale,
                key_tradeoffs=tradeoffs,
                primary_risks=risks,
                mitigation_plan=r_profile.mitigation_summary,
                supporting_evidence_count=len(opt_evidence),
                traceability_sources=sources,
            )
            recommendations.append(rec_item)

        top_rec = recommendations[0] if recommendations else None

        # 2. Formulate explicit Human Choice Boundaries
        human_boundaries = self._formulate_human_choice_boundaries(context, options, tradeoff_matrix, risk_profiles)

        report = DecisionRecommendationReport(
            decision_id=context.context_id,
            topic=context.topic,
            user_query=context.user_query,
            top_recommendation=top_rec,
            all_recommendations=recommendations,
            tradeoff_matrix=tradeoff_matrix,
            risk_profiles=risk_profiles,
            simulation_results=simulation_results,
            confidence_assessments=confidence_assessments,
            human_choice_boundaries=human_boundaries,
            evidence_items=evidence_items,
        )

        logger.info(
            f"Decision recommendation report synthesized with top recommendation: '{top_rec.option_title if top_rec else 'None'}'."
        )
        return report

    def _formulate_human_choice_boundaries(
        self,
        context: DecisionContext,
        options: List[Option],
        tradeoff_matrix: TradeOffMatrix,
        risk_profiles: Dict[str, RiskProfile],
    ) -> List[HumanChoiceBoundary]:
        """Define explicit decision boundaries where human judgment must override automated models."""
        boundaries: List[HumanChoiceBoundary] = [
            HumanChoiceBoundary(
                category="Organizational Strategy & Culture",
                description="Evaluating alignment with unquantified long-term internal organizational culture or vendor partnerships.",
                tradeoff_condition="If team familiarity with legacy technology overrides raw benchmark scores.",
                human_action_required="Stakeholders should explicitly validate whether organizational adoption friction outweighs technical scoring.",
            ),
            HumanChoiceBoundary(
                category="Regulatory & Compliance Authorization",
                description="Final legal/regulatory compliance sign-off for data privacy and sovereignty.",
                tradeoff_condition="If deployment region requires localized data hosting compliance waivers.",
                human_action_required="Require explicit legal review prior to contract execution.",
            ),
            HumanChoiceBoundary(
                category="Budgetary Allocation Authority",
                description="Capital expenditure approval for upfront implementation costs.",
                tradeoff_condition="If capital expenditure exceeds delegation-of-authority financial limits.",
                human_action_required="Escalate for formal executive sponsor finance sign-off.",
            ),
        ]
        return boundaries
