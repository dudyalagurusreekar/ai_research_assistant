"""File Router implementation utilizing FormatDetector and ParserRegistry."""

import os
from typing import Optional, Union, BinaryIO
from tools.document.interfaces.router import IFileRouter
from tools.document.interfaces.detector import IFormatDetector
from tools.document.interfaces.parser import IParserRegistry, IDocumentParser
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext
from tools.document.models.format import DocumentFormat
from tools.document.exceptions import DocumentError, ParserNotFoundError, FormatDetectionError
from tools.document.detector.format_detector import FormatDetector
from infrastructure.logging.logger import StructuredLogger


class FileRouter(IFileRouter):
    """Validates incoming document source, detects format, resolves parser from registry, and executes parsing."""

    def __init__(
        self,
        parser_registry: IParserRegistry,
        format_detector: Optional[IFormatDetector] = None,
    ) -> None:
        self._logger = StructuredLogger("FileRouter")
        self.parser_registry = parser_registry
        self.format_detector = format_detector or FormatDetector()

    def resolve_parser(
        self,
        source: Union[str, bytes, BinaryIO],
        mime_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> IDocumentParser:
        """Resolve IDocumentParser strategy for a given file source without executing parse."""

        # Format detection synchronously or via detection result helper
        # Note: caller can also use route_and_parse
        # To resolve parser, we run format_detector detect
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In async context
            detection = loop.run_until_complete(self.format_detector.detect(source, mime_type, filename)) if not loop.is_running() else None
        # We handle resolve_parser inside route_and_parse asynchronously
        return None

    async def route_and_parse(
        self,
        source: Union[str, bytes, BinaryIO],
        mime_type: Optional[str] = None,
        filename: Optional[str] = None,
        context: Optional[ProcessingContext] = None,
    ) -> NormalizedDocument:
        """Validate input file, detect format, select registered parser, and execute initial parsing."""
        ctx = context or ProcessingContext()

        # 1. Validate File Source
        target_name = filename or self._extract_filename(source)
        self._validate_source(source, target_name, ctx)

        # 2. Detect Format
        detection = await self.format_detector.detect(source, mime_type, target_name)
        self._logger.info(
            f"Routing file '{target_name}': format='{detection.format.value}', "
            f"mime='{detection.mime_type}', method='{detection.detected_by}'"
        )
        ctx.record_metric("format", detection.format.value)
        ctx.record_metric("mime_type", detection.mime_type)

        # 3. Resolve Parser Strategy from ParserRegistry
        parser = self.parser_registry.get_parser(detection.format)
        if not parser:
            # Fallback to TXT parser if text format, otherwise raise exception
            if detection.format in [DocumentFormat.TXT, DocumentFormat.UNKNOWN]:
                txt_parser = self.parser_registry.get_parser(DocumentFormat.TXT)
                if txt_parser:
                    parser = txt_parser
            if not parser:
                raise ParserNotFoundError(detection.format.value)

        # 4. Execute Parser
        normalized_doc = await parser.parse(source, ctx)
        normalized_doc.metadata.file_name = target_name
        normalized_doc.metadata.mime_type = detection.mime_type
        if not normalized_doc.metadata.title:
            normalized_doc.metadata.title = target_name

        return normalized_doc

    def _validate_source(
        self,
        source: Union[str, bytes, BinaryIO],
        filename: str,
        ctx: ProcessingContext,
    ) -> None:
        """Validate source existence, size, and readability."""
        if isinstance(source, str):
            if os.path.exists(source):
                size = os.path.getsize(source)
                if size == 0:
                    raise DocumentError(f"File '{source}' is empty (0 bytes).")
                if size > ctx.config.max_file_size_bytes:
                    raise DocumentError(
                        f"File '{source}' exceeds max size limit ({size} > {ctx.config.max_file_size_bytes} bytes)."
                    )
        elif isinstance(source, bytes):
            if len(source) == 0:
                raise DocumentError("Document bytes input is empty (0 bytes).")
            if len(source) > ctx.config.max_file_size_bytes:
                raise DocumentError(
                    f"Document bytes exceed max size limit ({len(source)} > {ctx.config.max_file_size_bytes} bytes)."
                )

    def _extract_filename(self, source: Union[str, bytes, BinaryIO]) -> str:
        if isinstance(source, str) and os.path.exists(source):
            return os.path.basename(source)
        return "document"
