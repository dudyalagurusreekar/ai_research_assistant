"""Semantic and Structure-Aware Document Chunking Engine."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from core.rag.parsers.base import ParsedDocument, ParsedSection


@dataclass
class DocumentChunkData:
    """Dataclass holding chunk content and metadata."""
    content: str
    chunk_index: int
    token_count: int
    metadata: Dict[str, Any]


class SemanticChunker:
    """Structure-aware semantic chunker respecting headings, paragraphs, and token limits."""

    def __init__(self, max_tokens: int = 500, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_document(self, parsed_doc: ParsedDocument) -> List[DocumentChunkData]:
        """Chunk document respecting section boundaries and token budgets."""
        chunks = []
        chunk_idx = 0

        # Process structured sections if available
        if parsed_doc.sections:
            for section in parsed_doc.sections:
                sec_chunks = self._chunk_text(
                    text=section.content,
                    heading=section.heading,
                    start_index=chunk_idx,
                    doc_metadata=parsed_doc.metadata,
                )
                chunks.extend(sec_chunks)
                chunk_idx += len(sec_chunks)
        else:
            sec_chunks = self._chunk_text(
                text=parsed_doc.raw_text,
                heading=parsed_doc.title,
                start_index=0,
                doc_metadata=parsed_doc.metadata,
            )
            chunks.extend(sec_chunks)

        return chunks

    def _chunk_text(self, text: str, heading: str, start_index: int, doc_metadata: dict) -> List[DocumentChunkData]:
        words = text.split()
        if not words:
            return []

        chunks = []
        idx = 0
        current_index = start_index

        while idx < len(words):
            chunk_words = words[idx : idx + self.max_tokens]
            chunk_text = f"## {heading}\n" + " ".join(chunk_words) if heading else " ".join(chunk_words)
            
            chunks.append(
                DocumentChunkData(
                    content=chunk_text.strip(),
                    chunk_index=current_index,
                    token_count=len(chunk_words),
                    metadata={"section_heading": heading, **doc_metadata},
                )
            )
            current_index += 1
            idx += max(1, self.max_tokens - self.overlap_tokens)

        return chunks


class TableStructureChunker:
    """Specialized chunker preserving markdown tables and JSON objects."""

    @staticmethod
    def chunk_tables(parsed_doc: ParsedDocument) -> List[DocumentChunkData]:
        """Convert extracted tables into structured markdown table chunks."""
        chunks = []
        for idx, table in enumerate(parsed_doc.tables):
            headers_str = "| " + " | ".join(table.headers) + " |"
            sep_str = "| " + " | ".join(["---"] * len(table.headers)) + " |"
            row_strs = ["| " + " | ".join(r) + " |" for r in table.rows]
            
            table_markdown = "\n".join([f"### Table: {table.caption}", headers_str, sep_str] + row_strs)
            chunks.append(
                DocumentChunkData(
                    content=table_markdown,
                    chunk_index=idx,
                    token_count=len(table_markdown.split()),
                    metadata={"is_table": True, "caption": table.caption},
                )
            )
        return chunks
