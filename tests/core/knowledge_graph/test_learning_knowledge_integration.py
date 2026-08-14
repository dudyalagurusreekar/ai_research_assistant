"""Integration tests for Continuous Learning Engine experience sync with Knowledge Graph."""

import pytest

from core.knowledge_graph import KnowledgeGraphEngine, LearningKnowledgeIntegration
from core.learning.engine import ContinuousLearningEngine


def test_learning_knowledge_integration():
    kg_engine = KnowledgeGraphEngine()
    learning_engine = ContinuousLearningEngine()
    integration = LearningKnowledgeIntegration(kg_engine)

    learning_engine.record_experience(
        query="Optimize Graph Reasoning",
        intent="multi_step_research",
        complexity_score=4,
        selected_tools=["graph_tool"],
        excluded_tools=[],
        dag_nodes_count=3,
        dag_edges_count=2,
        parallel_waves=1,
        execution_latency_ms=120.0,
    )

    synced_count = integration.sync_experience_store(learning_engine.store)
    assert synced_count >= 1
    assert kg_engine.graph.node_count >= 1
