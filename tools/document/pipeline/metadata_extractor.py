"""MetadataExtractorStep for populating word, line, and page counts."""

import re
from tools.document.interfaces.pipeline import IPipelineStep
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext


class MetadataExtractorStep(IPipelineStep):
    """Pipeline step computing document metadata metrics."""

    @property
    def name(self) -> str:
        return "MetadataExtractorStep"

    async def process(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        text = document.full_text or ""
        words = re.findall(r"\w+", text)
        lines = [l for l in text.splitlines() if l.strip()]

        document.metadata.word_count = len(words)
        document.metadata.line_count = len(lines)
        if document.metadata.page_count == 0:
            document.metadata.page_count = max(1, len(lines) // 40)

        if not document.metadata.title and lines:
            document.metadata.title = lines[0][:100]

        return document
