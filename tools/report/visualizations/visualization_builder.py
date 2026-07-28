"""Visualization Builder constructing Markdown tables and comparison matrices."""

from typing import List
from tools.report.interfaces.report_interfaces import IVisualizationBuilder
from tools.report.models.report_models import VisualizationElement
from infrastructure.logging.logger import StructuredLogger


class VisualizationBuilder(IVisualizationBuilder):
    """Generates formatted Markdown tables, comparison matrices, and metric summary boxes."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("VisualizationBuilder")

    def create_markdown_table(self, headers: List[str], rows: List[List[str]], title: str = "") -> VisualizationElement:
        """Construct Markdown table visualization element."""
        lines = []
        if title:
            lines.append(f"### {title}")
            lines.append("")

        # Header row
        lines.append("| " + " | ".join(headers) + " |")
        # Separator row
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        # Data rows
        for row in rows:
            lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

        markdown_text = "\n".join(lines)
        return VisualizationElement(
            title=title or "Data Table",
            element_type="table",
            content_markdown=markdown_text,
            data={"headers": headers, "rows": rows},
        )
