"""XLSX Spreadsheet Parser using Pandas / OpenPyXL / Zip XML."""

import io
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument, DocumentTable
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class XLSXParser(BaseDocumentParser):
    """Parser strategy for Excel (.xlsx) spreadsheets."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.XLSX]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "spreadsheet.xlsx") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "spreadsheet.xlsx")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if PANDAS_AVAILABLE:
            try:
                excel_file = pd.ExcelFile(io.BytesIO(raw_bytes))
                doc.metadata.page_count = len(excel_file.sheet_names)
                sheet_texts: List[str] = []

                for sheet_name in excel_file.sheet_names:
                    df = excel_file.parse(sheet_name)
                    if df.empty:
                        continue

                    # Fill NaNs with empty string
                    df = df.fillna("")
                    headers = [str(col) for col in df.columns]
                    rows = [[str(val) for val in row] for row in df.values]
                    matrix = [headers] + rows

                    # Add table object
                    tbl = DocumentTable(
                        caption=f"Sheet: {sheet_name}",
                        headers=headers,
                        rows=rows,
                        matrix=matrix,
                        csv_content=df.to_csv(index=False),
                    )
                    doc.tables.append(tbl)

                    sheet_str = f"--- Sheet: {sheet_name} ---\n" + df.to_string(index=False)
                    sheet_texts.append(sheet_str)
                    doc.add_section(title=f"Sheet: {sheet_name}", level=2, content=sheet_str)

                doc.full_text = "\n\n".join(sheet_texts).strip()
                return doc

            except Exception as e:
                self._logger.debug(f"Pandas Excel reading failed ({e}); falling back to zip xml parsing.")

        # Fallback ZIP+XML sheet parsing
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                sheet_files = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
                doc.metadata.page_count = len(sheet_files)
                doc.full_text = f"[Excel Spreadsheet ({len(sheet_files)} sheets, {len(raw_bytes)} bytes)]"
        except Exception as ze:
            raise DocumentParsingError(file_name, str(ze)) from ze

        return doc
