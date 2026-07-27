"""CSV Document Parser using csv module / pandas."""

import csv
import io
from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument, DocumentTable
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError


class CSVParser(BaseDocumentParser):
    """Parser strategy for CSV documents."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.CSV]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "data.csv") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "data.csv")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="text/csv")

        try:
            text_str = raw_bytes.decode("utf-8", errors="replace")
            doc.full_text = text_str

            # Parse CSV content into matrix
            reader = csv.reader(io.StringIO(text_str))
            matrix: List[List[str]] = [row for row in reader if row]

            if matrix:
                headers = matrix[0]
                rows = matrix[1:] if len(matrix) > 1 else []
                tbl = DocumentTable(
                    caption=f"CSV Table ({file_name})",
                    headers=headers,
                    rows=rows,
                    matrix=matrix,
                    csv_content=text_str,
                )
                doc.tables.append(tbl)

            doc.add_section(title=f"CSV Data ({file_name})", level=1, content=text_str[:2000])

        except Exception as e:
            self._logger.error(f"Failed to parse CSV document: {e}")
            raise DocumentParsingError(file_name, str(e)) from e

        return doc
