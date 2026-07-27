"""ChunkerStep for generating sliding-window and heading-aware semantic chunks."""

import re
from typing import List, Optional
from tools.document.interfaces.pipeline import IPipelineStep
from tools.document.models.document import NormalizedDocument, DocumentChunk
from tools.document.models.context import ProcessingContext
from tools.document.utils.text_helpers import estimate_tokens


class ChunkerStep(IPipelineStep):
    """Pipeline step creating semantic chunks across sections or full text."""

    @property
    def name(self) -> str:
        return "ChunkerStep"

    async def process(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        if not context.config.enable_chunking:
            return document

        chunk_size = context.config.default_chunk_size
        chunk_overlap = context.config.default_chunk_overlap
        chunks: List[DocumentChunk] = []

        # If sections exist, chunk section by section
        if document.sections:
            for section in document.sections:
                sec_text = section.content or ""
                if not sec_text:
                    continue
                sec_chunks = self._chunk_text(
                    text=sec_text,
                    chunk_size=chunk_size,
                    overlap=chunk_overlap,
                    section_id=section.section_id,
                    section_title=section.title,
                )
                chunks.extend(sec_chunks)
        else:
            # Fallback to chunking full_text
            full_text = document.full_text or ""
            chunks = self._chunk_text(
                text=full_text,
                chunk_size=chunk_size,
                overlap=chunk_overlap,
                section_id=None,
                section_title=None,
            )

        # Set chunk indices
        for idx, chk in enumerate(chunks):
            chk.chunk_index = idx

        document.chunks = chunks
        context.record_metric("chunk_count", len(chunks))
        return document

    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
        section_id: Optional[str] = None,
        section_title: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """Sliding window chunking helper."""
        if not text.strip():
            return []

        words = text.split()
        if len(words) <= chunk_size:
            return [
                DocumentChunk(
                    text=text,
                    token_count=estimate_tokens(text),
                    section_id=section_id,
                    metadata={"section_title": section_title} if section_title else {},
                )
            ]

        chunks = []
        step = max(1, chunk_size - overlap)
        for i in range(0, len(words), step):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)
            if chunk_text.strip():
                chunks.append(
                    DocumentChunk(
                        text=chunk_text,
                        token_count=estimate_tokens(chunk_text),
                        section_id=section_id,
                        metadata={"section_title": section_title} if section_title else {},
                    )
                )
        return chunks
