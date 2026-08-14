"""Integration tests for MemorySystem sync into Knowledge Graph."""

import pytest

from core.knowledge_graph import KnowledgeGraphEngine, MemorySystemKnowledgeIntegration
from tools.browser.memory.models import MemoryItem, MemoryType


def test_memory_system_knowledge_integration():
    kg_engine = KnowledgeGraphEngine()
    integration = MemorySystemKnowledgeIntegration(kg_engine)

    memory_item = MemoryItem(
        content="GitHub API rate limits occur after 5000 requests per hour",
        memory_type=MemoryType.SEMANTIC,
        importance=0.9,
    )

    node = integration.sync_memory_item(memory_item)
    assert node is not None
    assert kg_engine.graph.node_count == 1
    assert "GitHub API" in node.name
