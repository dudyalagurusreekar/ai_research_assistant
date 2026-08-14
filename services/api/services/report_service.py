"""Clean Architecture Service for Report Generation and MinIO Blob Export."""

from typing import List, Optional
from sqlalchemy.orm import Session

from config.settings import settings
from infrastructure.database.models.reporting import Artifact, Report, ReportSection
from infrastructure.storage.storage_manager import storage_manager


class ReportService:
    """Business logic service for Research Reports and Artifact Exports."""

    def __init__(self, db_session: Session):
        self.session = db_session

    def generate_report(
        self,
        research_session_id: str,
        title: str,
        summary: str,
        sections: List[dict],
        format_type: str = "markdown",
    ) -> Report:
        """Generate structured report, upload to MinIO, and create database record."""
        # 1. Format content
        content_lines = [f"# {title}\n", f"## Executive Summary\n{summary}\n"]
        for sec in sections:
            content_lines.append(f"### {sec.get('title', 'Section')}\n{sec.get('content', '')}\n")
        full_markdown = "\n".join(content_lines)

        # 2. Upload blob to MinIO and create Report record
        report = storage_manager.store_report_file(
            research_session_id=research_session_id,
            title=title,
            report_bytes=full_markdown.encode("utf-8"),
            report_format=format_type,
            db_session=self.session,
        )

        # 3. Add Report Sections
        for idx, sec in enumerate(sections):
            sec_obj = ReportSection(
                report_id=report.id,
                section_title=sec.get("title", f"Section {idx+1}"),
                content=sec.get("content", ""),
                section_order=idx,
            )
            self.session.add(sec_obj)


        self.session.commit()
        self.session.refresh(report)
        return report


    def get_report_by_id(self, report_id: str) -> Optional[Report]:
        """Retrieve report by ID."""
        return self.session.query(Report).filter(Report.id == report_id).first()

    def get_presigned_download_url(self, report: Report, expires_seconds: int = 3600) -> str:
        """Generate presigned download URL for report file from MinIO."""
        return storage_manager.get_presigned_download_url(
            bucket_name=settings.MINIO_BUCKET_REPORTS,
            object_name=report.storage_path.split("/")[-1],
            expires_seconds=expires_seconds,
        )

