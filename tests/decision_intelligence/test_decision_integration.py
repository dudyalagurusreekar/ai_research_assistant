"""Integration tests for DecisionSubsystemIntegration with all 8 core ARA subsystems."""

import pytest
from core.decision_intelligence.engine import DecisionIntelligenceEngine
from core.decision_intelligence.integration import DecisionSubsystemIntegration
from core.decision_intelligence.models import DecisionRequest


def test_integration_with_planner():
    adapter = DecisionSubsystemIntegration()
    plan_ctx = {"query": "Evaluate Cloud Architecture", "plan_id": "p123"}
    res = adapter.enhance_plan_with_decision_support(plan_ctx)
    assert res["plan_id"] == "p123"
    assert "recommended_strategy" in res
    assert res["decision_confidence"] > 0.0


def test_integration_with_reflection():
    adapter = DecisionSubsystemIntegration()
    feedback = {"quality_score": 0.45}
    res = adapter.evaluate_decision_quality("report_001", feedback)
    assert res["replanning_required"] is True
    assert res["reflection_status"] == "CORRECTED"


def test_integration_with_learning():
    adapter = DecisionSubsystemIntegration()
    req = DecisionRequest(user_query="Select DB")
    d_res = adapter.engine.process_decision_request(req)
    res = adapter.record_decision_experience(d_res, {"rating": 5.0})
    assert res["status"] == "recorded"


def test_integration_with_knowledge_graph():
    adapter = DecisionSubsystemIntegration()
    req = DecisionRequest(user_query="Select Architecture")
    d_res = adapter.engine.process_decision_request(req)
    res = adapter.ingest_decision_tree_to_knowledge_graph(d_res)
    assert res["status"] == "success"
    assert res["nodes_ingested"] >= 1


def test_integration_with_data_intelligence():
    adapter = DecisionSubsystemIntegration()
    res = adapter.synthesize_data_intelligence({})
    assert "data_intelligence_metrics" in res
    assert len(res["data_intelligence_metrics"]) >= 1


def test_integration_with_multi_agent():
    adapter = DecisionSubsystemIntegration()
    res = adapter.convene_multi_agent_deliberation("Evaluate AI Agents", [])
    assert res["status"] == "deliberation_completed"
    assert "agent_consensus" in res


def test_integration_with_browser():
    adapter = DecisionSubsystemIntegration()
    res = adapter.verify_evidence_via_browser("PostgreSQL vs MongoDB")
    assert "browser_evidence" in res
    assert len(res["browser_evidence"]) >= 1


def test_integration_with_universal_connectors():
    adapter = DecisionSubsystemIntegration()
    res = adapter.fetch_enterprise_connector_context(["github", "jira", "notion"])
    assert "connector_data" in res
    assert len(res["connector_data"]) == 3
