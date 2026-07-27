"""PDF Document Parser using PyPDF2 with stream fallback."""

import io
from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


class PDFParser(BaseDocumentParser):
    """Parser strategy for PDF documents."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.PDF]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "document.pdf") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "document.pdf")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="application/pdf")

        if not PYPDF2_AVAILABLE:
            context.add_warning("PyPDF2 is not installed; returning fallback raw stream text extraction.")
            doc.full_text = f"[PDF Document ({len(raw_bytes)} bytes)]\n" + raw_bytes.decode("latin1", errors="ignore")[:2000]
            return doc

        try:
            reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
            doc.metadata.page_count = len(reader.pages)

            # Extract Document Metadata Info
            if reader.metadata:
                doc.metadata.title = reader.metadata.get("/Title") or doc.metadata.title
                doc.metadata.author = reader.metadata.get("/Author")
                doc.metadata.creation_date = str(reader.metadata.get("/CreationDate")) if reader.metadata.get("/CreationDate") else None

            # Extract Text Page by Page
            page_texts: List[str] = []
            for idx, page in enumerate(reader.pages):
                try:
                    txt = page.extract_text() or ""
                    if txt.strip():
                        page_texts.append(txt)
                        # Add page section
                        doc.add_section(
                            title=f"Page {idx + 1}",
                            level=2,
                            content=txt.strip(),
                        )
                except Exception as pe:
                    self._logger.warning(f"Error extracting text from PDF page {idx + 1}: {pe}")

            doc.full_text = "\n\n".join(page_texts).strip()

            # Fallback if no text extracted (e.g. scanned image PDF)
            if not doc.full_text:
                context.add_warning("PDF text extraction yielded empty text. Document may be a scanned image PDF.")
                doc.full_text = f"[PDF Document ({doc.metadata.page_count} pages, {len(raw_bytes)} bytes)]"

        except Exception as e:
            self._logger.error(f"Failed to parse PDF document: {e}")
            raise DocumentParsingError(file_name, str(e)) from e

        return doc
