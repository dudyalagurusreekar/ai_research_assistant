"""Reflection data structures and assessment models for ARA v2.0."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ReflectionAction(Enum):
    """Action resulting from reflection evaluation."""

    PROCEED = "proceed"                       # Execution quality is high, proceed to final report synthesis
    REPLAN = "replan"                         # Execution plan requires structural replanning
    PRUNE_STEPS = "prune_steps"               # Remove redundant or dead-end DAG nodes
    GATHER_MORE_EVIDENCE = "gather_evidence" # Inject additional evidence collection task
    RESOLVE_CONFLICT = "resolve_conflict"     # Inject conflict resolution task for opposing sources
    HALT_ERROR = "halt_error"                 # Unrecoverable execution error


class EvidenceQuality(Enum):
    """Quality classification for gathered evidence."""

    HIGH = "high"
    MODERATE = "moderate"
    WEAK = "weak"
    CONFLICTING = "conflicting"
    INSUFFICIENT = "insufficient"


@dataclass
class ReasoningAssessment:
    """Evaluation of logical reasoning quality and hallucination risk."""

    completeness_score: float = 1.0       # 0.0 to 1.0 score matching query intent
    coherence_score: float = 1.0          # 0.0 to 1.0 logical structure score
    hallucination_risk_score: float = 0.0 # 0.0 (low risk) to 1.0 (high risk)
    confidence_score: float = 0.95        # Overall reasoning confidence
    unaddressed_aspects: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completeness_score": round(self.completeness_score, 2),
            "coherence_score": round(self.coherence_score, 2),
            "hallucination_risk_score": round(self.hallucination_risk_score, 2),
            "confidence_score": round(self.confidence_score, 2),
            "unaddressed_aspects": self.unaddressed_aspects,
        }


@dataclass
class EvidenceAssessment:
    """Evaluation of evidence richness, diversity, and conflict detection."""

    quality: EvidenceQuality = EvidenceQuality.HIGH
    quality_score: float = 1.0            # 0.0 to 1.0 score
    source_count: int = 1
    freshness_score: float = 1.0          # 0.0 to 1.0
    conflict_detected: bool = False
    conflicting_sources: List[str] = field(default_factory=list)
    missing_keys: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality": self.quality.value,
            "quality_score": round(self.quality_score, 2),
            "source_count": self.source_count,
            "freshness_score": round(self.freshness_score, 2),
            "conflict_detected": self.conflict_detected,
            "conflicting_sources": self.conflicting_sources,
            "missing_keys": self.missing_keys,
        }


@dataclass
class PlanCriticReport:
    """Critique of the execution graph (DAG) identifying dead-ends and redundant steps."""

    redundant_node_ids: List[str] = field(default_factory=list)
    dead_end_node_ids: List[str] = field(default_factory=list)
    suggested_prunings: List[str] = field(default_factory=list)
    missing_capability_nodes: List[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.redundant_node_ids or self.dead_end_node_ids or self.missing_capability_nodes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "redundant_nodes": self.redundant_node_ids,
            "dead_end_nodes": self.dead_end_node_ids,
            "suggested_prunings": self.suggested_prunings,
            "missing_capabilities": self.missing_capability_nodes,
        }


@dataclass
class ReflectionDecision:
    """Audit record capturing reflection evaluation outcomes and graph modifications."""

    decision_id: str = field(default_factory=lambda: f"ref_{uuid.uuid4().hex[:8]}")
    action: ReflectionAction = ReflectionAction.PROCEED
    rationale: str = ""
    impact_summary: str = ""
    nodes_to_add: List[Dict[str, Any]] = field(default_factory=list)
    nodes_to_remove: List[str] = field(default_factory=list)
    reasoning_assessment: ReasoningAssessment = field(default_factory=ReasoningAssessment)
    evidence_assessment: EvidenceAssessment = field(default_factory=EvidenceAssessment)
    critic_report: PlanCriticReport = field(default_factory=PlanCriticReport)
    reflection_iteration: int = 1
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action": self.action.value,
            "rationale": self.rationale,
            "impact_summary": self.impact_summary,
            "nodes_added": len(self.nodes_to_add),
            "nodes_removed": self.nodes_to_remove,
            "reasoning": self.reasoning_assessment.to_dict(),
            "evidence": self.evidence_assessment.to_dict(),
            "critic": self.critic_report.to_dict(),
            "iteration": self.reflection_iteration,
            "timestamp": self.timestamp.isoformat(),
        }
