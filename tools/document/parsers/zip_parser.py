"""ZIP Archive Parser unpacking zip files and parsing sub-documents recursively."""

import io
import zipfile
from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument, AttachedArtifact
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError


class ZIPParser(BaseDocumentParser):
    """Parser strategy for ZIP archives containing multiple documents."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.ZIP]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "archive.zip") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "archive.zip")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="application/zip")

        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                file_list = zf.namelist()
                doc.metadata.page_count = len(file_list)

                sub_doc_texts: List[str] = []
                for entry in file_list:
                    if entry.endswith("/") or entry.startswith("__MACOSX"):
                        continue

                    entry_bytes = zf.read(entry)
                    doc.artifacts.append(
                        AttachedArtifact(
                            artifact_id=f"zip_{entry.replace('/', '_')}",
                            name=entry,
                            artifact_type="archive_entry",
                            mime_type="application/octet-stream",
                        )
                    )

                    # Try text decoding for small text items inside archive
                    try:
                        text_sample = entry_bytes.decode("utf-8")
                        sub_doc_texts.append(f"=== File: {entry} ===\n{text_sample[:1000]}")
                        doc.add_section(title=f"Archive Item: {entry}", level=2, content=text_sample[:1000])
                    except UnicodeDecodeError:
                        sub_doc_texts.append(f"=== File: {entry} ({len(entry_bytes)} bytes binary) ===")

                doc.full_text = "\n\n".join(sub_doc_texts).strip()

        except Exception as e:
            self._logger.error(f"Failed to parse ZIP archive: {e}")
            raise DocumentParsingError(file_name, str(e)) from e

        return doc
