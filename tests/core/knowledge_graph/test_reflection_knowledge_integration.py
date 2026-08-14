"""Integration tests for Reflection Engine decision logging in Knowledge Graph."""

import pytest

from core.knowledge_graph import KnowledgeGraphEngine, ReflectionKnowledgeIntegration
from core.reflection.models.reflection import ReflectionAction, ReflectionDecision


def test_reflection_knowledge_integration():
    kg_engine = KnowledgeGraphEngine()
    integration = ReflectionKnowledgeIntegration(kg_engine)

    decision = ReflectionDecision(action=ReflectionAction.PROCEED, rationale="DAG validated")

    integration.record_reflection_decision(decision, query="Benchmark Query")
    assert kg_engine.graph.node_count == 1
    assert kg_engine.graph.find_node_by_name("ReflectionDecision:proceed") is not None
