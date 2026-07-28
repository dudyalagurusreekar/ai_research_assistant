"""Format Detector implementation combining Magic Bytes, MIME Type, and File Extension."""

import os
from typing import Optional, Union, BinaryIO
from tools.document.interfaces.detector import IFormatDetector
from tools.document.models.format import DocumentFormat, FormatDetectionResult
from tools.document.utils.magic_bytes import detect_format_from_bytes
from infrastructure.logging.logger import StructuredLogger

# MIME type mapping dictionary
MIME_MAP = {
    "application/pdf": (DocumentFormat.PDF, ".pdf"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (DocumentFormat.DOCX, ".docx"),
    "application/msword": (DocumentFormat.DOCX, ".doc"),
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": (DocumentFormat.PPTX, ".pptx"),
    "application/vnd.ms-powerpoint": (DocumentFormat.PPTX, ".ppt"),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (DocumentFormat.XLSX, ".xlsx"),
    "application/vnd.ms-excel": (DocumentFormat.XLSX, ".xls"),
    "text/csv": (DocumentFormat.CSV, ".csv"),
    "text/plain": (DocumentFormat.TXT, ".txt"),
    "text/markdown": (DocumentFormat.MARKDOWN, ".md"),
    "text/x-markdown": (DocumentFormat.MARKDOWN, ".md"),
    "text/html": (DocumentFormat.HTML, ".html"),
    "application/xhtml+xml": (DocumentFormat.HTML, ".html"),
    "text/xml": (DocumentFormat.XML, ".xml"),
    "application/xml": (DocumentFormat.XML, ".xml"),
    "image/png": (DocumentFormat.IMAGE, ".png"),
    "image/jpeg": (DocumentFormat.IMAGE, ".jpg"),
    "image/webp": (DocumentFormat.IMAGE, ".webp"),
    "image/gif": (DocumentFormat.IMAGE, ".gif"),
    "image/bmp": (DocumentFormat.IMAGE, ".bmp"),
    "image/tiff": (DocumentFormat.IMAGE, ".tiff"),
    "application/zip": (DocumentFormat.ZIP, ".zip"),
    "application/x-zip-compressed": (DocumentFormat.ZIP, ".zip"),
}

# File extension mapping dictionary
EXT_MAP = {
    ".pdf": (DocumentFormat.PDF, "application/pdf"),
    ".docx": (DocumentFormat.DOCX, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ".doc": (DocumentFormat.DOCX, "application/msword"),
    ".pptx": (DocumentFormat.PPTX, "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    ".ppt": (DocumentFormat.PPTX, "application/vnd.ms-powerpoint"),
    ".xlsx": (DocumentFormat.XLSX, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ".xls": (DocumentFormat.XLSX, "application/vnd.ms-excel"),
    ".csv": (DocumentFormat.CSV, "text/csv"),
    ".txt": (DocumentFormat.TXT, "text/plain"),
    ".md": (DocumentFormat.MARKDOWN, "text/markdown"),
    ".markdown": (DocumentFormat.MARKDOWN, "text/markdown"),
    ".html": (DocumentFormat.HTML, "text/html"),
    ".htm": (DocumentFormat.HTML, "text/html"),
    ".xml": (DocumentFormat.XML, "application/xml"),
    ".png": (DocumentFormat.IMAGE, "image/png"),
    ".jpg": (DocumentFormat.IMAGE, "image/jpeg"),
    ".jpeg": (DocumentFormat.IMAGE, "image/jpeg"),
    ".webp": (DocumentFormat.IMAGE, "image/webp"),
    ".gif": (DocumentFormat.IMAGE, "image/gif"),
    ".bmp": (DocumentFormat.IMAGE, "image/bmp"),
    ".tiff": (DocumentFormat.IMAGE, "image/tiff"),
    ".zip": (DocumentFormat.ZIP, "application/zip"),
}


class FormatDetector(IFormatDetector):
    """Format Detector using magic bytes, MIME type, and file extension."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("FormatDetector")

    async def detect(
        self,
        source: Union[str, bytes, BinaryIO],
        mime_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> FormatDetectionResult:
        """Detect document format from input source."""
        head_bytes: Optional[bytes] = None
        target_filename: str = filename or ""

        # Extract head bytes & filename
        if isinstance(source, str):
            if os.path.exists(source):
                target_filename = target_filename or os.path.basename(source)
                try:
                    with open(source, "rb") as f:
                        head_bytes = f.read(2048)
                except Exception:
                    head_bytes = None
            else:
                # Source might be plain text string
                head_bytes = source.encode("utf-8")[:2048]
        elif isinstance(source, bytes):
            head_bytes = source[:2048]
        elif hasattr(source, "read"):
            try:
                current_pos = source.tell() if hasattr(source, "tell") else 0
                head_bytes = source.read(2048)
                if hasattr(source, "seek"):
                    source.seek(current_pos)
            except Exception:
                head_bytes = None

        # 1. Check Magic Bytes
        if head_bytes:
            magic_result = detect_format_from_bytes(head_bytes)
            if magic_result:
                fmt, detected_mime, ext = magic_result
                # Differentiate Office OpenXML formats (DOCX, PPTX, XLSX) from plain ZIP
                if fmt == DocumentFormat.ZIP:
                    office_fmt = self._check_office_xml(source, target_filename, mime_type)
                    if office_fmt:
                        return office_fmt

                self._logger.debug(f"Detected format '{fmt.value}' via magic bytes")
                return FormatDetectionResult(
                    format=fmt,
                    mime_type=detected_mime,
                    extension=ext,
                    confidence=0.95,
                    detected_by="magic_bytes",
                )

        # 2. Check explicitly provided MIME type
        if mime_type and mime_type.lower() in MIME_MAP:
            fmt, ext = MIME_MAP[mime_type.lower()]
            self._logger.debug(f"Detected format '{fmt.value}' via MIME type '{mime_type}'")
            return FormatDetectionResult(
                format=fmt,
                mime_type=mime_type.lower(),
                extension=ext,
                confidence=0.85,
                detected_by="mime_type",
            )

        # 3. Check File Extension
        ext = os.path.splitext(target_filename.lower())[1] if target_filename else ""
        if ext in EXT_MAP:
            fmt, mapped_mime = EXT_MAP[ext]
            self._logger.debug(f"Detected format '{fmt.value}' via file extension '{ext}'")
            return FormatDetectionResult(
                format=fmt,
                mime_type=mapped_mime,
                extension=ext,
                confidence=0.75,
                detected_by="extension",
            )

        # Fallback to plain text if string content
        if isinstance(source, str) and not os.path.exists(source):
            return FormatDetectionResult(
                format=DocumentFormat.TXT,
                mime_type="text/plain",
                extension=".txt",
                confidence=0.50,
                detected_by="fallback_string",
            )

        # Unknown format fallback
        return FormatDetectionResult(
            format=DocumentFormat.UNKNOWN,
            mime_type=mime_type or "application/octet-stream",
            extension=ext or ".bin",
            confidence=0.10,
            detected_by="unknown",
        )

    def _check_office_xml(
        self,
        source: Union[str, bytes, BinaryIO],
        filename: str,
        mime_type: Optional[str],
    ) -> Optional[FormatDetectionResult]:
        """Differentiate DOCX, PPTX, XLSX from ZIP based on extension or MIME type."""
        ext = os.path.splitext(filename.lower())[1] if filename else ""
        if ext in [".docx", ".doc"]:
            return FormatDetectionResult(DocumentFormat.DOCX, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx", 0.90, "zip_office_ext")
        elif ext in [".pptx", ".ppt"]:
            return FormatDetectionResult(DocumentFormat.PPTX, "application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx", 0.90, "zip_office_ext")
        elif ext in [".xlsx", ".xls"]:
            return FormatDetectionResult(DocumentFormat.XLSX, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx", 0.90, "zip_office_ext")

        if mime_type and "wordprocessingml" in mime_type:
            return FormatDetectionResult(DocumentFormat.DOCX, mime_type, ".docx", 0.90, "zip_office_mime")
        elif mime_type and "presentationml" in mime_type:
            return FormatDetectionResult(DocumentFormat.PPTX, mime_type, ".pptx", 0.90, "zip_office_mime")
        elif mime_type and "spreadsheetml" in mime_type:
            return FormatDetectionResult(DocumentFormat.XLSX, mime_type, ".xlsx", 0.90, "zip_office_mime")

        return None
