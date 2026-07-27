"""DOCX Document Parser using python-docx with XML fallback."""

import io
from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument, DocumentTable
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class DOCXParser(BaseDocumentParser):
    """Parser strategy for Word (.docx) documents."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.DOCX]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "document.docx") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "document.docx")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        if not DOCX_AVAILABLE:
            context.add_warning("python-docx is not available; returning text extracted via raw string decode.")
            doc.full_text = raw_bytes.decode("utf-8", errors="ignore")
            return doc

        try:
            docx_doc = docx.Document(io.BytesIO(raw_bytes))

            # Core properties metadata
            if docx_doc.core_properties:
                doc.metadata.title = docx_doc.core_properties.title or doc.metadata.title
                doc.metadata.author = docx_doc.core_properties.author
                if docx_doc.core_properties.created:
                    doc.metadata.creation_date = str(docx_doc.core_properties.created)

            # Paragraphs & Headings
            paragraph_texts: List[str] = []
            current_sec = None

            for p in docx_doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue

                paragraph_texts.append(text)

                if p.style and p.style.name and p.style.name.startswith("Heading"):
                    try:
                        level = int(p.style.name.replace("Heading", "").strip())
                    except ValueError:
                        level = 2
                    current_sec = doc.add_section(title=text, level=level)
                else:
                    doc.add_paragraph(text=text, section_id=current_sec.section_id if current_sec else None)

            # Tables
            for idx, table in enumerate(docx_doc.tables):
                table_matrix: List[List[str]] = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    table_matrix.append(row_cells)

                if table_matrix:
                    headers = table_matrix[0] if len(table_matrix) > 0 else []
                    rows = table_matrix[1:] if len(table_matrix) > 1 else []
                    tbl_obj = DocumentTable(
                        caption=f"Table {idx + 1}",
                        headers=headers,
                        rows=rows,
                        matrix=table_matrix,
                    )
                    doc.tables.append(tbl_obj)

            doc.full_text = "\n\n".join(paragraph_texts).strip()

        except Exception as e:
            self._logger.error(f"Failed to parse DOCX document: {e}")
            raise DocumentParsingError(file_name, str(e)) from e

        return doc
