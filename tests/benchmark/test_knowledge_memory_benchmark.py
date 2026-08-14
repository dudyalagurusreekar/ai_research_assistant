"""Benchmark test suite for Sprint 11 Knowledge Graph & Memory Platform performance and scaling."""

import time
import pytest
import tempfile
from core.knowledge_graph.engine import KnowledgeGraphEngine
from core.knowledge_graph.models.node import EntityNode, EntityType
from core.knowledge_graph.models.edge import RelationEdge, RelationType


@pytest.fixture
def temp_kg_engine():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = KnowledgeGraphEngine(storage_dir=tmpdir)
        yield engine


def test_entity_extraction_throughput_benchmark(temp_kg_engine):
    engine = temp_kg_engine
    sample_text = (
        "Transformer architecture built on PyTorch framework. BERT model evaluated on SQuAD dataset by Vaswani et al. "
        "ARA version 1.0 achieves 98% accuracy on benchmark tests using DeepLearning algorithms."
    )

    start_time = time.perf_counter()
    iterations = 20
    for i in range(iterations):
        engine.ingest_text(sample_text, source_id=f"text_{i}")
    elapsed = time.perf_counter() - start_time

    texts_per_sec = iterations / elapsed
    assert texts_per_sec > 10, f"Extraction throughput too low: {texts_per_sec:.2f} texts/sec"
    assert engine.graph.node_count >= 5


def test_large_graph_scaling_and_pathfinding_benchmark(temp_kg_engine):
    engine = temp_kg_engine
    graph = engine.graph

    # Build 100-node graph chain: N0 -> N1 -> N2 -> ... -> N99
    nodes = [
        EntityNode(name=f"Concept_{i}", canonical_name=f"concept_{i}", entity_type=EntityType.CONCEPT)
        for i in range(100)
    ]
    for n in nodes:
        graph.add_node(n)

    for i in range(99):
        edge = RelationEdge(
            source_id=nodes[i].node_id,
            target_id=nodes[i + 1].node_id,
            relation_type=RelationType.RELATED_TO,
        )
        graph.add_edge(edge)

    # Benchmark pathfinding
    start_time = time.perf_counter()
    paths = engine.find_path("Concept_0", "Concept_3", max_depth=4)
    path_time_ms = (time.perf_counter() - start_time) * 1000

    assert len(paths) >= 1
    assert path_time_ms < 100, f"Pathfinding latency too high: {path_time_ms:.2f} ms"

    # Benchmark NetworkX PageRank centrality calculation on 100 nodes
    start_time = time.perf_counter()
    centrality = engine.compute_centrality(metric="pagerank")
    pagerank_time_ms = (time.perf_counter() - start_time) * 1000

    assert len(centrality) == 100
    assert pagerank_time_ms < 500, f"PageRank calculation latency too high: {pagerank_time_ms:.2f} ms"


def test_memory_recall_latency_benchmark(temp_kg_engine):
    engine = temp_kg_engine

    # Store 100 memory items
    for i in range(100):
        engine.store_memory("user", "usr_bench", f"key_{i}", f"Value description for item {i}", importance=0.5)

    start_time = time.perf_counter()
    results = engine.recall_memory("user", "usr_bench", "item 50")
    recall_time_ms = (time.perf_counter() - start_time) * 1000

    assert len(results) >= 1
    assert recall_time_ms < 50, f"Memory recall latency too high: {recall_time_ms:.2f} ms"
