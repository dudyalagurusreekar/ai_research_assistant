"""Unit tests for GraphBuilder construction, entity resolution, and deduplication."""

import pytest

from core.knowledge_graph.components.graph_builder import GraphBuilder
from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode, EntityType


def test_graph_builder_deduplication_and_linking():
    graph = KnowledgeGraph()
    builder = GraphBuilder(graph)

    node1 = EntityNode(name="Transformer", entity_type=EntityType.MODEL)
    node2 = EntityNode(name="transformer", entity_type=EntityType.MODEL, aliases=["transformer_arch"])
    node3 = EntityNode(name="Attention", entity_type=EntityType.METHOD)

    edge1 = RelationEdge(source_id=node1.node_id, target_id=node3.node_id, relation_type=RelationType.USES)

    added_nodes, added_edges = builder.build_from_extraction([node1, node2, node3], [edge1])

    # Node 1 and Node 2 should resolve to same canonical node
    assert graph.node_count == 2
    assert graph.edge_count == 1
    canon_node = graph.find_node_by_name("Transformer")
    assert "transformer_arch" in canon_node.aliases
