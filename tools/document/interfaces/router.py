"""File Router Interface."""

from abc import ABC, abstractmethod
from typing import Optional, Union, BinaryIO
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext
from tools.document.interfaces.parser import IDocumentParser


class IFileRouter(ABC):
    """Interface for File Router validating incoming files and selecting correct parser."""

    @abstractmethod
    async def route_and_parse(
        self,
        source: Union[str, bytes, BinaryIO],
        mime_type: Optional[str] = None,
        filename: Optional[str] = None,
        context: Optional[ProcessingContext] = None,
    ) -> NormalizedDocument:
        """Validate input file, detect format, select parser, and execute initial parsing."""

    @abstractmethod
    def resolve_parser(
        self,
        source: Union[str, bytes, BinaryIO],
        mime_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> IDocumentParser:
        """Resolve correct IDocumentParser for input source."""
