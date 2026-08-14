"""Reports, Sections, and Generated Artifacts ORM models."""

from sqlalchemy import Column, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin


class Report(BaseORMModel):
    """Generated research report model."""

    __tablename__ = "reports"

    research_session_id = Column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    format = Column(String(50), default="markdown", nullable=False)  # markdown, pdf, html, json
    storage_path = Column(String(512), nullable=False)
    minio_bucket = Column(String(100), default="ara-reports", nullable=False)
    report_metadata = Column(JSON, default=dict, nullable=False)

    research_session = relationship("ResearchSession", back_populates="reports")
    sections = relationship("ReportSection", back_populates="report", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="report", cascade="all, delete-orphan")


class ReportSection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Structured report section."""

    __tablename__ = "report_sections"

    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    section_title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    section_order = Column(Integer, default=0, nullable=False)

    report = relationship("Report", back_populates="sections")


class Artifact(BaseORMModel):
    """Generated artifact (diagrams, plots, data exports)."""

    __tablename__ = "artifacts"

    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=True, index=True)
    artifact_name = Column(String(255), nullable=False)
    artifact_type = Column(String(100), nullable=False)  # chart, table, diagram, code
    storage_path = Column(String(512), nullable=False)
    minio_bucket = Column(String(100), default="ara-generated-files", nullable=False)
    content_summary = Column(Text, nullable=True)

    report = relationship("Report", back_populates="artifacts")
