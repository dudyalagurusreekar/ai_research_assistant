"""Unit tests for GraphStorage persistence, file saving, and loading."""

import pytest
import tempfile

from core.knowledge_graph.components.graph_storage import GraphStorage
from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode, EntityType


def test_graph_storage_save_and_load(tmp_path):
    graph = KnowledgeGraph()
    n1 = graph.add_node(EntityNode(name="PyTorch", entity_type=EntityType.TOOL))
    n2 = graph.add_node(EntityNode(name="CUDA", entity_type=EntityType.TOOL))
    graph.add_edge(RelationEdge(source_id=n1.node_id, target_id=n2.node_id, relation_type=RelationType.USES))

    storage = GraphStorage(graph, storage_dir=str(tmp_path))
    file_path = storage.save_to_file("test_kg.json")

    assert file_path.exists()

    # Create new graph and load back
    new_graph = KnowledgeGraph()
    new_storage = GraphStorage(new_graph, storage_dir=str(tmp_path))
    assert new_storage.load_from_file("test_kg.json") is True

    assert new_graph.node_count == 2
    assert new_graph.edge_count == 1
    assert new_graph.find_node_by_name("PyTorch") is not None
