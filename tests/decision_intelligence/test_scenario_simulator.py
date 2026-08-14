"""Unit tests for ScenarioSimulator component."""

import pytest
from core.decision_intelligence.components.decision_analyzer import DecisionAnalyzer
from core.decision_intelligence.components.evidence_aggregator import EvidenceAggregator
from core.decision_intelligence.components.option_generator import OptionGenerator
from core.decision_intelligence.components.scenario_simulator import ScenarioSimulator
from core.decision_intelligence.components.tradeoff_analyzer import TradeoffAnalyzer


def test_scenario_simulator_run():
    analyzer = DecisionAnalyzer()
    generator = OptionGenerator()
    aggregator = EvidenceAggregator()
    tradeoff = TradeoffAnalyzer()
    simulator = ScenarioSimulator()

    ctx = analyzer.analyze_context("Select cloud architecture")
    options = generator.generate_options(ctx)
    evidence = aggregator.aggregate_evidence(ctx, options)
    matrix = tradeoff.analyze_tradeoffs(ctx, options, evidence)

    results = simulator.run_simulations(ctx, options, matrix)

    assert len(results) == len(options)
    for opt in options:
        res = results[opt.option_id]
        assert res.baseline_outcome is not None
        assert len(res.alternative_scenarios) >= 3
        assert len(res.sensitivity_drivers) >= 1
        assert 0.0 <= res.robustness_score <= 1.0
