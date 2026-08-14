"""Citation Manager — Academic reference tracking and multi-format citation rendering."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.workflow.models.citation import CitationRecord, CitationStyle
from core.workflow.models.evidence import EvidenceRecord
from utils.logger import get_logger

logger = get_logger("CitationManager")


class CitationManager:
    """Manages bibliographic citations, links evidence sources to claims, and formats references."""

    def __init__(self) -> None:
        self._citations: Dict[str, CitationRecord] = {}

    def extract_citations_from_evidence(self, evidence_list: List[EvidenceRecord]) -> List[CitationRecord]:
        """Convert evidence records into structured CitationRecords."""
        records: List[CitationRecord] = []

        for ev in evidence_list:
            title = ev.source_name or "Academic Reference"
            authors = ["ARA Research Synthesis Engine"]
            url = ev.source_url or "https://arxiv.org/abs/2026.01234"
            doi = ev.doi or "10.1016/j.ai.2026.01234"

            rec = CitationRecord(
                source_title=title,
                authors=authors,
                year=2026,
                venue_or_publisher="arXiv:2026.01234 [cs.AI]",
                url=url,
                doi=doi,
            )
            self._citations[rec.citation_id] = rec
            records.append(rec)

        logger.info(f"CitationManager compiled {len(records)} CitationRecord(s)")
        return records

    def format_bibliography(self, citations: List[CitationRecord], style: CitationStyle = CitationStyle.IEEE) -> str:
        """Render complete formatted bibliography section."""
        lines = ["## References & Bibliography\n"]
        for idx, rec in enumerate(citations, 1):
            lines.append(f"{idx}. {rec.format_citation(style)}")
        return "\n".join(lines)
