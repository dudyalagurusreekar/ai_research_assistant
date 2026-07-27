"""HeaderFooterStep for detecting and stripping repeated headers and footers."""

import re
from typing import Dict, List
from tools.document.interfaces.pipeline import IPipelineStep
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext


class HeaderFooterStep(IPipelineStep):
    """Pipeline step detecting and removing recurring top/bottom header & footer patterns."""

    @property
    def name(self) -> str:
        return "HeaderFooterStep"

    async def process(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        if not context.config.enable_header_footer_removal or not document.full_text:
            return document

        # Split into page-like or block-like chunks
        blocks = document.full_text.split("\n\n")
        if len(blocks) < 3:
            return document

        # Identify lines occurring at top or bottom of blocks repeatedly
        top_lines: Dict[str, int] = {}
        bottom_lines: Dict[str, int] = {}

        for block in blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            if lines:
                first = lines[0]
                last = lines[-1]
                if len(first) < 80 and not first.startswith("#"):
                    top_lines[first] = top_lines.get(first, 0) + 1
                if len(last) < 80 and not last.startswith("#"):
                    bottom_lines[last] = bottom_lines.get(last, 0) + 1

        # Identify headers/footers appearing in >40% of blocks
        threshold = max(2, int(len(blocks) * 0.4))
        repeated_patterns = set(
            [line for line, count in top_lines.items() if count >= threshold]
            + [line for line, count in bottom_lines.items() if count >= threshold]
        )

        if not repeated_patterns:
            return document

        cleaned_text = document.full_text
        for pattern in repeated_patterns:
            cleaned_text = re.sub(rf"^\s*{re.escape(pattern)}\s*$", "", cleaned_text, flags=re.MULTILINE)

        document.full_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()
        return document
