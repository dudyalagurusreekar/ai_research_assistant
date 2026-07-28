"""DocumentToolFacade - Single Public Entry Point for Document Intelligence Platform."""

import os
from typing import Optional, Union, BinaryIO, List, Any
from core.interfaces.event_bus import IEventBus
from core.events.bus import AsyncEventBus
from core.models.event import Event
from tools.document.config import DocumentConfig
from tools.document.interfaces.router import IFileRouter
from tools.document.interfaces.parser import IParserRegistry
from tools.document.interfaces.pipeline import IProcessingPipeline, IPipelineRegistry
from tools.document.interfaces.artifact_manager import IDocumentArtifactManager
from tools.document.interfaces.retrieval import IRetrievalEngine, IDocumentComparator, IDocumentSummarizer
from tools.document.models.document import NormalizedDocument, DocumentMetadata, DocumentTable, DocumentImage, DocumentChunk
from tools.document.models.context import ProcessingContext
from tools.document.models.retrieval import SearchResult, DocumentComparisonResult, DocumentSummary
from tools.document.registry.parser_registry import ParserRegistry
from tools.document.router.file_router import FileRouter
from tools.document.pipeline.registry import PipelineRegistry
from tools.document.pipeline.engine import ProcessingPipeline
from tools.document.pipeline.cleaner import CleanerStep
from tools.document.pipeline.header_footer import HeaderFooterStep
from tools.document.pipeline.metadata_extractor import MetadataExtractorStep
from tools.document.pipeline.heading_detector import HeadingDetectorStep
from tools.document.pipeline.table_extractor import TableExtractorStep
from tools.document.pipeline.image_extractor import ImageExtractorStep
from tools.document.pipeline.chunker import ChunkerStep
from tools.document.storage.artifact_manager import DocumentArtifactManager
from tools.document.retrieval.search import KeywordSearchEngine
from tools.document.retrieval.comparison import DocumentComparator
from tools.document.retrieval.summarizer import DocumentSummarizer
from tools.document.parsers import (
    PDFParser,
    DOCXParser,
    PPTXParser,
    XLSXParser,
    CSVParser,
    TXTParser,
    MarkdownParser,
    HTMLParser,
    XMLParser,
    ImageOCRParser,
    ZIPParser,
)
from infrastructure.logging.logger import StructuredLogger


class DocumentToolFacade:
    """Single Public Entry Point Facade for the Document Intelligence Platform.

    Provides a clean, unified public interface for parsing, processing, extracting, chunking,
    searching, comparing, and summarizing documents.
    """

    def __init__(
        self,
        config: Optional[DocumentConfig] = None,
        parser_registry: Optional[IParserRegistry] = None,
        file_router: Optional[IFileRouter] = None,
        pipeline_registry: Optional[IPipelineRegistry] = None,
        pipeline: Optional[IProcessingPipeline] = None,
        artifact_manager: Optional[IDocumentArtifactManager] = None,
        retrieval_engine: Optional[IRetrievalEngine] = None,
        comparator: Optional[IDocumentComparator] = None,
        summarizer: Optional[IDocumentSummarizer] = None,
        event_bus: Optional[IEventBus] = None,
    ) -> None:
        self._logger = StructuredLogger("DocumentToolFacade")
        self.config = config or DocumentConfig()
        self.event_bus = event_bus or AsyncEventBus()

        # 1. Setup Parser Registry & Register All Default Parsers
        self.parser_registry = parser_registry or ParserRegistry()
        if not parser_registry:
            self._register_default_parsers()

        # 2. Setup File Router
        self.file_router = file_router or FileRouter(parser_registry=self.parser_registry)

        # 3. Setup Pipeline & Pipeline Registry
        if not pipeline_registry:
            self.pipeline_registry = PipelineRegistry()
            self._register_default_pipeline_steps()
        else:
            self.pipeline_registry = pipeline_registry

        self.pipeline = pipeline or ProcessingPipeline(pipeline_registry=self.pipeline_registry)

        # 4. Setup Artifact Manager
        self.artifact_manager = artifact_manager or DocumentArtifactManager(event_bus=self.event_bus)

        # 5. Setup Retrieval, Comparison, and Summarization
        self.retrieval_engine = retrieval_engine or KeywordSearchEngine()
        self.comparator = comparator or DocumentComparator()
        self.summarizer = summarizer or DocumentSummarizer()

    def _register_default_parsers(self) -> None:
        """Register default set of 11 format parsers with ParserRegistry."""
        self.parser_registry.register(PDFParser())
        self.parser_registry.register(DOCXParser())
        self.parser_registry.register(PPTXParser())
        self.parser_registry.register(XLSXParser())
        self.parser_registry.register(CSVParser())
        self.parser_registry.register(TXTParser())
        self.parser_registry.register(MarkdownParser())
        self.parser_registry.register(HTMLParser())
        self.parser_registry.register(XMLParser())
        self.parser_registry.register(ImageOCRParser())
        self.parser_registry.register(ZIPParser())

    def _register_default_pipeline_steps(self) -> None:
        """Register default sequence of processing steps."""
        self.pipeline_registry.register_step(CleanerStep())
        self.pipeline_registry.register_step(HeaderFooterStep())
        self.pipeline_registry.register_step(MetadataExtractorStep())
        self.pipeline_registry.register_step(HeadingDetectorStep())
        self.pipeline_registry.register_step(TableExtractorStep())
        self.pipeline_registry.register_step(ImageExtractorStep())
        self.pipeline_registry.register_step(ChunkerStep())

    async def parse_document(
        self,
        source: Union[str, bytes, BinaryIO],
        mime_type: Optional[str] = None,
        filename: Optional[str] = None,
        context: Optional[ProcessingContext] = None,
    ) -> NormalizedDocument:
        """Parse raw file source into a fully processed NormalizedDocument.

        Validates, detects format, parses, executes processing pipeline, and persists artifacts.
        """
        ctx = context or ProcessingContext(config=self.config)
        try:
            # 1. Route & parse initial document
            doc = await self.file_router.route_and_parse(
                source=source,
                mime_type=mime_type,
                filename=filename,
                context=ctx,
            )

            # 2. Execute processing pipeline
            processed_doc = await self.pipeline.execute(doc, ctx)

            # 3. Store artifacts
            raw_bytes = source if isinstance(source, bytes) else (
                open(source, "rb").read() if isinstance(source, str) and os.path.exists(source) else None
            )
            await self.artifact_manager.store_document_artifacts(processed_doc, raw_bytes=raw_bytes)

            # 4. Emit Domain Events
            if self.event_bus:
                await self.event_bus.publish(
                    Event(
                        event_type="document.parsed",
                        source="DocumentToolFacade",
                        payload={
                            "document_id": processed_doc.document_id,
                            "file_name": processed_doc.metadata.file_name,
                            "word_count": processed_doc.metadata.word_count,
                            "chunk_count": len(processed_doc.chunks),
                        },
                    )
                )
                if processed_doc.chunks:
                    await self.event_bus.publish(
                        Event(
                            event_type="document.chunked",
                            source="DocumentToolFacade",
                            payload={
                                "document_id": processed_doc.document_id,
                                "chunk_count": len(processed_doc.chunks),
                            },
                        )
                    )

            self._logger.info(f"Successfully parsed and processed document '{processed_doc.document_id}'")
            return processed_doc

        except Exception as e:
            self._logger.error(f"Failed to parse document: {e}")
            if self.event_bus:
                await self.event_bus.publish(
                    Event(
                        event_type="document.failed",
                        source="DocumentToolFacade",
                        payload={"filename": filename, "error": str(e)},
                    )
                )
            raise e

    async def read_document(self, source: Union[str, bytes, BinaryIO]) -> str:
        """Extract full plain text content from document."""
        doc = await self.parse_document(source)
        return doc.full_text

    async def extract_text(self, source: Union[str, bytes, BinaryIO]) -> str:
        """Alias for read_document."""
        return await self.read_document(source)

    async def extract_tables(self, source: Union[str, bytes, BinaryIO]) -> List[DocumentTable]:
        """Extract all structured tables from document."""
        doc = await self.parse_document(source)
        return doc.tables

    async def extract_images(self, source: Union[str, bytes, BinaryIO]) -> List[DocumentImage]:
        """Extract all embedded images from document."""
        doc = await self.parse_document(source)
        return doc.images

    async def get_metadata(self, source: Union[str, bytes, BinaryIO]) -> DocumentMetadata:
        """Extract document metadata header."""
        doc = await self.parse_document(source)
        return doc.metadata

    async def chunk_document(
        self,
        source: Union[str, bytes, BinaryIO],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[DocumentChunk]:
        """Extract semantic chunks from document with optional size overrides."""
        ctx = ProcessingContext(config=self.config)
        if chunk_size:
            ctx.config.default_chunk_size = chunk_size
        if chunk_overlap:
            ctx.config.default_chunk_overlap = chunk_overlap

        doc = await self.parse_document(source, context=ctx)
        return doc.chunks

    async def search_documents(
        self,
        query: str,
        documents_or_chunks: List[Any],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Perform ranked keyword search across documents or chunks."""
        return await self.retrieval_engine.search(query, documents_or_chunks, top_k=top_k)

    async def compare_documents(
        self,
        doc_a: NormalizedDocument,
        doc_b: NormalizedDocument,
    ) -> DocumentComparisonResult:
        """Compare two NormalizedDocument objects for similarity and structural diffs."""
        return await self.comparator.compare(doc_a, doc_b)

    async def summarize_document(
        self,
        source: Union[str, bytes, BinaryIO],
        max_sentences: int = 5,
    ) -> DocumentSummary:
        """Extract key sentences and structural summary from document."""
        doc = await self.parse_document(source)
        return await self.summarizer.summarize(doc, max_sentences=max_sentences)
