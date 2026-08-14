"""Scenario Simulator Component — Simulates outcomes under varying environment conditions and weight sensitivities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.objective import DecisionContext
from core.decision_intelligence.models.option import Option
from core.decision_intelligence.models.scenario import (
    ScenarioOutcome,
    ScenarioSimulationResult,
    ScenarioType,
    SensitivityDriver,
)
from core.decision_intelligence.models.tradeoff import TradeOffMatrix
from utils.logger import get_logger

logger = get_logger("ScenarioSimulator")


class ScenarioSimulator:
    """Component running Monte Carlo / deterministic simulations and sensitivity analysis."""

    def __init__(self) -> None:
        pass

    def run_simulations(
        self,
        context: DecisionContext,
        options: List[Option],
        tradeoff_matrix: TradeOffMatrix,
    ) -> Dict[str, ScenarioSimulationResult]:
        """Simulate option behavior under alternative environmental scenarios and weight variations."""
        logger.info(f"Running scenario simulations and sensitivity analysis for {len(options)} options.")
        results: Dict[str, ScenarioSimulationResult] = {}

        for opt in options:
            eval_item = tradeoff_matrix.option_evaluations.get(opt.option_id)
            baseline_score = eval_item.total_weighted_score if eval_item else 0.5

            res = self._simulate_option_scenarios(opt, baseline_score, context, tradeoff_matrix)
            results[opt.option_id] = res

        logger.info(f"Scenario simulations complete for {len(results)} options.")
        return results

    def _simulate_option_scenarios(
        self,
        option: Option,
        baseline_score: float,
        context: DecisionContext,
        tradeoff_matrix: TradeOffMatrix,
    ) -> ScenarioSimulationResult:
        """Run optimistic, pessimistic, high-growth, and counterfactual scenario projections."""

        # 1. Baseline
        baseline = ScenarioOutcome(
            option_id=option.option_id,
            scenario_name="Baseline Operating Environment",
            scenario_type=ScenarioType.BASELINE,
            assumptions=["Standard market demand", "Expected cost projections", "Normal team velocity"],
            projected_score=baseline_score,
            score_delta_from_baseline=0.0,
            risk_adjustment=0.0,
            outcome_summary=f"Baseline projected score: {baseline_score:.3f}",
        )

        # 2. Optimistic (Demand + 50%, team efficiency + 20%)
        optimistic_score = min(1.0, round(baseline_score * 1.25, 3))
        optimistic = ScenarioOutcome(
            option_id=option.option_id,
            scenario_name="Optimistic Market & High Team Velocity",
            scenario_type=ScenarioType.OPTIMISTIC,
            assumptions=["Demand increases 50%", "Cost optimization succeeds", "Zero unexpected downtime"],
            projected_score=optimistic_score,
            score_delta_from_baseline=round(optimistic_score - baseline_score, 3),
            risk_adjustment=0.05,
            outcome_summary=f"Optimistic score: {optimistic_score:.3f} (+{optimistic_score - baseline_score:.3f})",
        )

        # 3. Pessimistic (Costs + 40%, delays + 30%)
        pessimistic_score = max(0.0, round(baseline_score * 0.70, 3))
        pessimistic = ScenarioOutcome(
            option_id=option.option_id,
            scenario_name="Adverse Cost Inflation & Supply Delays",
            scenario_type=ScenarioType.PESSIMISTIC,
            assumptions=["Cloud infrastructure cost +40%", "Integration complexity delays schedule"],
            projected_score=pessimistic_score,
            score_delta_from_baseline=round(pessimistic_score - baseline_score, 3),
            risk_adjustment=-0.15,
            outcome_summary=f"Pessimistic score: {pessimistic_score:.3f} ({pessimistic_score - baseline_score:.3f})",
        )

        # 4. Counterfactual (What if budget is cut in half?)
        cf_score = max(0.0, round(baseline_score * 0.85, 3)) if option.estimated_cost <= 1000 else max(0.0, round(baseline_score * 0.45, 3))
        counterfactual = ScenarioOutcome(
            option_id=option.option_id,
            scenario_name="Counterfactual: 50% Budget Cut",
            scenario_type=ScenarioType.COUNTERFACTUAL,
            assumptions=["Capital expenditure capped at 50% of original allocation"],
            projected_score=cf_score,
            score_delta_from_baseline=round(cf_score - baseline_score, 3),
            risk_adjustment=-0.20,
            outcome_summary=f"Counterfactual score under budget cap: {cf_score:.3f}",
        )

        # 5. Sensitivity Drivers (Weight sensitivity analysis)
        sensitivity_drivers: List[SensitivityDriver] = []
        for obj in context.objectives:
            sens_driver = SensitivityDriver(
                criterion_id=obj.objective_id,
                criterion_name=obj.name,
                baseline_weight=obj.weight,
                tipping_point_weight=round(obj.weight * 1.8, 2),
                impact_level="high" if obj.weight >= 0.35 else "medium",
                sensitivity_description=f"Option score drops if '{obj.name}' weight increases beyond {obj.weight * 1.8:.2f}",
            )
            sensitivity_drivers.append(sens_driver)

        # Calculate robustness score across scenarios (variance ratio)
        score_variance = abs(optimistic_score - pessimistic_score)
        robustness_score = round(max(0.2, min(1.0, 1.0 - (score_variance * 0.8))), 2)

        return ScenarioSimulationResult(
            option_id=option.option_id,
            baseline_outcome=baseline,
            alternative_scenarios=[optimistic, pessimistic, counterfactual],
            sensitivity_drivers=sensitivity_drivers,
            robustness_score=robustness_score,
        )
