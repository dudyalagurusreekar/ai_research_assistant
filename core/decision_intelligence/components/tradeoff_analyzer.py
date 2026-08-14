"""Trade-off Analyzer Component — Evaluates multi-criteria trade-offs and computes Pareto efficiency."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.evidence import EvidenceItem
from core.decision_intelligence.models.objective import DecisionContext, Objective
from core.decision_intelligence.models.option import Option, OptionStatus
from core.decision_intelligence.models.tradeoff import (
    CriterionScore,
    OptionEvaluation,
    TradeOffMatrix,
)
from utils.logger import get_logger

logger = get_logger("TradeoffAnalyzer")


class TradeoffAnalyzer:
    """Component implementing MCDA scoring, weighted matrix normalization, and Pareto frontier detection."""

    def __init__(self) -> None:
        pass

    def analyze_tradeoffs(
        self,
        context: DecisionContext,
        options: List[Option],
        evidence_items: List[EvidenceItem],
    ) -> TradeOffMatrix:
        """Construct multi-criteria evaluation matrix and identify Pareto-optimal options."""
        logger.info(f"Analyzing trade-offs across {len(options)} options and {len(context.objectives)} criteria.")
        matrix = TradeOffMatrix()

        if not options or not context.objectives:
            logger.warning("No options or objectives provided for trade-off analysis.")
            return matrix

        # Map objective weights
        criteria_weights = {obj.objective_id: obj.weight for obj in context.objectives}
        matrix.criteria_weights = criteria_weights

        # 1. Score each option against each objective criterion
        option_evaluations: Dict[str, OptionEvaluation] = {}
        for opt in options:
            eval_item = OptionEvaluation(
                option_id=opt.option_id,
                option_title=opt.title,
            )

            # Infeasible options get penalized
            status_multiplier = 1.0 if opt.status == OptionStatus.FEASIBLE else (0.7 if opt.status == OptionStatus.CONDITIONAL else 0.2)

            for obj in context.objectives:
                raw_val, norm_score, justification = self._score_option_against_objective(opt, obj, evidence_items)
                norm_score = max(0.0, min(1.0, norm_score * status_multiplier))
                weighted_score = round(norm_score * obj.weight, 4)

                c_score = CriterionScore(
                    criterion_id=obj.objective_id,
                    criterion_name=obj.name,
                    raw_value=raw_val,
                    normalized_score=round(norm_score, 4),
                    weighted_score=weighted_score,
                    justification=justification,
                    supporting_evidence_ids=[e.evidence_id for e in evidence_items if e.option_id == opt.option_id],
                )
                eval_item.criteria_scores[obj.objective_id] = c_score

            # Sum total weighted score
            eval_item.total_weighted_score = round(sum(cs.weighted_score for cs in eval_item.criteria_scores.values()), 4)
            option_evaluations[opt.option_id] = eval_item

        # 2. Compute Pareto Frontier and dominance relationships
        self._compute_pareto_frontier(option_evaluations, context.objectives)

        # 3. Assign Ranks
        sorted_evals = sorted(option_evaluations.values(), key=lambda x: x.total_weighted_score, reverse=True)
        for idx, item in enumerate(sorted_evals, 1):
            item.rank = idx

        matrix.option_evaluations = option_evaluations
        matrix.pareto_frontier_option_ids = [k for k, v in option_evaluations.items() if v.is_pareto_optimal]

        # 4. Generate Trade-off summaries
        matrix.tradeoff_summaries = self._generate_tradeoff_summaries(matrix, context.objectives)

        logger.info(
            f"Tradeoff analysis complete. Top option score: {sorted_evals[0].total_weighted_score if sorted_evals else 0.0}. Pareto options: {len(matrix.pareto_frontier_option_ids)}."
        )
        return matrix

    def _score_option_against_objective(
        self, option: Option, objective: Objective, evidence_items: List[EvidenceItem]
    ) -> tuple[Any, float, str]:
        """Compute normalized score [0.0..1.0] for option on objective."""
        o_name_lower = objective.name.lower()
        cat_value = objective.category.value.lower()

        # Financial / Cost
        if "cost" in o_name_lower or cat_value == "financial":
            cost = option.estimated_cost
            # Lower cost is better if MINIMIZE
            if cost <= 500:
                score = 1.0
            elif cost <= 1500:
                score = 0.8
            elif cost <= 3000:
                score = 0.5
            else:
                score = 0.2
            if objective.target_direction == "MAXIMIZE":
                score = 1.0 - score
            return cost, score, f"Estimated cost of ${cost:,.2f}"

        # Technical / Performance / Complexity
        if "technical" in cat_value or "performance" in o_name_lower or "speed" in o_name_lower:
            comp = option.implementation_complexity.lower()
            if comp == "low":
                score = 0.95
            elif comp == "medium":
                score = 0.75
            else:
                score = 0.5
            return option.implementation_complexity, score, f"Implementation complexity is {option.implementation_complexity}"

        # Operational / Time to value
        if "operational" in cat_value or "time" in o_name_lower or "simplicity" in o_name_lower:
            days = option.time_to_value_days
            if days <= 7:
                score = 1.0
            elif days <= 15:
                score = 0.8
            elif days <= 30:
                score = 0.6
            else:
                score = 0.3
            return f"{days} days", score, f"Time to value estimated at {days} days"

        # Heuristic scoring based on pros vs cons
        pro_count = len(option.pros)
        con_count = len(option.cons)
        base_score = 0.7 + (pro_count * 0.05) - (con_count * 0.05)
        base_score = max(0.1, min(0.95, base_score))
        return f"{pro_count} pros / {con_count} cons", base_score, f"Supported by {pro_count} advantages"

    def _compute_pareto_frontier(
        self, option_evaluations: Dict[str, OptionEvaluation], objectives: List[Objective]
    ) -> None:
        """Mark options as Pareto-optimal if no other option strictly dominates them across all criteria."""
        evals = list(option_evaluations.values())
        obj_ids = [o.objective_id for o in objectives]

        for i, a in enumerate(evals):
            is_dominated = False
            for j, b in enumerate(evals):
                if i == j:
                    continue

                # b dominates a if b is >= a on all criteria and > on at least one
                b_better_or_equal = True
                b_strictly_better = False

                for oid in obj_ids:
                    score_a = a.criteria_scores.get(oid, CriterionScore()).normalized_score
                    score_b = b.criteria_scores.get(oid, CriterionScore()).normalized_score

                    if score_b < score_a:
                        b_better_or_equal = False
                        break
                    if score_b > score_a:
                        b_strictly_better = True

                if b_better_or_equal and b_strictly_better:
                    is_dominated = True
                    a.dominated_by_option_ids.append(b.option_id)
                    b.dominates_option_ids.append(a.option_id)

            a.is_pareto_optimal = not is_dominated

    def _generate_tradeoff_summaries(self, matrix: TradeOffMatrix, objectives: List[Objective]) -> List[str]:
        """Summarize key trade-offs between options."""
        summaries: List[str] = []
        evals = sorted(matrix.option_evaluations.values(), key=lambda x: x.rank)

        if len(evals) >= 2:
            top = evals[0]
            runner_up = evals[1]
            summaries.append(
                f"Rank 1 ({top.option_title}) scores {top.total_weighted_score:.3f} vs Rank 2 ({runner_up.option_title}) scoring {runner_up.total_weighted_score:.3f}."
            )
            summaries.append(
                f"Pareto Frontier contains {len(matrix.pareto_frontier_option_ids)} non-dominated options out of {len(evals)} total options."
            )

        return summaries
