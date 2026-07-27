"""XML Document Parser using ElementTree."""

import xml.etree.ElementTree as ET
from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError


class XMLParser(BaseDocumentParser):
    """Parser strategy for XML documents."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.XML]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "document.xml") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "document.xml")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="application/xml")

        try:
            root = ET.fromstring(raw_bytes)
            doc.metadata.title = f"XML Root: <{root.tag}>"

            # Recursive XML element walker
            elements_text: List[str] = []

            def _walk(elem, level=1):
                tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                elem_text = elem.text.strip() if elem.text else ""

                if elem_text:
                    elements_text.append(f"<{tag_name}>: {elem_text}")
                    doc.add_paragraph(text=f"{tag_name}: {elem_text}")

                if len(list(elem)) > 0:
                    doc.add_section(title=f"<{tag_name}>", level=min(6, level))

                for child in elem:
                    _walk(child, level + 1)

            _walk(root)

            doc.full_text = "\n".join(elements_text).strip()
            if not doc.full_text:
                doc.full_text = raw_bytes.decode("utf-8", errors="replace")

        except Exception as e:
            self._logger.error(f"Failed to parse XML document: {e}")
            raise DocumentParsingError(file_name, str(e)) from e

        return doc
