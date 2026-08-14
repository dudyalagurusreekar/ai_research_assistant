"""REST API Router for Enterprise RAG & Document Intelligence (/api/v1/rag)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session
from core.rag.pipeline import GroundedQAEngine, RAGPipeline
from core.rag.retrieval.hybrid import HybridRetriever
from infrastructure.database.models.auth import User
from infrastructure.database.models.knowledge import DocumentChunk
from services.api.schemas.envelope import ResponseEnvelope

router = APIRouter(prefix="/rag", tags=["Enterprise RAG & Document Intelligence"])


class SearchQueryRequest(BaseModel):
    query: str
    workspace_id: Optional[str] = "default"
    top_k: Optional[int] = 5


class GroundedQARequest(BaseModel):
    workspace_id: str
    question: str
    top_k: Optional[int] = 5


@router.post("/documents/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_document(
    workspace_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Ingest multi-format document (PDF, DOCX, PPTX, TXT, MD, HTML, CSV, JSON), generate vector chunks, and persist to MinIO & PostgreSQL."""
    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    pipeline = RAGPipeline(db)
    doc = pipeline.ingest_document(
        workspace_id=workspace_id,
        filename=file.filename or "document.pdf",
        file_bytes=content_bytes,
        mime_type=file.content_type,
    )

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": doc.id,
            "workspace_id": doc.workspace_id,
            "title": doc.title,
            "mime_type": doc.mime_type,
            "file_size": doc.file_size,
            "storage_path": doc.storage_path,
            "sha256_hash": doc.sha256_hash,
        },
        correlation_id=correlation_id,
    )


@router.post("/search")
def hybrid_search(
    req: SearchQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Execute Hybrid pgvector + BM25 search with Reciprocal Rank Fusion and Reranking."""
    retriever = HybridRetriever(db)
    results = retriever.search(req.workspace_id, req.query, top_k=req.top_k or 5)

    correlation_id = getattr(request.state, "correlation_id", None)
    data = [
        {
            "chunk_id": item.chunk_id,
            "document_id": item.document_id,
            "document_title": item.document_title,
            "chunk_index": item.chunk_index,
            "content": item.content,
            "score": item.score,
            "citation": item.citation,
        }
        for item in results
    ]
    return ResponseEnvelope.success_response(data=data, correlation_id=correlation_id)


@router.post("/query")
def grounded_qa_query(
    req: GroundedQARequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Generate evidence-grounded answer with traceable inline citations."""
    qa_engine = GroundedQAEngine(db)
    result = qa_engine.answer_question(req.workspace_id, req.question, top_k=req.top_k or 5)

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(data=result, correlation_id=correlation_id)


@router.get("/documents/{document_id}/chunks")
def inspect_document_chunks(
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Inspect document chunking breakdown and vector index metadata."""
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index.asc()).all()

    correlation_id = getattr(request.state, "correlation_id", None)
    data = [
        {
            "id": c.id,
            "chunk_index": c.chunk_index,
            "token_count": c.token_count,
            "content": c.content,
            "extra_metadata": c.extra_metadata,
        }
        for c in chunks
    ]
    return ResponseEnvelope.success_response(data=data, correlation_id=correlation_id)


@router.post("/documents/{document_id}/reindex")
def reindex_document(
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Trigger incremental document re-indexing."""
    pipeline = RAGPipeline(db)
    try:
        doc = pipeline.reindex_document(document_id)
        correlation_id = getattr(request.state, "correlation_id", None)
        return ResponseEnvelope.success_response(
            data={"message": f"Document '{doc.title}' (ID: {doc.id}) re-indexed successfully."},
            correlation_id=correlation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
