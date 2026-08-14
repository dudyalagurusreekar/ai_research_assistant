"""Scenario Simulation and Sensitivity Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ScenarioType(str, Enum):
    BASELINE = "baseline"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    HIGH_GROWTH = "high_growth"
    BUDGET_CONSTRAINED = "budget_constrained"
    COUNTERFACTUAL = "counterfactual"


@dataclass
class ScenarioOutcome:
    """Outcomes of simulating an option under a specific scenario condition."""

    scenario_id: str = field(default_factory=lambda: f"scen_{uuid.uuid4().hex[:8]}")
    option_id: str = ""
    scenario_name: str = ""
    scenario_type: ScenarioType = ScenarioType.BASELINE
    assumptions: List[str] = field(default_factory=list)
    projected_score: float = 0.0
    score_delta_from_baseline: float = 0.0
    risk_adjustment: float = 0.0
    outcome_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "option_id": self.option_id,
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type.value,
            "assumptions": self.assumptions,
            "projected_score": self.projected_score,
            "score_delta_from_baseline": self.score_delta_from_baseline,
            "risk_adjustment": self.risk_adjustment,
            "outcome_summary": self.outcome_summary,
        }


@dataclass
class SensitivityDriver:
    """Identifies how sensitive an option's rank is to changes in a criterion's weight."""

    criterion_id: str = ""
    criterion_name: str = ""
    baseline_weight: float = 0.0
    tipping_point_weight: Optional[float] = None  # Weight at which option rank flips
    impact_level: str = "medium"  # low, medium, high, critical
    sensitivity_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "criterion_name": self.criterion_name,
            "baseline_weight": self.baseline_weight,
            "tipping_point_weight": self.tipping_point_weight,
            "impact_level": self.impact_level,
            "sensitivity_description": self.sensitivity_description,
        }


@dataclass
class ScenarioSimulationResult:
    """Complete simulation and sensitivity analysis package for an option."""

    option_id: str = ""
    baseline_outcome: ScenarioOutcome = field(default_factory=ScenarioOutcome)
    alternative_scenarios: List[ScenarioOutcome] = field(default_factory=list)
    sensitivity_drivers: List[SensitivityDriver] = field(default_factory=list)
    robustness_score: float = 0.8  # 0.0 fragile to 1.0 highly robust across scenarios

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "baseline_outcome": self.baseline_outcome.to_dict(),
            "alternative_scenarios": [s.to_dict() for s in self.alternative_scenarios],
            "sensitivity_drivers": [sd.to_dict() for sd in self.sensitivity_drivers],
            "robustness_score": self.robustness_score,
        }
