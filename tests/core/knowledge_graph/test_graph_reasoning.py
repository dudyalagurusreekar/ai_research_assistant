"""Unit tests for GraphReasoningEngine pathfinding, transitive inference, and PageRank."""

import pytest

from core.knowledge_graph.components.graph_reasoning import GraphReasoningEngine
from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode, EntityType


def test_pathfinding_and_centrality():
    graph = KnowledgeGraph()
    n1 = graph.add_node(EntityNode(name="NodeA", entity_type=EntityType.CONCEPT))
    n2 = graph.add_node(EntityNode(name="NodeB", entity_type=EntityType.CONCEPT))
    n3 = graph.add_node(EntityNode(name="NodeC", entity_type=EntityType.CONCEPT))

    graph.add_edge(RelationEdge(source_id=n1.node_id, target_id=n2.node_id, relation_type=RelationType.IMPLEMENTS))
    graph.add_edge(RelationEdge(source_id=n2.node_id, target_id=n3.node_id, relation_type=RelationType.USES))

    reasoning = GraphReasoningEngine(graph)

    # 1. Multi-hop Pathfinding
    paths = reasoning.find_paths(n1.node_id, n3.node_id, max_depth=3)
    assert len(paths) == 1
    assert paths[0].length == 2

    # 2. Transitive Inference
    inferred = reasoning.infer_transitive_relations()
    assert len(inferred) == 1
    assert inferred[0].relation_type == RelationType.USES

    # 3. Node Centrality
    scores = reasoning.compute_node_centrality()
    assert len(scores) == 3
    assert n3.node_id in scores
