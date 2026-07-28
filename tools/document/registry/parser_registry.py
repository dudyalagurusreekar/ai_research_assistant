"""Dynamic Parser Registry implementation."""

from typing import Dict, List, Optional
from tools.document.interfaces.parser import IDocumentParser, IParserRegistry
from tools.document.models.format import DocumentFormat
from infrastructure.logging.logger import StructuredLogger


class ParserRegistry(IParserRegistry):
    """Registry maintaining mappings between DocumentFormat types and concrete IDocumentParser instances."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ParserRegistry")
        self._registry: Dict[DocumentFormat, IDocumentParser] = {}

    def register(self, parser: IDocumentParser) -> None:
        """Register a parser strategy for all formats it supports."""
        for fmt in parser.supported_formats:
            self._registry[fmt] = parser
            self._logger.debug(f"Registered parser '{parser.__class__.__name__}' for format '{fmt.value}'")

    def get_parser(self, doc_format: DocumentFormat) -> Optional[IDocumentParser]:
        """Retrieve parser strategy for a format."""
        return self._registry.get(doc_format)

    def list_supported_formats(self) -> List[DocumentFormat]:
        """List all currently registered document formats."""
        return list(self._registry.keys())
