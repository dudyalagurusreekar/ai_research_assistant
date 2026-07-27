"""VectorSearchExtensionPoint implementation serving as extension point for future vector retrieval."""

from typing import List
from tools.document.interfaces.retrieval import IVectorSearchEngine
from tools.document.models.document import NormalizedDocument
from tools.document.models.retrieval import SearchResult
from infrastructure.logging.logger import StructuredLogger


class VectorSearchExtensionPoint(IVectorSearchEngine):
    """Extension Point implementation for semantic vector embeddings and vector index searching."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("VectorSearchExtensionPoint")

    async def embed_and_index(self, document: NormalizedDocument) -> bool:
        """Extension point stub to embed chunks and index in vector store."""
        self._logger.info(
            f"[Extension Point] Vector search indexing stub called for document '{document.document_id}' "
            f"({len(document.chunks)} chunks)."
        )
        return True

    async def vector_search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Extension point stub to search indexed chunks via vector embeddings."""
        self._logger.info(f"[Extension Point] Vector search stub called for query '{query}'.")
        return []
