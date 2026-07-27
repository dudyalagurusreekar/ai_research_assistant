"""Unit tests for KeywordSearchEngine, DocumentComparator, DocumentSummarizer, and VectorSearchExtensionPoint."""

import asyncio
from tools.document.models.document import NormalizedDocument, DocumentChunk
from tools.document.retrieval.search import KeywordSearchEngine
from tools.document.retrieval.comparison import DocumentComparator
from tools.document.retrieval.summarizer import DocumentSummarizer
from tools.document.retrieval.vector_extension import VectorSearchExtensionPoint


def test_keyword_search_engine():
    async def _test():
        engine = KeywordSearchEngine()
        chunks = [
            DocumentChunk(chunk_id="c1", text="Quantum computing principles and qubit superposition."),
            DocumentChunk(chunk_id="c2", text="Artificial intelligence deep learning neural networks."),
            DocumentChunk(chunk_id="c3", text="Quantum entanglement and quantum gate circuits."),
        ]
        results = await engine.search(query="quantum computing", documents_or_chunks=chunks, top_k=2)

        assert len(results) > 0
        assert results[0].chunk_id in ["c1", "c3"]
        assert results[0].score > 0.0

    asyncio.run(_test())


def test_document_comparator():
    async def _test():
        comparator = DocumentComparator()

        doc1 = NormalizedDocument()
        doc1.full_text = "Quantum computing uses qubits to perform complex calculations."
        doc1.add_section("Introduction", level=1)

        doc2 = NormalizedDocument()
        doc2.full_text = "Quantum computing relies on qubit state superposition and entanglement."
        doc2.add_section("Overview", level=1)

        res = await comparator.compare(doc1, doc2)
        assert res.text_similarity_score > 0.0
        assert res.common_words_count > 0

    asyncio.run(_test())


def test_document_summarizer():
    async def _test():
        summarizer = DocumentSummarizer()
        doc = NormalizedDocument()
        doc.full_text = (
            "Document Intelligence Platform transforms files into structured knowledge. "
            "It supports PDF, DOCX, XLSX, and images using Clean Architecture. "
            "The processing pipeline cleans text and extracts semantic chunks. "
            "Artifact manager persists extracted data into shared storage."
        )
        doc.metadata.title = "Platform Architecture"
        summary = await summarizer.summarize(doc, max_sentences=2)

        assert summary.summary_text != ""
        assert len(summary.key_sentences) <= 2
        assert len(summary.key_terms) > 0

    asyncio.run(_test())


def test_vector_extension_point():
    async def _test():
        vector_ext = VectorSearchExtensionPoint()
        doc = NormalizedDocument()
        res_index = await vector_ext.embed_and_index(doc)
        assert res_index is True
        res_search = await vector_ext.vector_search("test query")
        assert res_search == []

    asyncio.run(_test())
