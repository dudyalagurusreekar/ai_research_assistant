"""Abstract Document Parser Interface and Data Containers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParsedSection:
    """Structured section extracted from document."""
    heading: str
    content: str
    level: int = 1


@dataclass
class ParsedTable:
    """Structured table extracted from document."""
    caption: str
    headers: List[str]
    rows: List[List[str]]


@dataclass
class ParsedDocument:
    """Standardized representation of a parsed document."""
    title: str
    raw_text: str
    sections: List[ParsedSection] = field(default_factory=list)
    tables: List[ParsedTable] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AbstractDocumentParser(ABC):
    """Base abstract class for document format parsers."""

    @abstractmethod
    def parse(self, file_bytes: bytes, filename: str, mime_type: Optional[str] = None) -> ParsedDocument:
        """Parse raw file bytes into ParsedDocument container."""
        pass
