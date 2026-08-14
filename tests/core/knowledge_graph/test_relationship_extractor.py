"""Unit tests for RelationshipExtractor predicate extraction and rule heuristics."""

import pytest

from core.knowledge_graph.components.entity_extractor import EntityExtractor
from core.knowledge_graph.components.relationship_extractor import RelationshipExtractor
from core.knowledge_graph.models.edge import RelationType


def test_extract_relationships_from_text():
    text = "The ResNet model evaluates on the ImageNet dataset using PyTorch framework."
    ent_extractor = EntityExtractor()
    rel_extractor = RelationshipExtractor()

    nodes = ent_extractor.extract_from_text(text)
    edges = rel_extractor.extract_relationships(text, nodes)

    assert len(edges) >= 1
    rel_types = [e.relation_type for e in edges]
    assert (RelationType.EVALUATES_ON in rel_types) or (RelationType.USES in rel_types) or (RelationType.RELATED_TO in rel_types)
