"""CleanerStep for normalizing text and removing control characters."""

from tools.document.interfaces.pipeline import IPipelineStep
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext
from tools.document.utils.text_helpers import clean_text_content


class CleanerStep(IPipelineStep):
    """Pipeline step for cleaning document text content."""

    @property
    def name(self) -> str:
        return "CleanerStep"

    async def process(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        if not context.config.enable_cleaning:
            return document

        document.full_text = clean_text_content(document.full_text)

        # Clean paragraphs
        for par in document.paragraphs:
            par.text = clean_text_content(par.text)

        # Clean sections
        for sec in document.sections:
            sec.content = clean_text_content(sec.content)

        return document
