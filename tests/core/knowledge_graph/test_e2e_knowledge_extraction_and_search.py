"""End-to-End Test: Text/Document Knowledge Ingestion, Graph Building, and Hybrid Semantic Search."""

import pytest

from core.knowledge_graph import KnowledgeGraphEngine


def test_e2e_knowledge_extraction_and_search():
    engine = KnowledgeGraphEngine()

    research_paper = (
        "The Attention Mechanism is a fundamental method used by the Transformer model architecture. "
        "The Transformer is evaluated on the ImageNet benchmark and written by Vaswani et al."
    )

    added_nodes, added_edges = engine.ingest_text(research_paper, source_id="vaswani_2017")
    assert len(added_nodes) >= 3
    assert len(added_edges) >= 1

    # Hybrid Semantic Search
    res = engine.query("Where was the Transformer evaluated?")
    assert res.total_nodes_found >= 1
    assert any("imagenet" in n.canonical_name for n in res.matched_nodes)
