"""Unit tests for master DecisionIntelligenceEngine."""

import pytest
from core.decision_intelligence.engine import DecisionIntelligenceEngine
from core.decision_intelligence.models import DecisionRequest, RecommendationType


def test_decision_engine_e2e_pipeline():
    engine = DecisionIntelligenceEngine()

    req = DecisionRequest(
        user_query="Evaluate backend framework for high-throughput AI API services",
        topic="API Framework Selection",
        preset_options=[
            {"title": "FastAPI Async Engine", "estimated_cost": 500.0, "implementation_complexity": "low"},
            {"title": "Spring Boot Microservices", "estimated_cost": 2500.0, "implementation_complexity": "high"},
            {"title": "Go Fiber Service Engine", "estimated_cost": 800.0, "implementation_complexity": "medium"},
        ],
    )

    res = engine.process_decision_request(req)

    assert res.status == "success"
    assert res.execution_time_ms > 0.0
    assert res.report is not None
    assert res.report.topic == "API Framework Selection"
    assert res.report.top_recommendation is not None
    assert res.report.top_recommendation.recommendation_type == RecommendationType.PRIMARY_RECOMMENDATION
    assert len(res.report.all_recommendations) == 3
    assert len(res.report.human_choice_boundaries) >= 1
