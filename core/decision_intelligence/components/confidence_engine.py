"""Confidence Engine Component — Quantifies uncertainty and evidence calibration."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.confidence import (
    ConfidenceAssessment,
    ConfidenceLevel,
    UncertaintyFactor,
)
from core.decision_intelligence.models.evidence import EvidenceItem, VerificationStatus
from core.decision_intelligence.models.option import Option
from utils.logger import get_logger

logger = get_logger("ConfidenceEngine")


class ConfidenceEngine:
    """Component responsible for uncertainty quantification and evidence confidence calibration."""

    def __init__(self) -> None:
        pass

    def evaluate_confidence(
        self,
        options: List[Option],
        evidence_items: List[EvidenceItem],
    ) -> Dict[str, ConfidenceAssessment]:
        """Evaluate composite confidence scores and uncertainty factors for each option."""
        logger.info(f"Quantifying confidence and uncertainty for {len(options)} options.")
        assessments: Dict[str, ConfidenceAssessment] = {}

        for opt in options:
            opt_evidence = [e for e in evidence_items if e.option_id == opt.option_id or not e.option_id]
            assessment = self._evaluate_option_confidence(opt, opt_evidence)
            assessments[opt.option_id] = assessment

        logger.info(f"Confidence evaluation complete for {len(assessments)} options.")
        return assessments

    def _evaluate_option_confidence(
        self, option: Option, evidence_items: List[EvidenceItem]
    ) -> ConfidenceAssessment:
        """Calculate evidence coverage, source authority, and confidence intervals."""
        uncertainty_factors: List[UncertaintyFactor] = []

        if not evidence_items:
            coverage_pct = 40.0
            authority_score = 0.50
            uncertainty_factors.append(
                UncertaintyFactor(
                    title="Sparse Evidence Base",
                    description="No direct empirical benchmark evidence available for option.",
                    source="evidence_aggregator",
                    impact_magnitude=0.35,
                    mitigation_suggestion="Run additional web verification or benchmark tests.",
                )
            )
        else:
            verified_count = sum(1 for e in evidence_items if e.verification_status == VerificationStatus.VERIFIED)
            coverage_pct = min(100.0, round((verified_count / max(1, len(evidence_items))) * 90.0 + 10.0, 1))
            authority_score = round(sum(e.confidence_score for e in evidence_items) / max(1, len(evidence_items)), 2)

        # Check for soft constraint penalties
        if option.feasibility.soft_constraint_violations:
            uncertainty_factors.append(
                UncertaintyFactor(
                    title="Policy Constraint Violation",
                    description="Option violates non-critical policy guidelines.",
                    source="option_generator",
                    impact_magnitude=0.15,
                    mitigation_suggestion="Confirm policy exception waiver with compliance stakeholders.",
                )
            )

        # Check for high complexity uncertainty
        if option.implementation_complexity.lower() in ["high", "extreme"]:
            uncertainty_factors.append(
                UncertaintyFactor(
                    title="High Complexity Execution Risk",
                    description="Architectural complexity increases variance in timeline and resource estimates.",
                    source="risk_assessment",
                    impact_magnitude=0.20,
                    mitigation_suggestion="Conduct proof-of-concept spike prior to full rollout.",
                )
            )

        # Compute composite confidence score
        penalty = sum(uf.impact_magnitude for uf in uncertainty_factors)
        composite_score = round(max(0.20, min(0.98, (authority_score * (coverage_pct / 100.0)) - (penalty * 0.3))), 2)

        if composite_score >= 0.80:
            level = ConfidenceLevel.HIGH
        elif composite_score >= 0.60:
            level = ConfidenceLevel.MEDIUM
        elif composite_score >= 0.40:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.UNCERTAIN

        ci_lower = round(max(0.0, composite_score - 0.08), 2)
        ci_upper = round(min(1.0, composite_score + 0.07), 2)

        return ConfidenceAssessment(
            option_id=option.option_id,
            overall_confidence_score=composite_score,
            confidence_level=level,
            evidence_coverage_pct=coverage_pct,
            data_source_authority_score=authority_score,
            uncertainty_factors=uncertainty_factors,
            confidence_interval=[ci_lower, ci_upper],
        )
