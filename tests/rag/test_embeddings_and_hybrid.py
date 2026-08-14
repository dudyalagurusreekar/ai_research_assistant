"""Unit tests for GeminiEmbeddingProvider, BM25Retriever, RRF, and Reranker."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from core.rag.embeddings.provider import GeminiEmbeddingProvider, embedding_engine
from core.rag.retrieval.hybrid import BM25Retriever, CitationGenerator, RerankerEngine, SearchResultItem
from infrastructure.database.models.knowledge import DocumentChunk


def test_gemini_embedding_provider_dimensionality():
    provider = GeminiEmbeddingProvider(model_name="gemini-embedding-2", output_dimension=1536)
    embeddings = provider.generate_embeddings(["Quantum supremacy in 2026."])
    
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 1536

    # Test custom 768 dimensions option
    provider_768 = GeminiEmbeddingProvider(model_name="gemini-embedding-2", output_dimension=768)
    emb_768 = provider_768.generate_embeddings(["Multimodal embedding content."])
    assert len(emb_768[0]) == 768


def test_bm25_retriever():
    bm25 = BM25Retriever()
    c1 = DocumentChunk(id="c1", content="Superconducting qubits achieve quantum supremacy.", chunk_index=0)
    c2 = DocumentChunk(id="c2", content="Classical supercomputers simulate molecular dynamics.", chunk_index=1)
    c3 = DocumentChunk(id="c3", content="Quantum error correction uses surface codes.", chunk_index=2)

    results = bm25.search([c1, c2, c3], query="quantum supremacy qubits", top_k=2)
    assert len(results) == 2
    assert results[0][0].id == "c1"


def test_reranker_and_citation_generator():
    items = [
        SearchResultItem(
            chunk_id="chk1",
            document_id="doc1",
            document_title="Quantum.pdf",
            chunk_index=0,
            content="Superconducting quantum processors outperform classical computers.",
            score=0.8,
            citation="",
            metadata={},
        ),
        SearchResultItem(
            chunk_id="chk2",
            document_id="doc2",
            document_title="Biology.pdf",
            chunk_index=1,
            content="Gene editing using CRISPR Cas9 enzymes.",
            score=0.9,
            citation="",
            metadata={},
        ),
    ]

    reranked = RerankerEngine.rerank(items, query="quantum processors superconducting")
    assert reranked[0].chunk_id == "chk1"

    citation_tag = CitationGenerator.generate_citation("Quantum.pdf", 0, 0.95)
    assert citation_tag == "[Doc: Quantum.pdf | Chunk: 0 | Score: 0.95]"
