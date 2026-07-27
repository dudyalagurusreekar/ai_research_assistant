"""HTML Document Parser using BeautifulSoup4."""

from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import (
    NormalizedDocument,
    DocumentTable,
    DocumentImage,
    DocumentReference,
)
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class HTMLParser(BaseDocumentParser):
    """Parser strategy for HTML documents."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.HTML]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "document.html") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "document.html")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="text/html")

        if not BS4_AVAILABLE:
            context.add_warning("BeautifulSoup4 not available; falling back to raw html decode.")
            doc.full_text = raw_bytes.decode("utf-8", errors="ignore")
            return doc

        try:
            soup = BeautifulSoup(raw_bytes, "html.parser")

            # Extract Page Title
            if soup.title and soup.title.string:
                doc.metadata.title = soup.title.string.strip()

            # Extract Headings (h1-h6) and build Sections
            for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                level = int(tag.name[1])
                title = tag.get_text().strip()
                if title:
                    doc.add_section(title=title, level=level)

            # Extract Paragraphs
            for p in soup.find_all("p"):
                txt = p.get_text().strip()
                if txt:
                    doc.add_paragraph(text=txt)

            # Extract Tables
            for idx, table_tag in enumerate(soup.find_all("table")):
                matrix: List[List[str]] = []
                for tr in table_tag.find_all("tr"):
                    cells = [td.get_text().strip() for td in tr.find_all(["th", "td"])]
                    if cells:
                        matrix.append(cells)
                if matrix:
                    headers = matrix[0]
                    rows = matrix[1:] if len(matrix) > 1 else []
                    tbl = DocumentTable(
                        caption=f"HTML Table {idx + 1}",
                        headers=headers,
                        rows=rows,
                        matrix=matrix,
                    )
                    doc.tables.append(tbl)

            # Extract Images <img>
            for img_tag in soup.find_all("img"):
                src = img_tag.get("src", "")
                alt = img_tag.get("alt", "")
                if src or alt:
                    doc.images.append(
                        DocumentImage(
                            caption=alt or "HTML Image",
                            mime_type="image/png",
                        )
                    )

            # Extract Links <a>
            for a_tag in soup.find_all("a", href=True):
                url = a_tag["href"]
                txt = a_tag.get_text().strip()
                if url:
                    doc.references.append(
                        DocumentReference(
                            ref_type="link",
                            title=txt or url,
                            url=url,
                            text=txt or url,
                        )
                    )

            # Clean Full Text Extraction
            for element in soup(["script", "style", "head"]):
                element.extract()
            doc.full_text = soup.get_text(separator="\n").strip()

        except Exception as e:
            self._logger.error(f"Failed to parse HTML document: {e}")
            raise DocumentParsingError(file_name, str(e)) from e

        return doc
