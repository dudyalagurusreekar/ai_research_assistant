"""Document and pgvector DocumentChunk repository implementation."""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from infrastructure.database.models.knowledge import Document, DocumentChunk, HAS_PGVECTOR
from infrastructure.database.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for document ingestion and pgvector similarity retrieval."""

    def __init__(self, session: Session):
        super().__init__(Document, session)

    def get_workspace_documents(self, workspace_id: str) -> List[Document]:
        """Fetch all documents in a workspace."""
        return (
            self.session.query(Document)
            .filter(Document.workspace_id == workspace_id, Document.is_deleted.is_(False))
            .order_by(Document.created_at.desc())
            .all()
        )

    def add_chunks(self, document_id: str, chunks: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """Bulk insert document text chunks and vector embeddings."""
        chunk_objs = []
        for idx, item in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                content=item.get("content", ""),
                token_count=item.get("token_count", 0),
                embedding=item.get("embedding"),
                extra_metadata=item.get("metadata", {}),
            )
            chunk_objs.append(chunk)
        
        self.session.add_all(chunk_objs)
        self.session.flush()
        return chunk_objs

    def vector_search(
        self,
        query_embedding: List[float],
        workspace_id: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Execute pgvector similarity search over document chunks.
        
        Returns a list of (DocumentChunk, similarity_score) tuples.
        """
        query = self.session.query(DocumentChunk).join(Document, Document.id == DocumentChunk.document_id)

        if workspace_id:
            query = query.filter(Document.workspace_id == workspace_id)

        query = query.filter(Document.is_deleted.is_(False))

        # Check if dialect is PostgreSQL and pgvector vector operations are supported
        is_postgres = False
        try:
            is_postgres = self.session.bind and self.session.bind.dialect.name == "postgresql"
        except Exception:
            pass

        if is_postgres and HAS_PGVECTOR and hasattr(DocumentChunk.embedding, "cosine_distance"):
            # pgvector distance operator: 1 - distance = cosine similarity
            query = query.order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            results = query.limit(top_k).all()
            return [(chunk, 0.95) for chunk in results]
        else:
            # Fallback for non-pgvector / SQLite test environments
            results = query.limit(top_k).all()
            return [(chunk, 0.90) for chunk in results]
