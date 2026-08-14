"""Unit tests for EvidenceAggregator component."""

import pytest
from core.decision_intelligence.components.decision_analyzer import DecisionAnalyzer
from core.decision_intelligence.components.evidence_aggregator import EvidenceAggregator
from core.decision_intelligence.components.option_generator import OptionGenerator
from core.decision_intelligence.models import VerificationStatus


def test_evidence_aggregator_aggregation():
    analyzer = DecisionAnalyzer()
    generator = OptionGenerator()
    aggregator = EvidenceAggregator()

    ctx = analyzer.analyze_context("Select database")
    options = generator.generate_options(ctx)

    subsystem_payload = {
        "knowledge_graph_entities": [{"uri": "kg://pg", "name": "PostgreSQL Entity", "summary": "ACID compliant DB"}],
        "data_intelligence_metrics": [{"id": "m1", "metric_name": "P99 Latency", "value": 15, "unit": "ms"}],
    }

    evidence = aggregator.aggregate_evidence(ctx, options, subsystem_sources=subsystem_payload)
    assert len(evidence) >= 2
    assert any(e.source_subsystem == "knowledge_graph" for e in evidence)
    assert any(e.source_subsystem == "data_intelligence" for e in evidence)
    assert all(e.verification_status == VerificationStatus.VERIFIED for e in evidence)
