"""Citation models — Academic source tracking and multi-format citation rendering."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class CitationStyle(Enum):
    """Citation formatting styles supported."""

    APA = "apa"
    IEEE = "ieee"
    BIBTEX = "bibtex"
    MARKDOWN = "markdown"


@dataclass
class CitationRecord:
    """Academic/web reference citation container."""

    source_title: str
    authors: List[str] = field(default_factory=list)
    year: int = 2026
    venue_or_publisher: str = "arXiv"
    url: Optional[str] = None
    doi: Optional[str] = None
    citation_id: str = field(default_factory=lambda: f"cite_{uuid.uuid4().hex[:8]}")

    def format_citation(self, style: CitationStyle = CitationStyle.IEEE) -> str:
        """Format citation in designated academic style."""
        authors_str = ", ".join(self.authors) if self.authors else "Anonymous"
        if style == CitationStyle.IEEE:
            return f"[{self.citation_id}] {authors_str}, \"{self.source_title},\" {self.venue_or_publisher}, {self.year}."
        elif style == CitationStyle.APA:
            return f"{authors_str} ({self.year}). {self.source_title}. {self.venue_or_publisher}."
        elif style == CitationStyle.BIBTEX:
            return f"@article{{{self.citation_id},\n  title={{{self.source_title}}},\n  author={{{authors_str}}},\n  year={{{self.year}}}\n}}"
        else:  # MARKDOWN
            url_part = f" ([Link]({self.url}))" if self.url else ""
            return f"- **{self.source_title}** ({self.year}) — {authors_str}{url_part}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "source_title": self.source_title,
            "authors": self.authors,
            "year": self.year,
            "venue_or_publisher": self.venue_or_publisher,
            "url": self.url,
            "doi": self.doi,
            "formatted_ieee": self.format_citation(CitationStyle.IEEE),
        }
