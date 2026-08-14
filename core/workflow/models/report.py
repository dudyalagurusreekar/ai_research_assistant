"""Research Report models — Composed academic and executive research document containers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.workflow.models.citation import CitationRecord


class ReportFormat(Enum):
    """Output format types for research reports."""

    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


@dataclass
class ReportSection:
    """A single section container in a research report."""

    title: str
    content: str
    section_id: str = field(default_factory=lambda: f"sec_{uuid.uuid4().hex[:6]}")
    order: int = 0
    citations_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "order": self.order,
            "content_length": len(self.content),
            "citations_used": self.citations_used,
        }


@dataclass
class ResearchReport:
    """Comprehensive academic/executive research report container."""

    title: str
    executive_summary: str
    sections: List[ReportSection] = field(default_factory=list)
    citations: List[CitationRecord] = field(default_factory=list)
    charts_svg: List[str] = field(default_factory=list)
    data_tables: List[Dict[str, Any]] = field(default_factory=list)
    markdown_content: str = ""
    html_content: str = ""
    report_id: str = field(default_factory=lambda: f"rep_{uuid.uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "sections_count": len(self.sections),
            "citations_count": len(self.citations),
            "charts_count": len(self.charts_svg),
            "created_at": self.created_at,
        }
