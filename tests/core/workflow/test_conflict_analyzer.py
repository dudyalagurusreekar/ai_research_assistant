"""Unit test for ConflictAnalyzer."""

import pytest

from core.workflow.components.conflict_analyzer import ConflictAnalyzer
from core.workflow.models.evidence import EvidenceConfidence, EvidenceRecord, EvidenceSourceType


def test_conflict_analyzer_low_confidence():
    analyzer = ConflictAnalyzer()
    e1 = EvidenceRecord(
        question_id="rq_1",
        content="Solid evidence claim.",
        source_type=EvidenceSourceType.LITERATURE,
        confidence_score=0.95,
    )
    e2 = EvidenceRecord(
        question_id="rq_1",
        content="Uncertain claim.",
        source_type=EvidenceSourceType.WEB_SEARCH,
        confidence_score=0.40,
    )

    reports = analyzer.analyze_conflicts([e1, e2])

    assert len(reports) == 1
    assert reports[0].is_resolved is True
    assert "Discarded low confidence" in reports[0].resolved_finding
