"""Unit tests for RecommendationGenerator component."""

import pytest
from core.decision_intelligence.components.decision_analyzer import DecisionAnalyzer
from core.decision_intelligence.components.evidence_aggregator import EvidenceAggregator
from core.decision_intelligence.components.option_generator import OptionGenerator
from core.decision_intelligence.components.tradeoff_analyzer import TradeoffAnalyzer
from core.decision_intelligence.components.risk_assessment import RiskAssessmentEngine
from core.decision_intelligence.components.scenario_simulator import ScenarioSimulator
from core.decision_intelligence.components.confidence_engine import ConfidenceEngine
from core.decision_intelligence.components.recommendation_generator import RecommendationGenerator


def test_recommendation_generator_report():
    analyzer = DecisionAnalyzer()
    generator = OptionGenerator()
    aggregator = EvidenceAggregator()
    tradeoff = TradeoffAnalyzer()
    risk = RiskAssessmentEngine()
    simulator = ScenarioSimulator()
    confidence = ConfidenceEngine()
    recommendation = RecommendationGenerator()

    ctx = analyzer.analyze_context("Select cloud architecture")
    options = generator.generate_options(ctx)
    evidence = aggregator.aggregate_evidence(ctx, options)
    matrix = tradeoff.analyze_tradeoffs(ctx, options, evidence)
    risk_profiles = risk.evaluate_risks(ctx, options)
    sim_results = simulator.run_simulations(ctx, options, matrix)
    conf_assessments = confidence.evaluate_confidence(options, evidence)

    report = recommendation.generate_recommendation_report(
        context=ctx,
        options=options,
        tradeoff_matrix=matrix,
        risk_profiles=risk_profiles,
        simulation_results=sim_results,
        confidence_assessments=conf_assessments,
        evidence_items=evidence,
    )

    assert report.topic == ctx.topic
    assert report.top_recommendation is not None
    assert len(report.all_recommendations) == len(options)
    assert len(report.human_choice_boundaries) >= 1
    assert report.to_dict()["report_id"] is not None
