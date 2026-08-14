"""Unit tests for RiskAssessmentEngine component."""

import pytest
from core.decision_intelligence.components.decision_analyzer import DecisionAnalyzer
from core.decision_intelligence.components.option_generator import OptionGenerator
from core.decision_intelligence.components.risk_assessment import RiskAssessmentEngine


def test_risk_assessment_evaluation():
    analyzer = DecisionAnalyzer()
    generator = OptionGenerator()
    risk_engine = RiskAssessmentEngine()

    ctx = analyzer.analyze_context("Select cloud architecture")
    options = generator.generate_options(ctx)

    profiles = risk_engine.evaluate_risks(ctx, options)

    assert len(profiles) == len(options)
    for opt in options:
        profile = profiles[opt.option_id]
        assert profile.option_id == opt.option_id
        assert profile.overall_risk_score >= 0.0
        assert profile.risk_level in ["low", "medium", "high", "critical"]
        assert len(profile.risk_factors) >= 1
        assert profile.mitigation_summary != ""
