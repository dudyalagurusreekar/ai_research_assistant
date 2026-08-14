"""ObjectStorageManager coordinating MinIO binary blobs with PostgreSQL metadata records."""

import uuid
from typing import Optional
from sqlalchemy.orm import Session
from config.settings import settings
from infrastructure.database.models.browser import BrowserScreenshot
from infrastructure.database.models.knowledge import Document
from infrastructure.database.models.reporting import Report
from infrastructure.storage.minio_client import minio_client_manager
from utils.logger import get_logger

logger = get_logger("ObjectStorageManager")


class ObjectStorageManager:
    """Manager coordinating object storage uploads and database metadata updates."""

    def __init__(self, client_manager=None):
        self._minio = client_manager or minio_client_manager

    def store_document_file(
        self,
        workspace_id: str,
        title: str,
        content_bytes: bytes,
        mime_type: str = "text/plain",
        db_session: Optional[Session] = None,
    ) -> Document:
        """Upload document binary to MinIO (ara-uploads) and persist metadata record in PostgreSQL."""
        bucket = settings.MINIO_BUCKET_UPLOADS
        ext = mime_type.split("/")[-1] if "/" in mime_type else "bin"
        object_name = f"{workspace_id}/{uuid.uuid4().hex}.{ext}"

        # 1. Upload file bytes to MinIO
        sha256 = self._minio.calculate_sha256(content_bytes)
        storage_path = self._minio.upload_bytes(
            bucket_name=bucket,
            object_name=object_name,
            data=content_bytes,
            content_type=mime_type,
        )

        # 2. Create Document metadata model
        doc = Document(
            workspace_id=workspace_id,
            title=title,
            mime_type=mime_type,
            file_size=len(content_bytes),
            storage_path=storage_path,
            minio_bucket=bucket,
            sha256_hash=sha256,
            status="processed",
        )

        if db_session:
            db_session.add(doc)
            db_session.flush()

        logger.info(f"Stored document file '{title}' ({len(content_bytes)} bytes) in bucket '{bucket}'")
        return doc

    def store_report_file(
        self,
        research_session_id: str,
        title: str,
        report_bytes: bytes,
        report_format: str = "markdown",
        db_session: Optional[Session] = None,
    ) -> Report:
        """Upload generated report binary to MinIO (ara-reports) and persist metadata in PostgreSQL."""
        bucket = settings.MINIO_BUCKET_REPORTS
        object_name = f"{research_session_id}/{uuid.uuid4().hex}.{report_format}"

        mime_type = "application/pdf" if report_format == "pdf" else "text/markdown"
        storage_path = self._minio.upload_bytes(
            bucket_name=bucket,
            object_name=object_name,
            data=report_bytes,
            content_type=mime_type,
        )

        report = Report(
            research_session_id=research_session_id,
            title=title,
            format=report_format,
            storage_path=storage_path,
            minio_bucket=bucket,
        )

        if db_session:
            db_session.add(report)
            db_session.flush()

        logger.info(f"Stored report file '{title}' in bucket '{bucket}'")
        return report

    def store_screenshot(
        self,
        browser_session_id: str,
        page_url: str,
        screenshot_bytes: bytes,
        page_title: Optional[str] = None,
        db_session: Optional[Session] = None,
    ) -> BrowserScreenshot:
        """Upload browser screenshot PNG to MinIO (ara-screenshots) and log metadata."""
        bucket = settings.MINIO_BUCKET_SCREENSHOTS
        object_name = f"{browser_session_id}/{uuid.uuid4().hex}.png"

        storage_path = self._minio.upload_bytes(
            bucket_name=bucket,
            object_name=object_name,
            data=screenshot_bytes,
            content_type="image/png",
        )

        screenshot = BrowserScreenshot(
            browser_session_id=browser_session_id,
            page_title=page_title,
            page_url=page_url,
            storage_path=storage_path,
            minio_bucket=bucket,
        )

        if db_session:
            db_session.add(screenshot)
            db_session.flush()

        return screenshot

    def get_file_content(self, bucket_name: str, object_name: str) -> bytes:
        """Retrieve binary file content from MinIO object storage."""
        return self._minio.download_bytes(bucket_name, object_name)

    def get_presigned_download_url(self, bucket_name: str, object_name: str, expires_seconds: int = 3600) -> str:
        """Generate presigned GET URL for file download."""
        return self._minio.get_presigned_url(bucket_name, object_name, expires_seconds)


# Global ObjectStorageManager instance
storage_manager = ObjectStorageManager()
