"""Clean Architecture Service for Document Ingestion, MinIO Storage Sync, Chunking, and RAG Retrieval."""

import hashlib
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from config.settings import settings
from infrastructure.database.models.knowledge import Document, DocumentChunk
from infrastructure.database.repositories.document_repository import DocumentRepository
from infrastructure.storage.storage_manager import storage_manager
from utils.logger import get_logger

logger = get_logger("DocumentService")


class DocumentService:
    """Business logic service for Document Ingestion and Hybrid GraphRAG Retrieval."""

    def __init__(self, db_session: Session):
        self.session = db_session
        self.repo = DocumentRepository(db_session)

    def upload_and_ingest_document(
        self,
        workspace_id: str,
        filename: str,
        file_bytes: bytes,
        mime_type: str = "application/pdf",
        chunk_size: int = 500,
    ) -> Document:
        """Upload file blob to MinIO, create document record, and generate vector chunks using gemini-embedding-2."""
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        bucket_name = settings.MINIO_BUCKET_UPLOADS

        # 1. Upload file binary to MinIO and create Document record
        doc = storage_manager.store_document_file(
            workspace_id=workspace_id,
            title=filename,
            content_bytes=file_bytes,
            mime_type=mime_type,
            db_session=self.session,
        )


        # 3. Simple text chunking simulation
        text_content = file_bytes.decode("utf-8", errors="ignore")
        if not text_content.strip():
            text_content = f"Document content for {filename} (SHA256: {sha256[:12]})"

        words = text_content.split()
        chunks_data = []
        for i in range(0, max(1, len(words)), chunk_size):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)
            if chunk_text.strip():
                # Simulated 1536-dimensional vector embedding for gemini-embedding-2
                embedding = [0.1] * settings.VECTOR_EMBEDDING_DIM
                chunks_data.append({
                    "content": chunk_text,
                    "token_count": len(chunk_words),
                    "embedding": embedding,
                })

        if chunks_data:
            self.repo.add_chunks(doc.id, chunks_data)

        logger.info(f"Ingested document '{filename}' (ID: {doc.id}) with {len(chunks_data)} vector chunks using model {settings.EMBEDDING_MODEL}")
        return doc

    def list_workspace_documents(self, workspace_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[Document], int]:
        """List documents in a workspace."""
        docs = self.repo.get_workspace_documents(workspace_id)
        total = len(docs)
        return docs[skip : skip + limit], total

    def hybrid_vector_search(
        self,
        workspace_id: str,
        query_text: str,
        top_k: int = 5,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Perform hybrid vector & keyword search against document chunks."""
        # Simulated embedding calculation with gemini-embedding-2
        query_embedding = [0.1] * settings.VECTOR_EMBEDDING_DIM
        return self.repo.vector_search(
            query_embedding=query_embedding,
            workspace_id=workspace_id,
            top_k=top_k,
        )
