"""PPTX Presentation Parser using Zip Archive and Slide XML parsing."""

import io
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError


class PPTXParser(BaseDocumentParser):
    """Parser strategy for PowerPoint (.pptx) presentation files."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.PPTX]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "presentation.pptx") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "presentation.pptx")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")

        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                # Find slide XML files (ppt/slides/slide1.xml, slide2.xml...)
                slide_names = [name for name in zf.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
                # Sort slide files numerically
                slide_names.sort(key=lambda x: int("".join(filter(str.isdigit, x)) or 0))

                doc.metadata.page_count = len(slide_names)
                all_slide_texts: List[str] = []

                for idx, slide_path in enumerate(slide_names):
                    slide_xml = zf.read(slide_path)
                    root = ET.fromstring(slide_xml)
                    # Extract all text nodes <a:t>
                    text_nodes = root.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}t")
                    texts = [node.text.strip() for node in text_nodes if node.text and node.text.strip()]

                    slide_title = texts[0] if texts else f"Slide {idx + 1}"
                    slide_content = "\n".join(texts)

                    doc.add_section(
                        title=f"Slide {idx + 1}: {slide_title[:50]}",
                        level=2,
                        content=slide_content,
                    )
                    all_slide_texts.append(f"--- Slide {idx + 1} ---\n{slide_content}")

                doc.full_text = "\n\n".join(all_slide_texts).strip()

        except Exception as e:
            self._logger.error(f"Failed to parse PPTX presentation: {e}")
            raise DocumentParsingError(file_name, str(e)) from e

        return doc
