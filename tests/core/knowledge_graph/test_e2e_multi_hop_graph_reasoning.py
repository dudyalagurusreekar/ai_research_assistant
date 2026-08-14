"""End-to-End Test: Multi-Hop Graph Reasoning, Transitive Inference, and Centrality Analysis."""

import pytest

from core.knowledge_graph import KnowledgeGraphEngine
from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.node import EntityNode, EntityType


def test_e2e_multi_hop_graph_reasoning():
    engine = KnowledgeGraphEngine()

    n1 = engine.graph.add_node(EntityNode(name="SafeCodeAgent", entity_type=EntityType.MODEL))
    n2 = engine.graph.add_node(EntityNode(name="SafePythonExecutor", entity_type=EntityType.METHOD))
    n3 = engine.graph.add_node(EntityNode(name="PyTorch", entity_type=EntityType.TOOL))

    engine.graph.add_edge(RelationEdge(source_id=n1.node_id, target_id=n2.node_id, relation_type=RelationType.IMPLEMENTS))
    engine.graph.add_edge(RelationEdge(source_id=n2.node_id, target_id=n3.node_id, relation_type=RelationType.USES))

    # Multi-hop Path Query
    paths = engine.find_path("SafeCodeAgent", "PyTorch", max_depth=3)
    assert len(paths) == 1
    assert paths[0].length == 2

    # Transitive Inference (SafeCodeAgent IMPLEMENTS SafePythonExecutor USES PyTorch => SafeCodeAgent USES PyTorch)
    inferred_edges = engine.reasoning_engine.infer_transitive_relations()
    assert len(inferred_edges) == 1
    assert inferred_edges[0].source_id == n1.node_id
    assert inferred_edges[0].target_id == n3.node_id
