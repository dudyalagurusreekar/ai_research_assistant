"""Report Template Registry storing reusable report deliverable structures."""

from typing import Dict, List, Any, Optional
from tools.report.interfaces.report_interfaces import IReportTemplateRegistry
from infrastructure.logging.logger import StructuredLogger


class ReportTemplateRegistry(IReportTemplateRegistry):
    """Registry maintaining reusable report templates (Research Report, Technical Doc, Executive Summary, Code Review, Comparison)."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ReportTemplateRegistry")
        self._templates: Dict[str, List[Dict[str, Any]]] = {}

        # Register default templates
        self.register_template("research_report", [
            {"title": "Executive Summary", "content": "Summary of research findings and key insights."},
            {"title": "Background & Context", "content": "Background details and domain context."},
            {"title": "Detailed Findings", "content": "Comprehensive findings extracted across platforms."},
            {"title": "Conclusions & Recommendations", "content": "Strategic recommendations based on findings."},
        ])

        self.register_template("code_review", [
            {"title": "Project Architecture Overview", "content": "Overview of codebase architecture and project indexing."},
            {"title": "Static Analysis & Security Warnings", "content": "Complexity metrics and security vulnerability warnings."},
            {"title": "Dependency Audit", "content": "Package manifest dependencies and versions."},
            {"title": "Recommendations & Next Steps", "content": "Code quality refactoring suggestions."},
        ])

        self.register_template("executive_summary", [
            {"title": "High-Level Overview", "content": "Core research outcome summary."},
            {"title": "Key Takeaways", "content": "Bullet points of key insights."},
            {"title": "Action Plan", "content": "Next steps and decision roadmap."},
        ])

    def register_template(self, name: str, structure: List[Dict[str, Any]]) -> None:
        """Register a report deliverable template."""
        self._templates[name.lower()] = structure
        self._logger.debug(f"Registered report template '{name}' ({len(structure)} sections)")

    def get_template(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve registered report template structure by name."""
        return self._templates.get(name.lower())
