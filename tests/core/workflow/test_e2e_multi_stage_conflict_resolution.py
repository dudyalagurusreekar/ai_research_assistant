"""End-to-End test for Multi-Stage Evidence Aggregation and Conflict Resolution."""

import pytest

from core.workflow.components.conflict_analyzer import ConflictAnalyzer
from core.workflow.components.evidence_aggregator import EvidenceAggregator
from core.workflow.models.evidence import EvidenceConfidence, EvidenceRecord, EvidenceSourceType
from core.workflow.models.question import ResearchQuestion


def test_e2e_multi_stage_conflict_resolution():
    q1 = ResearchQuestion(question_text="What is the throughput of Model A?")
    e_lit = EvidenceRecord(
        question_id=q1.question_id,
        content="Literature reports 95% accuracy for Model A.",
        source_type=EvidenceSourceType.LITERATURE,
        confidence_score=0.95,
    )
    e_low = EvidenceRecord(
        question_id=q1.question_id,
        content="Unverified web blog claims Model A failed.",
        source_type=EvidenceSourceType.WEB_SEARCH,
        confidence_score=0.35,
    )

    analyzer = ConflictAnalyzer()
    conflicts = analyzer.analyze_conflicts([e_lit, e_low])

    assert len(conflicts) >= 1
    assert any(c.is_resolved for c in conflicts)
