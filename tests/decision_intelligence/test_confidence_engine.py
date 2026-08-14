"""Unit tests for ConfidenceEngine component."""

import pytest
from core.decision_intelligence.components.decision_analyzer import DecisionAnalyzer
from core.decision_intelligence.components.evidence_aggregator import EvidenceAggregator
from core.decision_intelligence.components.option_generator import OptionGenerator
from core.decision_intelligence.components.confidence_engine import ConfidenceEngine
from core.decision_intelligence.models import ConfidenceLevel


def test_confidence_engine_evaluation():
    analyzer = DecisionAnalyzer()
    generator = OptionGenerator()
    aggregator = EvidenceAggregator()
    confidence = ConfidenceEngine()

    ctx = analyzer.analyze_context("Select cloud architecture")
    options = generator.generate_options(ctx)
    evidence = aggregator.aggregate_evidence(ctx, options)

    assessments = confidence.evaluate_confidence(options, evidence)

    assert len(assessments) == len(options)
    for opt in options:
        assess = assessments[opt.option_id]
        assert 0.0 <= assess.overall_confidence_score <= 1.0
        assert assess.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN]
        assert len(assess.confidence_interval) == 2
        assert assess.confidence_interval[0] <= assess.confidence_interval[1]
