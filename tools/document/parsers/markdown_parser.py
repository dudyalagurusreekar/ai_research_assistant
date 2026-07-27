"""Markdown Document Parser."""

import re
from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument, DocumentReference
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import DocumentParsingError


class MarkdownParser(BaseDocumentParser):
    """Parser strategy for Markdown (.md) documents."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.MARKDOWN]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "document.md") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "document.md")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="text/markdown")

        try:
            try:
                text_str = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_str = raw_bytes.decode("latin1", errors="replace")

            doc.full_text = text_str.strip()

            # Parse Markdown Headings
            lines = text_str.splitlines()
            current_sec = None
            current_lines: List[str] = []

            for line in lines:
                h_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
                if h_match:
                    if current_sec:
                        current_sec.content = "\n".join(current_lines).strip()
                        current_lines.clear()

                    level = len(h_match.group(1))
                    title = h_match.group(2).strip()
                    current_sec = doc.add_section(title=title, level=level)
                else:
                    if current_sec:
                        current_lines.append(line)

            if current_sec and current_lines:
                current_sec.content = "\n".join(current_lines).strip()

            # Extract Markdown Links `[text](url)`
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text_str)
            for title, url in links:
                ref = DocumentReference(ref_type="link", title=title, url=url, text=f"[{title}]({url})")
                doc.references.append(ref)

        except Exception as e:
            self._logger.error(f"Failed to parse Markdown document: {e}")
            raise DocumentParsingError(file_name, str(e)) from e

        return doc
