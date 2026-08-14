"""Unit tests for DecisionAnalyzer component."""

import pytest
from core.decision_intelligence.components.decision_analyzer import DecisionAnalyzer
from core.decision_intelligence.models import ConstraintType, ObjectiveType, ComparisonOperator


def test_decision_analyzer_basic_query():
    analyzer = DecisionAnalyzer()
    ctx = analyzer.analyze_context(
        query="Choose a database with latency under 100ms and budget under $5000 USD for high throughput analytics",
        topic="Database Selection",
    )

    assert ctx.topic == "Database Selection"
    assert len(ctx.objectives) >= 1
    assert len(ctx.constraints) >= 1

    # Check extracted budget constraint
    budget_const = next((c for c in ctx.constraints if "Budget" in c.name), None)
    assert budget_const is not None
    assert budget_const.threshold_value == 5000.0
    assert budget_const.operator == ComparisonOperator.LESS_THAN_OR_EQUAL

    # Check extracted latency constraint
    latency_const = next((c for c in ctx.constraints if "Latency" in c.name), None)
    assert latency_const is not None
    assert latency_const.threshold_value == 100.0


def test_decision_analyzer_with_explicit_objectives():
    analyzer = DecisionAnalyzer()
    from core.decision_intelligence.models import Objective, Constraint

    explicit_obj = [
        Objective(name="Security Compliance", category=ObjectiveType.COMPLIANCE, weight=0.6),
        Objective(name="User Experience", category=ObjectiveType.USER_EXPERIENCE, weight=0.4),
    ]
    explicit_const = [
        Constraint(name="SOC2 Type II", constraint_type=ConstraintType.HARD, metric="soc2_certified", threshold_value=True),
    ]

    ctx = analyzer.analyze_context(
        query="Evaluate cloud security vendors",
        explicit_objectives=explicit_obj,
        explicit_constraints=explicit_const,
    )

    assert len(ctx.objectives) == 2
    assert ctx.objectives[0].name == "Security Compliance"
    assert len(ctx.constraints) >= 1
    assert ctx.to_dict()["topic"] is not None
