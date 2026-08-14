"""Unit test for EvidenceAggregator."""

import pytest

from core.collaboration import SharedWorkspace
from core.workflow.components.evidence_aggregator import EvidenceAggregator
from core.workflow.models.question import ResearchQuestion


def test_evidence_aggregator_workspace_harvesting():
    aggregator = EvidenceAggregator()
    workspace = SharedWorkspace()
    workspace.set("research_summary", "Transformer models achieve 95% accuracy in benchmarks.", artifact_type="text")
    workspace.set("data_stats", {"mean_ms": 1.5, "p95_ms": 3.2}, artifact_type="json")

    questions = [ResearchQuestion(question_text="What are the performance metrics?")]
    evidence = aggregator.aggregate_evidence(questions, workspace=workspace)

    assert len(evidence) >= 2
    assert any("Transformer" in e.content for e in evidence)
    assert any("mean_ms" in e.content for e in evidence)
