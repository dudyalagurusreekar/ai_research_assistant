"""Unit tests for SemanticRetrievalEngine hybrid vector/keyword search and k-hop expansion."""

import pytest

from core.knowledge_graph.components.semantic_retrieval import SemanticRetrievalEngine
from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode, EntityType
from core.knowledge_graph.models.query import GraphQuery, SearchMode


def test_semantic_retrieval_search_and_khop_expansion():
    graph = KnowledgeGraph()
    n1 = graph.add_node(EntityNode(name="GPT-4", entity_type=EntityType.MODEL))
    n2 = graph.add_node(EntityNode(name="Transformer", entity_type=EntityType.CONCEPT))
    n3 = graph.add_node(EntityNode(name="Attention Mechanism", entity_type=EntityType.METHOD))

    graph.add_edge(RelationEdge(source_id=n1.node_id, target_id=n2.node_id, relation_type=RelationType.USES))
    graph.add_edge(RelationEdge(source_id=n2.node_id, target_id=n3.node_id, relation_type=RelationType.PART_OF))

    retrieval = SemanticRetrievalEngine(graph)

    query = GraphQuery(query_text="GPT-4 Transformer", max_hop_depth=2, limit=5)
    res = retrieval.search(query)

    assert len(res.matched_nodes) >= 2
    assert len(res.matched_edges) >= 1
    assert any(n.name == "GPT-4" for n in res.matched_nodes)
    assert any(n.name == "Attention Mechanism" for n in res.matched_nodes)
