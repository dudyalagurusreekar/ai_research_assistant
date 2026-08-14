"""Unit tests for GraphQueryService natural language graph QA and pattern queries."""

import pytest

from core.knowledge_graph.components.query_service import GraphQueryService
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode, EntityType


def test_natural_language_query_service():
    graph = KnowledgeGraph()
    graph.add_node(EntityNode(name="Convolutional Neural Network", entity_type=EntityType.MODEL, aliases=["CNN"]))
    graph.add_node(EntityNode(name="Image Classification", entity_type=EntityType.TASK))

    qs = GraphQueryService(graph)

    res = qs.query_natural_language("What model architectures perform Image Classification?")
    assert len(res.matched_nodes) >= 1
    assert res.query_latency_ms >= 0.0
