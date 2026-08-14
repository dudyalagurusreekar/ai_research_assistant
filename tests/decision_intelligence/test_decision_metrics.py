"""Unit tests for DecisionMetricsEngine."""

import pytest
from core.decision_intelligence.metrics import DecisionMetricsEngine


def test_decision_metrics_recording():
    metrics = DecisionMetricsEngine()
    metrics.reset()

    metrics.record_evaluation(
        success=True,
        latency_ms=120.0,
        option_count=3,
        evidence_count=5,
        pareto_count=2,
        top_confidence=0.85,
        top_risk=1.2,
    )

    summary = metrics.get_summary()
    assert summary["total_requests"] == 1
    assert summary["successful_requests"] == 1
    assert summary["avg_latency_ms"] == 120.0
    assert summary["total_options_evaluated"] == 3
    assert summary["avg_confidence_score"] == 0.85
    assert summary["avg_risk_score"] == 1.2
