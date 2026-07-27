"""Documentation Engine for generating Markdown API docs from NormalizedCodeProject."""

import asyncio
from typing import List
from tools.code.interfaces.code_interfaces import IDocumentationEngine
from tools.code.models.code_models import NormalizedCodeProject, DocGenResult
from infrastructure.logging.logger import StructuredLogger


class DocumentationEngine(IDocumentationEngine):
    """Generates structured Markdown API documentation and project overviews."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("DocumentationEngine")

    async def generate_documentation(self, project: NormalizedCodeProject) -> DocGenResult:
        """Construct Markdown documentation for project symbols and structure."""
        doc_lines = []
        toc = []
        symbol_count = 0

        doc_lines.append(f"# Project Documentation: {project.project_name}")
        doc_lines.append("")
        doc_lines.append(f"- **Total Files**: {project.total_files}")
        doc_lines.append(f"- **Total Lines**: {project.total_lines}")
        doc_lines.append(f"- **Languages**: {', '.join(project.languages)}")
        doc_lines.append("")

        doc_lines.append("## Dependencies")
        if project.dependencies:
            for dep in project.dependencies:
                doc_lines.append(f"- `{dep.package_name}` ({dep.version_spec}) [{dep.ecosystem}]")
        else:
            doc_lines.append("No explicit manifest dependencies detected.")
        doc_lines.append("")

        doc_lines.append("## Code Files & API Reference")
        doc_lines.append("")

        for f in project.files:
            if not f.symbols:
                continue
            
            section_title = f"File: {f.relative_path}"
            toc.append(section_title)
            doc_lines.append(f"### {section_title}")
            doc_lines.append(f"*Language: {f.language} | Lines: {f.line_count}*")
            doc_lines.append("")

            for sym in f.symbols:
                symbol_count += 1
                doc_lines.append(f"#### `{sym.signature or sym.name}`")
                doc_lines.append(f"- **Type**: {sym.symbol_type.value}")
                doc_lines.append(f"- **Lines**: L{sym.start_line}-L{sym.end_line}")
                if sym.docstring:
                    doc_lines.append(f"> {sym.docstring.strip()}")
                doc_lines.append("")

        markdown_text = "\n".join(doc_lines)
        result = DocGenResult(
            project_name=project.project_name,
            markdown_doc=markdown_text,
            table_of_contents=toc,
            symbols_documented=symbol_count,
        )

        self._logger.info(f"Generated documentation for '{project.project_name}': {symbol_count} symbols documented.")
        return result
