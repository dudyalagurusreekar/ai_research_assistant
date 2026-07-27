"""Smolagents Tool wrapper for the Report Generation Platform."""

from smolagents import Tool
from tools.report.facade.facade import ReportToolFacade


class ReportTool(Tool):
    """Tool wrapper exposing ReportToolFacade capabilities to smolagents."""

    name = "report_tool"
    description = "Unified output generation tool for composing, validating, formatting, and exporting research reports."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'compose', 'export', 'validate', or 'list_templates'",
            "nullable": True,
        },
        "title": {
            "type": "string",
            "description": "Report title string",
            "nullable": True,
        },
        "format": {
            "type": "string",
            "description": "Export format: 'markdown', 'html', 'json', 'csv', 'txt', 'pdf', or 'docx'",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: ReportToolFacade = None):
        super().__init__()
        self._facade = facade or ReportToolFacade()

    def forward(self, action: str = "compose", title: str = "AI Research Report", format: str = "markdown") -> str:
        import asyncio
        return asyncio.run(self._facade.forward(action=action, title=title, format=format))
