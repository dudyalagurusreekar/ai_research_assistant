"""Retrieval, Comparison, Summarization, and Vector Extension Interfaces."""

from abc import ABC, abstractmethod
from typing import List, Any
from tools.document.models.document import NormalizedDocument
from tools.document.models.retrieval import SearchResult, DocumentComparisonResult, DocumentSummary


class IRetrievalEngine(ABC):
    """Interface for keyword search and ranked retrieval over normalized chunks."""

    @abstractmethod
    async def search(
        self,
        query: str,
        documents_or_chunks: List[Any],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Perform ranked keyword/BM25 search across documents or chunks."""


class IDocumentComparator(ABC):
    """Interface for comparing two NormalizedDocument objects."""

    @abstractmethod
    async def compare(
        self,
        doc_a: NormalizedDocument,
        doc_b: NormalizedDocument,
    ) -> DocumentComparisonResult:
        """Compare structural and text differences between two documents."""


class IDocumentSummarizer(ABC):
    """Interface for extractive document summarization without LLM decision-making."""

    @abstractmethod
    async def summarize(
        self,
        document: NormalizedDocument,
        max_sentences: int = 5,
    ) -> DocumentSummary:
        """Extract key sentences and structural summary from document."""


class IVectorSearchEngine(ABC):
    """Extension Point Interface for future Semantic Vector Retrieval."""

    @abstractmethod
    async def embed_and_index(self, document: NormalizedDocument) -> bool:
        """Extension point to embed chunks and index in vector store."""

    @abstractmethod
    async def vector_search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Extension point to search indexed chunks via vector embeddings."""
