"""Reflection Policy configuration model for ARA v2.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ReflectionPolicy:
    """Policy thresholds governing reflection evaluation, replanning, and pruning."""

    min_completeness_threshold: float = 0.75
    min_evidence_quality_threshold: float = 0.70
    max_hallucination_risk_threshold: float = 0.30
    max_reflection_loops: int = 3
    enable_auto_pruning: bool = True
    enable_conflict_resolution: bool = True
    max_additional_tasks_per_replan: int = 2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_completeness_threshold": self.min_completeness_threshold,
            "min_evidence_quality_threshold": self.min_evidence_quality_threshold,
            "max_hallucination_risk_threshold": self.max_hallucination_risk_threshold,
            "max_reflection_loops": self.max_reflection_loops,
            "enable_auto_pruning": self.enable_auto_pruning,
            "enable_conflict_resolution": self.enable_conflict_resolution,
        }
