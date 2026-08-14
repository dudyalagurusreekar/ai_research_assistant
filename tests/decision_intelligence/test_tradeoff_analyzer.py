"""Unit tests for TradeoffAnalyzer component."""

import pytest
from core.decision_intelligence.components.decision_analyzer import DecisionAnalyzer
from core.decision_intelligence.components.evidence_aggregator import EvidenceAggregator
from core.decision_intelligence.components.option_generator import OptionGenerator
from core.decision_intelligence.components.tradeoff_analyzer import TradeoffAnalyzer


def test_tradeoff_analyzer_mcda():
    analyzer = DecisionAnalyzer()
    generator = OptionGenerator()
    aggregator = EvidenceAggregator()
    tradeoff = TradeoffAnalyzer()

    ctx = analyzer.analyze_context("Select cloud architecture")
    options = generator.generate_options(ctx)
    evidence = aggregator.aggregate_evidence(ctx, options)

    matrix = tradeoff.analyze_tradeoffs(ctx, options, evidence)

    assert len(matrix.option_evaluations) == len(options)
    assert len(matrix.pareto_frontier_option_ids) >= 1
    assert len(matrix.tradeoff_summaries) >= 1

    # Ranks should be 1..N
    ranks = [e.rank for e in matrix.option_evaluations.values()]
    assert sorted(ranks) == list(range(1, len(options) + 1))
