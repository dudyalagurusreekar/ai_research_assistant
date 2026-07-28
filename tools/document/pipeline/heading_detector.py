"""HeadingDetectorStep for detecting section hierarchy from Markdown, HTML, or plain text headings."""

import re
from typing import List
from tools.document.interfaces.pipeline import IPipelineStep
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext


class HeadingDetectorStep(IPipelineStep):
    """Pipeline step detecting headings and building section structures."""

    @property
    def name(self) -> str:
        return "HeadingDetectorStep"

    async def process(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        if not context.config.enable_heading_detection or not document.full_text:
            return document

        # If sections are already populated by parser (e.g. HTML/Markdown), skip rebuild
        if len(document.sections) > 0:
            return document

        lines = document.full_text.splitlines()
        current_section = None
        current_content: List[str] = []

        for line in lines:
            line_str = line.strip()
            # Markdown header match `# Title`
            md_match = re.match(r"^(#{1,6})\s+(.+)$", line_str)
            # Capitalized short line heading heuristic
            cap_match = (
                not md_match
                and len(line_str) > 3
                and len(line_str) < 60
                and line_str.isupper()
                and not line_str.endswith(".")
            )

            if md_match or cap_match:
                # Save previous section
                if current_section:
                    current_section.content = "\n".join(current_content).strip()
                    current_content.clear()

                level = len(md_match.group(1)) if md_match else 2
                title = md_match.group(2) if md_match else line_str.title()
                current_section = document.add_section(title=title, level=level)
            else:
                if current_section:
                    current_content.append(line)

        if current_section and current_content:
            current_section.content = "\n".join(current_content).strip()

        return document
