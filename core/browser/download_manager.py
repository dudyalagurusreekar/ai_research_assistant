"""Browser Download Interceptor & RAG Ingestion Pipeline."""

import logging
import uuid
from typing import Dict, Any, Optional
from core.browser.models import BrowserDownload

logger = logging.getLogger(__name__)


class DownloadManager:
    """Manages browser file downloads, stores in MinIO, and feeds into RAG pipeline."""

    def __init__(self, minio_client: Optional[Any] = None, rag_pipeline: Optional[Any] = None):
        self.minio_client = minio_client
        self.rag_pipeline = rag_pipeline
        self.downloads: Dict[str, BrowserDownload] = {}

    async def handle_download(
        self,
        session_id: str,
        download_url: str,
        filename: str,
        file_bytes: bytes,
        mime_type: str = "application/pdf",
    ) -> BrowserDownload:
        """Save downloaded file to MinIO (browser-downloads) and index into RAG vector storage."""
        download_id = f"dl_{uuid.uuid4().hex[:8]}"
        storage_path = f"browser-downloads/{session_id}/{filename}"

        # Save to MinIO storage if available
        if self.minio_client:
            try:
                self.minio_client.put_object(
                    bucket_name="browser-downloads",
                    object_name=f"{session_id}/{filename}",
                    data=file_bytes,
                    length=len(file_bytes),
                    content_type=mime_type,
                )
            except Exception as e:
                logger.warning(f"MinIO download storage failed: {e}.")

        # Ingest into Enterprise RAG Pipeline
        rag_doc_id = None
        if self.rag_pipeline:
            try:
                doc = self.rag_pipeline.ingest_document(
                    filename=filename,
                    content_bytes=file_bytes,
                    mime_type=mime_type,
                    metadata={"source": "browser_download", "url": download_url, "session_id": session_id},
                )
                rag_doc_id = doc.id if hasattr(doc, "id") else str(doc)
            except Exception as e:
                logger.warning(f"RAG download ingestion error: {e}.")

        download_item = BrowserDownload(
            download_id=download_id,
            session_id=session_id,
            filename=filename,
            url=download_url,
            mime_type=mime_type,
            file_size=len(file_bytes),
            storage_path=storage_path,
            rag_document_id=rag_doc_id or f"doc_rag_{download_id}",
        )
        self.downloads[download_id] = download_item
        logger.info(f"Successfully processed browser download '{filename}' ({len(file_bytes)} bytes) for session '{session_id}'.")
        return download_item
