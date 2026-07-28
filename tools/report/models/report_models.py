"""Data models for the Report Generation Platform."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_isoformat


class ExportFormat(str, Enum):
    """Supported report output export formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    TXT = "txt"
    PDF = "pdf"
    DOCX = "docx"


@dataclass
class CitationItem:
    """Model representing an attributed source citation."""
    citation_id: str = field(default_factory=lambda: generate_id("cite_"))
    reference_number: int = 1
    title: str = ""
    source_url_or_path: str = ""
    author: Optional[str] = None
    publish_date: Optional[str] = None
    snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "reference_number": self.reference_number,
            "title": self.title,
            "source_url_or_path": self.source_url_or_path,
            "author": self.author,
            "publish_date": self.publish_date,
            "snippet": self.snippet,
        }


@dataclass
class VisualizationElement:
    """Model representing a visual chart, table, or matrix element inside a report."""
    vis_id: str = field(default_factory=lambda: generate_id("vis_"))
    title: str = ""
    element_type: str = "table"  # 'table', 'matrix', 'chart', 'timeline'
    content_markdown: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vis_id": self.vis_id,
            "title": self.title,
            "element_type": self.element_type,
            "content_markdown": self.content_markdown,
            "data": self.data,
        }


@dataclass
class ReportSection:
    """Individual section inside a structured report deliverable."""
    section_id: str = field(default_factory=lambda: generate_id("sec_"))
    title: str = ""
    content: str = ""
    subsections: List['ReportSection'] = field(default_factory=list)
    visualizations: List[VisualizationElement] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "content": self.content,
            "subsections": [s.to_dict() for s in self.subsections],
            "visualizations": [v.to_dict() for v in self.visualizations],
        }


@dataclass
class ReportMetrics:
    """Telemetry and document statistics for generated reports."""
    word_count: int = 0
    section_count: int = 0
    citation_count: int = 0
    visualization_count: int = 0
    generation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word_count": self.word_count,
            "section_count": self.section_count,
            "citation_count": self.citation_count,
            "visualization_count": self.visualization_count,
            "generation_time_ms": self.generation_time_ms,
        }


@dataclass
class ReportValidationResult:
    """Quality and completeness validation report result."""
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": self.issues,
            "warnings": self.warnings,
        }


@dataclass
class NormalizedReport:
    """Unified container model representing a final structured deliverable report."""
    report_id: str = field(default_factory=lambda: generate_id("rep_"))
    title: str = "AI Research Assistant Report"
    subtitle: Optional[str] = None
    summary: str = ""
    template_name: str = "research_report"
    sections: List[ReportSection] = field(default_factory=list)
    citations: List[CitationItem] = field(default_factory=list)
    metrics: ReportMetrics = field(default_factory=ReportMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "summary": self.summary,
            "template_name": self.template_name,
            "sections": [s.to_dict() for s in self.sections],
            "citations": [c.to_dict() for c in self.citations],
            "metrics": self.metrics.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
