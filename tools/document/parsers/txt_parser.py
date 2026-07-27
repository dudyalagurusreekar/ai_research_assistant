"""Plain Text Document Parser."""

from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError


class TXTParser(BaseDocumentParser):
    """Parser strategy for plain text (.txt) documents."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.TXT, DocumentFormat.UNKNOWN]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "document.txt") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "document.txt")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="text/plain")

        try:
            # Encoding detection / decoding
            try:
                text_str = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_str = raw_bytes.decode("latin1", errors="replace")

            doc.full_text = text_str.strip()
            doc.add_section(title="Main Content", level=1, content=doc.full_text)

        except Exception as e:
            self._logger.error(f"Failed to parse text document: {e}")
            raise DocumentParsingError(file_name, str(e)) from e

        return doc
