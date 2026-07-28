"""Format Detector Interface."""

from abc import ABC, abstractmethod
from typing import Optional, Union, BinaryIO
from tools.document.models.format import FormatDetectionResult


class IFormatDetector(ABC):
    """Interface for detecting document format via MIME type, magic bytes, and file extension."""

    @abstractmethod
    async def detect(
        self,
        source: Union[str, bytes, BinaryIO],
        mime_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> FormatDetectionResult:
        """Detect document format from input source."""
