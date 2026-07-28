"""Abstract interface contracts for the Report Generation Platform."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tools.report.models.report_models import (
    NormalizedReport,
    CitationItem,
    VisualizationElement,
    ExportFormat,
    ReportValidationResult,
)


class IReportTemplateRegistry(ABC):
    """Abstract report template registry interface."""

    @abstractmethod
    def register_template(self, name: str, structure: List[Dict[str, Any]]) -> None:
        """Register a report template."""

    @abstractmethod
    def get_template(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """Get template structure by name."""


class IReportComposer(ABC):
    """Abstract report composer interface assembling multi-source data models into a NormalizedReport."""

    @abstractmethod
    async def compose_report(
        self,
        title: str,
        template_name: str = "research_report",
        sources: Optional[List[Any]] = None,
        custom_sections: Optional[List[Dict[str, Any]]] = None,
    ) -> NormalizedReport:
        """Assemble structured report."""


class ICitationManager(ABC):
    """Abstract citation manager interface handling source attribution and bibliography generation."""

    @abstractmethod
    def add_citation(self, title: str, url_or_path: str, snippet: Optional[str] = None) -> CitationItem:
        """Add citation reference item."""

    @abstractmethod
    def format_bibliography_markdown(self) -> str:
        """Format bibliography references into Markdown list."""


class IVisualizationBuilder(ABC):
    """Abstract visualization builder interface generating tables and comparison matrices."""

    @abstractmethod
    def create_markdown_table(self, headers: List[str], rows: List[List[str]], title: str = "") -> VisualizationElement:
        """Build Markdown table visualization element."""


class IExportEngine(ABC):
    """Abstract export engine interface converting NormalizedReport into target export formats."""

    @abstractmethod
    async def export(self, report: NormalizedReport, format_type: ExportFormat) -> str:
        """Export report into target format string or file payload."""


class IReportValidator(ABC):
    """Abstract report validator interface checking report completeness and citations."""

    @abstractmethod
    def validate_report(self, report: NormalizedReport) -> ReportValidationResult:
        """Validate report structure and citation references."""
