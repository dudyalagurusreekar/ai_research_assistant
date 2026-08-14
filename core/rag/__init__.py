"""ARA Sprint 4 Enterprise RAG & Document Intelligence Package."""

from core.rag.parsers.base import AbstractDocumentParser, ParsedDocument, ParsedSection, ParsedTable
from core.rag.parsers.multiformat import parser_registry, DocumentParserRegistry
from core.rag.chunking.chunker import SemanticChunker, TableStructureChunker, DocumentChunkData
from core.rag.embeddings.provider import embedding_engine, GeminiEmbeddingProvider, MockEmbeddingProvider
from core.rag.retrieval.hybrid import HybridRetriever, BM25Retriever, RerankerEngine, CitationGenerator, SearchResultItem
from core.rag.pipeline import RAGPipeline, GroundedQAEngine

__all__ = [
    "AbstractDocumentParser",
    "ParsedDocument",
    "ParsedSection",
    "ParsedTable",
    "parser_registry",
    "DocumentParserRegistry",
    "SemanticChunker",
    "TableStructureChunker",
    "DocumentChunkData",
    "embedding_engine",
    "GeminiEmbeddingProvider",
    "MockEmbeddingProvider",
    "HybridRetriever",
    "BM25Retriever",
    "RerankerEngine",
    "CitationGenerator",
    "SearchResultItem",
    "RAGPipeline",
    "GroundedQAEngine",
]
