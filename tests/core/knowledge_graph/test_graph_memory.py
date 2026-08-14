"""Unit tests for GraphMemoryManager decay scoring and low-confidence node pruning."""

import pytest

from core.knowledge_graph.components.graph_memory import GraphMemoryManager
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode, EntityType


def test_memory_decay_and_pruning():
    graph = KnowledgeGraph()
    n1 = graph.add_node(EntityNode(name="HighConfidence", confidence_score=0.95, decay_score=0.9))
    n2 = graph.add_node(EntityNode(name="LowConfidence", confidence_score=0.15, decay_score=0.1))

    memory_mgr = GraphMemoryManager(graph, prune_threshold=0.25)

    updated_count = memory_mgr.apply_decay()
    assert updated_count == 2

    pn, pe = memory_mgr.prune_low_confidence_nodes()
    assert pn == 1
    assert graph.node_count == 1
    assert graph.find_node_by_name("HighConfidence") is not None
    assert graph.find_node_by_name("LowConfidence") is None
