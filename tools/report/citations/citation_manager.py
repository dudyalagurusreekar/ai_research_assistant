"""Citation Manager managing reference attribution and bibliography generation."""

from typing import List, Dict, Optional
from tools.report.interfaces.report_interfaces import ICitationManager
from tools.report.models.report_models import CitationItem
from infrastructure.logging.logger import StructuredLogger


class CitationManager(ICitationManager):
    """Manages source reference attribution, footnotes, and Markdown bibliography lists."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("CitationManager")
        self._citations: List[CitationItem] = []

    def add_citation(self, title: str, url_or_path: str, snippet: Optional[str] = None) -> CitationItem:
        """Add a new citation reference."""
        ref_num = len(self._citations) + 1
        item = CitationItem(
            reference_number=ref_num,
            title=title,
            source_url_or_path=url_or_path,
            snippet=snippet,
        )
        self._citations.append(item)
        self._logger.debug(f"Added citation [{ref_num}] '{title}'")
        return item

    def get_citations(self) -> List[CitationItem]:
        """Return list of all registered citations."""
        return self._citations

    def format_bibliography_markdown(self) -> str:
        """Format references into Markdown bibliography list."""
        if not self._citations:
            return "No citations referenced."

        lines = ["## References & Citations", ""]
        for c in self._citations:
            line = f"[{c.reference_number}] **{c.title}** - `{c.source_url_or_path}`"
            if c.snippet:
                line += f"  \n   *\"{c.snippet.strip()}\"*"
            lines.append(line)

        return "\n".join(lines)
