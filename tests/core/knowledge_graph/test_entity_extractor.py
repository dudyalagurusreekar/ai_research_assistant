"""Unit tests for EntityExtractor text and structured data extraction."""

import pytest

from core.knowledge_graph.components.entity_extractor import EntityExtractor
from core.knowledge_graph.models.node import EntityType


def test_extract_entities_from_text():
    extractor = EntityExtractor()
    text = (
        "The Transformer architecture was evaluated on the ImageNet benchmark dataset. "
        "The PyTorch framework achieved 95% accuracy metric."
    )

    nodes = extractor.extract_from_text(text)
    assert len(nodes) >= 3

    node_names = [n.name.lower() for n in nodes]
    assert any("transformer" in name for name in node_names)
    assert any("imagenet" in name for name in node_names)
    assert any("pytorch" in name for name in node_names)


def test_extract_entities_from_structured_data():
    extractor = EntityExtractor()
    data = {
        "dataset_name": "ImageNet",
        "model_name": "ResNet-50",
        "accuracy_score": 0.92,
        "latency_ms": 12.5,
    }

    nodes = extractor.extract_from_structured_data(data)
    assert len(nodes) == 4

    types = [n.entity_type for n in nodes]
    assert EntityType.METRIC in types
