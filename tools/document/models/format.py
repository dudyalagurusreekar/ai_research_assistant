"""Document Format Enum and Detection Models."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


class DocumentFormat(str, Enum):
    """Supported document formats enum."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    CSV = "csv"
    TXT = "txt"
    MARKDOWN = "markdown"
    HTML = "html"
    XML = "xml"
    IMAGE = "image"
    ZIP = "zip"
    UNKNOWN = "unknown"


@dataclass
class FormatDetectionResult:
    """Result returned by FormatDetector."""

    format: DocumentFormat
    mime_type: str
    extension: str
    confidence: float  # 0.0 to 1.0
    detected_by: str  # 'magic_bytes', 'mime_type', or 'extension'
    metadata: Dict[str, Any] = field(default_factory=dict)
