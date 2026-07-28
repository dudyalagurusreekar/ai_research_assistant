"""Base abstract class for all document parsers."""

import os
from abc import ABC
from typing import Union, BinaryIO
from tools.document.interfaces.parser import IDocumentParser
from tools.document.models.document import NormalizedDocument
from tools.document.utils.text_helpers import compute_sha256
from infrastructure.logging.logger import StructuredLogger


class BaseDocumentParser(IDocumentParser, ABC):
    """Abstract base class providing shared loading, hashing, and metadata utilities for parsers."""

    def __init__(self) -> None:
        self._logger = StructuredLogger(self.__class__.__name__)

    def _read_bytes(self, source: Union[str, bytes, BinaryIO]) -> bytes:
        """Extract raw bytes from string path, bytes, or file-like object."""
        if isinstance(source, bytes):
            return source
        elif isinstance(source, str):
            if os.path.exists(source):
                with open(source, "rb") as f:
                    return f.read()
            else:
                return source.encode("utf-8")
        elif hasattr(source, "read"):
            current_pos = source.tell() if hasattr(source, "tell") else 0
            data = source.read()
            if hasattr(source, "seek"):
                source.seek(current_pos)
            return data
        return b""

    def _create_initial_document(
        self,
        source: Union[str, bytes, BinaryIO],
        file_name: str = "document",
        mime_type: str = "application/octet-stream",
    ) -> NormalizedDocument:
        """Helper to create initialized NormalizedDocument instance."""
        raw_bytes = self._read_bytes(source)
        file_hash = compute_sha256(raw_bytes) if raw_bytes else None

        doc = NormalizedDocument()
        doc.metadata.file_name = file_name
        doc.metadata.mime_type = mime_type
        doc.metadata.file_size_bytes = len(raw_bytes)
        doc.metadata.file_hash = file_hash
        return doc
