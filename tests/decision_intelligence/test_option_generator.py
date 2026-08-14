"""Unit tests for OptionGenerator component."""

import pytest
from core.decision_intelligence.components.decision_analyzer import DecisionAnalyzer
from core.decision_intelligence.components.option_generator import OptionGenerator
from core.decision_intelligence.models import OptionStatus, Constraint, ConstraintType, ComparisonOperator


def test_option_generator_default_synthesis():
    analyzer = DecisionAnalyzer()
    generator = OptionGenerator()

    ctx = analyzer.analyze_context("Which cloud architecture is best for containerized microservices?")
    options = generator.generate_options(ctx)

    assert len(options) >= 3
    assert any(o.status in [OptionStatus.FEASIBLE, OptionStatus.CONDITIONAL] for o in options)
    for opt in options:
        assert opt.title != ""
        assert isinstance(opt.pros, list)
        assert isinstance(opt.cons, list)


def test_option_generator_preset_options_feasibility():
    analyzer = DecisionAnalyzer()
    generator = OptionGenerator()

    hard_cost_const = Constraint(
        name="Cost Cap",
        constraint_type=ConstraintType.HARD,
        metric="estimated_cost",
        threshold_value=2000.0,
        operator=ComparisonOperator.LESS_THAN_OR_EQUAL,
    )
    ctx = analyzer.analyze_context("Select vendor", explicit_constraints=[hard_cost_const])

    presets = [
        {"title": "Low Cost Vendor", "estimated_cost": 1500.0, "implementation_complexity": "low"},
        {"title": "Expensive Vendor", "estimated_cost": 5000.0, "implementation_complexity": "high"},
    ]

    options = generator.generate_options(ctx, preset_options=presets)
    assert len(options) == 2
    opt_low = next(o for o in options if o.title == "Low Cost Vendor")
    opt_exp = next(o for o in options if o.title == "Expensive Vendor")

    assert opt_low.status == OptionStatus.FEASIBLE
    assert opt_exp.status == OptionStatus.INFEASIBLE
    assert "Cost Cap" in opt_exp.feasibility.hard_constraints_failed
