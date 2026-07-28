"""Parser & ParserRegistry Interfaces."""

from abc import ABC, abstractmethod
from typing import Optional, Union, BinaryIO, List
from tools.document.models.document import NormalizedDocument
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext


class IDocumentParser(ABC):
    """Interface for concrete format parsers transforming files into NormalizedDocument."""

    @property
    @abstractmethod
    def supported_formats(self) -> List[DocumentFormat]:
        """Return list of supported document formats for this parser."""

    @abstractmethod
    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        """Parse source document into NormalizedDocument."""


class IParserRegistry(ABC):
    """Interface for dynamic Parser Registry managing format parser implementations."""

    @abstractmethod
    def register(self, parser: IDocumentParser) -> None:
        """Register a document parser strategy."""

    @abstractmethod
    def get_parser(self, doc_format: DocumentFormat) -> Optional[IDocumentParser]:
        """Retrieve parser strategy for a given format."""

    @abstractmethod
    def list_supported_formats(self) -> List[DocumentFormat]:
        """List all supported formats across registered parsers."""
