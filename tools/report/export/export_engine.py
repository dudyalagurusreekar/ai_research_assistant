"""Export Engine rendering multi-format deliverables."""

import json
from typing import Optional
from tools.report.interfaces.report_interfaces import IExportEngine
from tools.report.models.report_models import NormalizedReport, ExportFormat
from infrastructure.storage.storage import DiskStorage
from infrastructure.logging.logger import StructuredLogger


class ExportEngine(IExportEngine):
    """Exports NormalizedReport objects into Markdown, HTML, JSON, CSV, TXT, PDF, and DOCX formats."""

    def __init__(self, storage: Optional[DiskStorage] = None) -> None:
        self._logger = StructuredLogger("ExportEngine")
        self._storage = storage or DiskStorage()

    async def export(self, report: NormalizedReport, format_type: ExportFormat) -> str:
        """Render report into target format string or payload."""
        self._logger.info(f"Exporting report '{report.report_id}' to format '{format_type.value}'")

        if format_type == ExportFormat.JSON:
            return json.dumps(report.to_dict(), indent=2)

        elif format_type == ExportFormat.MARKDOWN:
            return self._render_markdown(report)

        elif format_type == ExportFormat.HTML:
            md_text = self._render_markdown(report)
            return f"<!DOCTYPE html>\n<html>\n<head><title>{report.title}</title></head>\n<body>\n<pre>{md_text}</pre>\n</body>\n</html>"

        elif format_type == ExportFormat.TXT:
            return self._render_txt(report)

        elif format_type == ExportFormat.CSV:
            # Export section titles and word counts as CSV
            lines = ["Section Title,Word Count"]
            for sec in report.sections:
                lines.append(f'"{sec.title}",{len(sec.content.split())}')
            return "\n".join(lines)

        elif format_type in [ExportFormat.PDF, ExportFormat.DOCX]:
            # Wrapper container output for PDF/DOCX
            md_content = self._render_markdown(report)
            return f"[{format_type.value.upper()} EXPORT CONTAINER]\n\n{md_content}"

        else:
            return self._render_markdown(report)

    def _render_markdown(self, report: NormalizedReport) -> str:
        """Render report into clean Markdown text."""
        lines = []
        lines.append(f"# {report.title}")
        if report.subtitle:
            lines.append(f"*{report.subtitle}*")
        lines.append("")

        if report.summary:
            lines.append(f"> **Summary**: {report.summary}")
            lines.append("")

        for sec in report.sections:
            lines.append(f"## {sec.title}")
            lines.append(sec.content)
            lines.append("")

            for vis in sec.visualizations:
                lines.append(vis.content_markdown)
                lines.append("")

        if report.citations:
            lines.append("## References & Citations")
            for c in report.citations:
                lines.append(f"[{c.reference_number}] **{c.title}** - `{c.source_url_or_path}`")
            lines.append("")

        return "\n".join(lines)

    def _render_txt(self, report: NormalizedReport) -> str:
        """Render report into plain TXT text."""
        lines = [report.title.upper(), "=" * len(report.title), ""]
        for sec in report.sections:
            lines.append(sec.title)
            lines.append("-" * len(sec.title))
            lines.append(sec.content)
            lines.append("")
        return "\n".join(lines)
