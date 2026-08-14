"""Knowledge Base, RAG, pgvector Embeddings, and Retrieval Stats ORM models."""

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin
from config.settings import settings

# Attempt pgvector import with fallback to JSON for SQLite test environments
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    Vector = None
    HAS_PGVECTOR = False


class Document(BaseORMModel):
    """Document metadata model for RAG knowledge ingestion."""

    __tablename__ = "documents"

    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=False)
    minio_bucket = Column(String(100), default="ara-uploads", nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    source_url = Column(Text, nullable=True)
    status = Column(String(50), default="processed", nullable=False)  # pending, processing, processed, error

    workspace = relationship("Workspace", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    doc_metadata = relationship("DocumentMetadata", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Document text chunk and vector embedding representation."""

    __tablename__ = "document_chunks"

    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    
    # Vector embedding column (pgvector 1536 dims or JSON fallback)
    if HAS_PGVECTOR and Vector is not None:
        embedding = Column(Vector(settings.VECTOR_EMBEDDING_DIM), nullable=True)
    else:
        embedding = Column(JSON, nullable=True)

    extra_metadata = Column(JSON, default=dict, nullable=False)

    document = relationship("Document", back_populates="chunks")


class DocumentMetadata(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Flexible key-value document metadata pairs."""

    __tablename__ = "document_metadata"

    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    meta_key = Column(String(100), nullable=False, index=True)
    meta_value = Column(Text, nullable=False)

    document = relationship("Document", back_populates="doc_metadata")


class RetrievalStat(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Analytics and performance logging for RAG vector retrieval queries."""

    __tablename__ = "retrieval_stats"

    query_text = Column(Text, nullable=False)
    search_mode = Column(String(50), default="hybrid", nullable=False)  # vector, keyword, hybrid, graph
    retrieved_chunks_count = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    similarity_threshold = Column(Float, default=0.7, nullable=False)
    feedback_score = Column(Float, nullable=True)  # 1.0 positive, 0.0 negative
