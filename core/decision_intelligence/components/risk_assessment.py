"""Risk Assessment Engine Component — Identifies risk factors, calculates severity scores, and formulates mitigations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.objective import DecisionContext
from core.decision_intelligence.models.option import Option
from core.decision_intelligence.models.risk import (
    RiskCategory,
    RiskFactor,
    RiskProfile,
)
from utils.logger import get_logger

logger = get_logger("RiskAssessmentEngine")


class RiskAssessmentEngine:
    """Component responsible for identifying risk factors, calculating severity scores, and proposing mitigations."""

    def __init__(self) -> None:
        pass

    def evaluate_risks(
        self,
        context: DecisionContext,
        options: List[Option],
    ) -> Dict[str, RiskProfile]:
        """Evaluate risk profile for all candidate options."""
        logger.info(f"Evaluating risk profiles for {len(options)} candidate options.")
        profiles: Dict[str, RiskProfile] = {}

        for opt in options:
            profile = self._evaluate_option_risk(opt, context)
            profiles[opt.option_id] = profile

        logger.info(f"Risk evaluation completed for {len(profiles)} option profiles.")
        return profiles

    def _evaluate_option_risk(self, option: Option, context: DecisionContext) -> RiskProfile:
        """Analyze risk factors and calculate risk index for an option."""
        risk_factors: List[RiskFactor] = []
        spofs: List[str] = []

        # Complexity risk
        comp = option.implementation_complexity.lower()
        if comp == "high" or comp == "extreme":
            risk_factors.append(
                RiskFactor(
                    option_id=option.option_id,
                    title="High Architectural Complexity",
                    description=f"Option has high implementation complexity ({comp}), increasing integration risk.",
                    category=RiskCategory.TECHNICAL,
                    probability=0.45,
                    impact=4.0,
                    severity_score=1.8,
                    mitigation_strategy="Implement phased milestone rollouts and comprehensive automated end-to-end testing.",
                    residual_risk_score=0.6,
                )
            )

        # Cost risk
        if option.estimated_cost > 3000:
            risk_factors.append(
                RiskFactor(
                    option_id=option.option_id,
                    title="Budget Overrun Risk",
                    description=f"High estimated cost (${option.estimated_cost:,.2f}) exposes project to financial strain.",
                    category=RiskCategory.FINANCIAL,
                    probability=0.35,
                    impact=3.5,
                    severity_score=1.225,
                    mitigation_strategy="Establish strict cloud cost alerts and quarterly budget variance reviews.",
                    residual_risk_score=0.4,
                )
            )

        # Vendor Lock-in or Single Point of Failure heuristics
        opt_title_lower = option.title.lower()
        if "vendor" in opt_title_lower or "cloud native" in opt_title_lower or "managed" in opt_title_lower:
            risk_factors.append(
                RiskFactor(
                    option_id=option.option_id,
                    title="Vendor Dependency & Lock-in",
                    description="Reliance on proprietary managed platform APIs limits multi-cloud flexibility.",
                    category=RiskCategory.VENDOR_LOCKIN,
                    probability=0.50,
                    impact=3.0,
                    severity_score=1.5,
                    mitigation_strategy="Abstract cloud provider APIs behind standard interfaces or adapter layers.",
                    residual_risk_score=0.5,
                )
            )
            spofs.append("Single Managed Cloud Provider Infrastructure")

        # Soft constraint violation risk
        if option.feasibility.soft_constraint_violations:
            for violation in option.feasibility.soft_constraint_violations:
                risk_factors.append(
                    RiskFactor(
                        option_id=option.option_id,
                        title=f"Soft Constraint Violation: {violation}",
                        description=f"Violates operational policy guideline: {violation}",
                        category=RiskCategory.OPERATIONAL,
                        probability=0.4,
                        impact=3.0,
                        severity_score=1.2,
                        mitigation_strategy="Request stakeholder compliance waiver or adjust operational thresholds.",
                        residual_risk_score=0.4,
                    )
                )

        # Ensure at least one baseline risk factor is recorded
        if not risk_factors:
            risk_factors.append(
                RiskFactor(
                    option_id=option.option_id,
                    title="Standard Operational Change Management",
                    description="Standard operational risk associated with deploying infrastructure updates.",
                    category=RiskCategory.OPERATIONAL,
                    probability=0.2,
                    impact=2.0,
                    severity_score=0.4,
                    mitigation_strategy="Follow standard blue/green deployment and canary release protocol.",
                    residual_risk_score=0.1,
                )
            )

        # Calculate overall aggregate risk score
        overall_risk_score = round(sum(rf.severity_score for rf in risk_factors) / max(1, len(risk_factors)), 2)

        if overall_risk_score >= 2.5:
            risk_level = "high"
        elif overall_risk_score >= 1.2:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Determine primary risk category
        cat_counts: Dict[RiskCategory, float] = {}
        for rf in risk_factors:
            cat_counts[rf.category] = cat_counts.get(rf.category, 0.0) + rf.severity_score

        primary_category = max(cat_counts.items(), key=lambda x: x[1])[0] if cat_counts else RiskCategory.TECHNICAL

        return RiskProfile(
            option_id=option.option_id,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            primary_risk_category=primary_category,
            single_points_of_failure=spofs,
            mitigation_summary=f"Primary risk category: {primary_category.value}. Total of {len(risk_factors)} identified risk factors with mitigations.",
        )
