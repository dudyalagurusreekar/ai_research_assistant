"""Integration tests for Multi-Agent Framework workspace sync into Knowledge Graph."""

import pytest

from core.collaboration.components.workspace import SharedWorkspace
from core.knowledge_graph import CollaborationKnowledgeIntegration, KnowledgeGraphEngine


def test_collaboration_knowledge_integration():
    kg_engine = KnowledgeGraphEngine()
    integration = CollaborationKnowledgeIntegration(kg_engine)

    workspace = SharedWorkspace()
    workspace.set("research_summary", "Multi-agent collaboration synthesis text.", artifact_type="text")
    workspace.set("data_stats", {"row_count": 50}, artifact_type="data")

    synced_count = integration.sync_shared_workspace(workspace)
    assert synced_count == 2
    assert kg_engine.graph.node_count == 2
