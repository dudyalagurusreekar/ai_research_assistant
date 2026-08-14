"""REST API Router for Document Upload, MinIO Storage Sync, and RAG Hybrid Search (/api/v1/workspaces/{id}/documents)."""

from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import PaginationMeta, ResponseEnvelope
from services.api.services.document_service import DocumentService

router = APIRouter(tags=["Knowledge Base & RAG Documents"])


class SearchDocumentsRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


@router.post("/workspaces/{workspace_id}/documents/upload", status_code=status.HTTP_201_CREATED)
@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    workspace_id: str = "default",
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Upload document file, store binary blob in MinIO, create chunks, and index vector embeddings."""
    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    service = DocumentService(db)
    doc = service.upload_and_ingest_document(
        workspace_id=workspace_id,
        filename=file.filename or "uploaded_document.pdf",
        file_bytes=content_bytes,
        mime_type=file.content_type or "application/pdf",
    )

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": doc.id,
            "workspace_id": doc.workspace_id,
            "title": doc.title,
            "file_size": doc.file_size,
            "mime_type": doc.mime_type,
            "storage_path": doc.storage_path,
            "sha256_hash": doc.sha256_hash,
        },
        correlation_id=correlation_id,
    )


@router.get("/workspaces/{workspace_id}/documents")
@router.get("/documents")
def list_documents(
    workspace_id: str = "default",
    page: int = 1,
    limit: int = 20,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """List documents in a workspace."""
    service = DocumentService(db)
    skip = (page - 1) * limit
    docs, total = service.list_workspace_documents(workspace_id, skip=skip, limit=limit)

    meta = PaginationMeta(page=page, limit=limit, total_items=total, total_pages=(total + limit - 1) // limit if limit > 0 else 1)
    correlation_id = getattr(request.state, "correlation_id", None) if request else None

    data = [
        {
            "id": d.id,
            "title": d.title,
            "mime_type": d.mime_type,
            "file_size": d.file_size,
            "storage_path": d.storage_path,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]
    return ResponseEnvelope.success_response(data=data, meta=meta, correlation_id=correlation_id)


@router.post("/workspaces/{workspace_id}/documents/search")
@router.post("/documents/search")
def search_documents(
    req: SearchDocumentsRequest,
    request: Request,
    workspace_id: str = "default",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Perform hybrid vector RAG search using gemini-embedding-2."""
    service = DocumentService(db)
    results = service.hybrid_vector_search(workspace_id, req.query, top_k=req.top_k or 5)

    correlation_id = getattr(request.state, "correlation_id", None)
    data = [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "content": chunk.content,
            "similarity_score": round(score, 4),
        }
        for chunk, score in results
    ]
    return ResponseEnvelope.success_response(data=data, correlation_id=correlation_id)
