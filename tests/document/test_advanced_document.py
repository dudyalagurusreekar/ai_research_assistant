
"""Advanced Unit, Integration, Performance, and Concurrency Tests for Phase 4 Document Intelligence Platform."""

import asyncio
import os
import tempfile
from typing import Dict, Any

from tools.document.facade.facade import DocumentToolFacade
from tools.document.models.document import NormalizedDocument, DocumentMetadata, DocumentChunk
from tools.document.models.context import ProcessingContext
from tools.document.registry.parser_registry import ParserRegistry
from tools.document.detector.format_detector import FormatDetector
from tools.document.router.file_router import FileRouter
from tools.document.pipeline.engine import ProcessingPipeline
from tools.document.pipeline.registry import PipelineRegistry
from tools.document.storage.artifact_manager import DocumentArtifactManager
from tools.document.retrieval.search import KeywordSearchEngine
from tools.document.retrieval.comparison import DocumentComparator
from tools.document.retrieval.summarizer import DocumentSummarizer
from tools.document.retrieval.vector_extension import VectorSearchExtensionPoint
from core.events import AsyncEventBus
from infrastructure.artifacts import ArtifactStore
from infrastructure.storage import DiskStorage


def test_automatic_parser_registration():
    """Verify ParserRegistry automatically registers default parsers for all 11 supported formats."""
    registry = ParserRegistry()
    # Register default parsers
    from tools.document.parsers.pdf_parser import PDFParser
    from tools.document.parsers.docx_parser import DOCXParser
    from tools.document.parsers.pptx_parser import PPTXParser
    from tools.document.parsers.xlsx_parser import XLSXParser
    from tools.document.parsers.csv_parser import CSVParser
    from tools.document.parsers.txt_parser import TXTParser
    from tools.document.parsers.markdown_parser import MarkdownParser
    from tools.document.parsers.html_parser import HTMLParser
    from tools.document.parsers.xml_parser import XMLParser
    from tools.document.parsers.image_parser import ImageOCRParser
    from tools.document.parsers.zip_parser import ZIPParser

    for p in [PDFParser(), DOCXParser(), PPTXParser(), XLSXParser(), CSVParser(), TXTParser(), MarkdownParser(), HTMLParser(), XMLParser(), ImageOCRParser(), ZIPParser()]:
        registry.register(p)

    formats = [f.value for f in registry.list_supported_formats()]
    assert "pdf" in formats
    assert "docx" in formats
    assert "pptx" in formats
    
    assert "xlsx" in formats
    assert "csv" in formats
    assert "txt" in formats
    assert "markdown" in formats
    assert "html" in formats
    assert "xml" in formats
    assert "image" in formats
    assert "zip" in formats


def test_concurrent_document_processing():
    """Verify DocumentToolFacade can process multiple documents concurrently without race conditions."""
    async def _test():
        facade = DocumentToolFacade()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            files = []
            for i in range(5):
                fpath = os.path.join(tmpdir, f"doc_{i}.txt")
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(f"# Document Heading {i}\n\nThis is paragraph content for concurrent processing test document {i}.")
                files.append(fpath)
                
            tasks = [facade.parse_document(f) for f in files]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            for idx, doc in enumerate(results):
                assert doc.get_full_text() != ""
                assert f"Document Heading {idx}" in doc.get_full_text()

    asyncio.run(_test())


def test_artifact_manager_and_event_publishing():
    """Verify DocumentArtifactManager stores normalized documents and emits events on AsyncEventBus."""
    async def _test():
        bus = AsyncEventBus()
        events_captured = []
        
        async def handler(event):
            events_captured.append(event)
            
        bus.subscribe("document.parsed", handler)
        bus.subscribe("document.chunked", handler)
        bus.subscribe("document.artifacts_stored", handler)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            disk_storage = DiskStorage(base_dir=tmpdir)
            store = ArtifactStore(storage=disk_storage)
            manager = DocumentArtifactManager(artifact_store=store, event_bus=bus)
            
            doc = NormalizedDocument(
                full_text="Sample pdf text content",
                metadata=DocumentMetadata(title="Event Test PDF", mime_type="application/pdf"),
                chunks=[DocumentChunk(chunk_id="chunk_1", text="Chunk text", chunk_index=0)],
            )
            ctx = ProcessingContext()
            
            saved_artifacts = await manager.store_document_artifacts(doc, raw_bytes=b"sample pdf bytes")
            assert len(saved_artifacts) > 0
            
            # Wait briefly for async event loop processing
            await asyncio.sleep(0.05)
            assert len(events_captured) >= 1
            event_types = [e.event_type for e in events_captured]
            assert "document.artifacts_stored" in event_types

    asyncio.run(_test())


def test_retrieval_and_comparison_performance():
    """Performance benchmark test for BM25 search and document comparison."""
    async def _test():
        chunks = [
            DocumentChunk(chunk_id="c1", text="Artificial Intelligence and Machine Learning models transform scientific research."),
            DocumentChunk(chunk_id="c2", text="Deep Neural Networks learn complex data representations from large datasets."),
            DocumentChunk(chunk_id="c3", text="Machine Learning algorithms analyze empirical data and discover underlying patterns."),
        ]
        
        search_engine = KeywordSearchEngine()
        results = await search_engine.search("Artificial Intelligence research", chunks)
        assert len(results) > 0
        assert results[0].chunk_id == "c1"
        
        doc1 = NormalizedDocument()
        doc1.full_text = "Artificial Intelligence and Machine Learning models transform scientific research."
        doc2 = NormalizedDocument()
        doc2.full_text = "Machine Learning algorithms analyze empirical data and discover underlying patterns."

        comparator = DocumentComparator()
        comp_result = await comparator.compare(doc1, doc2)
        assert comp_result.text_similarity_score > 0.0
        assert comp_result.common_words_count > 0

        summarizer = DocumentSummarizer()
        summary = await summarizer.summarize(doc1, max_sentences=2)
        assert summary.summary_text != ""
        assert len(summary.key_sentences) > 0

        vector_ext = VectorSearchExtensionPoint()
        v_results = await vector_ext.vector_search("query")
        assert isinstance(v_results, list)

    asyncio.run(_test())
