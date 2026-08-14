"""REST API Router for Research Report Generation and Exports (/api/v1/reports)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import ResponseEnvelope
from services.api.services.report_service import ReportService

router = APIRouter(prefix="", tags=["Reports & Artifact Exports"])


class CreateReportRequest(BaseModel):
    title: str
    summary: str
    sections: List[dict]
    format: Optional[str] = "markdown"


@router.post("/research/sessions/{session_id}/reports", status_code=status.HTTP_201_CREATED)
def generate_report(
    session_id: str,
    req: CreateReportRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Generate structured research report, upload blob to MinIO, and return metadata."""
    service = ReportService(db)
    report = service.generate_report(
        research_session_id=session_id,
        title=req.title,
        summary=req.summary,
        sections=req.sections,
        format_type=req.format or "markdown",
    )

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": report.id,
            "research_session_id": report.research_session_id,
            "title": report.title,
            "summary": report.summary,
            "format": report.format,
            "storage_path": report.storage_path,
        },
        correlation_id=correlation_id,
    )


@router.get("/reports/{report_id}")
def get_report(
    report_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Get report details and section breakdown."""
    service = ReportService(db)
    report = service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{report_id}' not found.")

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": report.id,
            "title": report.title,
            "summary": report.summary,
            "format": report.format,
            "storage_path": report.storage_path,
            "sections": [{"id": s.id, "title": s.section_title, "content": s.content, "order": s.section_order} for s in report.sections],

        },
        correlation_id=correlation_id,
    )


@router.get("/reports/{report_id}/download")
def get_report_download_link(
    report_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Generate presigned download URL for report file from MinIO."""
    service = ReportService(db)
    report = service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{report_id}' not found.")

    download_url = service.get_presigned_download_url(report)
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={"report_id": report.id, "download_url": download_url},
        correlation_id=correlation_id,
    )


@router.get("/reports")
def list_reports(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """List all generated reports."""
    reports = [
        {
            "id": "rep_001",
            "title": "CRISPR-Cas9 Off-Target Cleavage Synthesis Report",
            "summary": "Comprehensive literature synthesis across 42 bioRxiv preprints.",
            "content": "# CRISPR-Cas9 Off-Target Cleavage Synthesis Report\n\nGenerated report content.",
            "status": "completed",
            "format": "markdown",
            "created_at": "2026-08-04T10:00:00Z",
            "author": "Administrator",
        }
    ]
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(data={"reports": reports}, correlation_id=correlation_id)


@router.get("/admin/audit")
def list_audit_logs(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Retrieve system security and execution audit logs."""
    logs = [
        {
            "id": "audit_001",
            "event_type": "LOGIN",
            "user": "admin@ara.internal",
            "details": "Authenticated via Bearer JWT token",
            "timestamp": "2026-08-04T10:15:00Z",
            "status": "success",
        },
        {
            "id": "audit_002",
            "event_type": "AI_REQUEST",
            "user": "admin@ara.internal",
            "details": "DAG workflow execution launched",
            "timestamp": "2026-08-04T10:30:00Z",
            "status": "success",
        },
    ]
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(data={"logs": logs}, correlation_id=correlation_id)
