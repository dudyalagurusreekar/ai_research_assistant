"""Magic Bytes Signatures and Identification Utility."""

from typing import Optional, Tuple
from tools.document.models.format import DocumentFormat

# Common byte signatures mapped to (DocumentFormat, MIME_Type, Primary_Extension)
MAGIC_SIGNATURES = [
    (b"%PDF", DocumentFormat.PDF, "application/pdf", ".pdf"),
    (b"\x89PNG\r\n\x1a\n", DocumentFormat.IMAGE, "image/png", ".png"),
    (b"\xff\xd8\xff", DocumentFormat.IMAGE, "image/jpeg", ".jpg"),
    (b"GIF87a", DocumentFormat.IMAGE, "image/gif", ".gif"),
    (b"GIF89a", DocumentFormat.IMAGE, "image/gif", ".gif"),
    (b"BM", DocumentFormat.IMAGE, "image/bmp", ".bmp"),
    (b"II*\x00", DocumentFormat.IMAGE, "image/tiff", ".tiff"),
    (b"MM\x00*", DocumentFormat.IMAGE, "image/tiff", ".tiff"),
    (b"RIFF", DocumentFormat.IMAGE, "image/webp", ".webp"),  # Check WEBP offset if RIFF
    (b"PK\x03\x04", DocumentFormat.ZIP, "application/zip", ".zip"),  # Base ZIP / Office OpenXML
]


def detect_format_from_bytes(data: bytes) -> Optional[Tuple[DocumentFormat, str, str]]:
    """Inspect head bytes to detect format, MIME type, and extension.

    Returns:
        Tuple of (DocumentFormat, mime_type, extension) if matched, else None.
    """
    if not data:
        return None

    # Check WEBP specifically
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return (DocumentFormat.IMAGE, "image/webp", ".webp")

    # Check signature table
    for sig, doc_fmt, mime, ext in MAGIC_SIGNATURES:
        if data.startswith(sig):
            return (doc_fmt, mime, ext)

    # Text / HTML / XML checks on raw text bytes
    try:
        sample = data[:1024].strip()
        sample_str = sample.decode("utf-8", errors="ignore").lower()
        if sample_str.startswith("<!doctype html") or sample_str.startswith("<html"):
            return (DocumentFormat.HTML, "text/html", ".html")
        if sample_str.startswith("<?xml") or (sample_str.startswith("<") and ">" in sample_str and not sample_str.startswith("<html")):
            return (DocumentFormat.XML, "application/xml", ".xml")
    except Exception:
        pass

    return None
