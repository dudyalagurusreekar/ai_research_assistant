"""Smolagents BaseTool wrapper and Capability Registry registration for DocumentToolFacade."""

import asyncio
from typing import Any, Optional
from tools.base import BaseTool
from tools.document.facade.facade import DocumentToolFacade
from core.models.metadata import ToolMetadata


class DocumentTool(BaseTool):
    """Tool wrapper exposing Document Intelligence capabilities to agents."""

    name = "document_tool"
    description = (
        "Parses, reads, extracts text, tables, images, metadata, chunks, searches, "
        "compares, and summarizes documents across PDF, DOCX, PPTX, XLSX, CSV, TXT, MD, HTML, XML, images, and ZIP."
    )
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'parse', 'read', 'extract_tables', 'extract_images', 'metadata', 'chunk', 'search', 'compare', 'summarize'",
        },
        "source": {
            "type": "string",
            "description": "File path or raw document text/bytes to process.",
        },
        "query": {
            "type": "string",
            "description": "Optional search query string for search action.",
            "nullable": True,
        },
        "max_sentences": {
            "type": "integer",
            "description": "Max sentences for summary action.",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: Optional[DocumentToolFacade] = None) -> None:
        super().__init__()
        self.facade = facade or DocumentToolFacade()
        # Metadata for CapabilityRegistry
        self.metadata = ToolMetadata(
            name=self.name,
            version="1.0.0",
            description=self.description,
            capabilities=[
                "parse_document",
                "read_document",
                "extract_tables",
                "extract_images",
                "chunk_document",
                "search_documents",
                "compare_documents",
                "summarize_document",
            ],
            tags=["document"],
            enabled=True,
        )

    def forward(
        self,
        action: str,
        source: str,
        query: Optional[str] = None,
        max_sentences: Optional[int] = 5,
    ) -> Any:
        """Synchronous wrapper executing async facade methods."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, self._execute_async(action, source, query, max_sentences)).result()
        else:
            return loop.run_until_complete(self._execute_async(action, source, query, max_sentences))

    async def _execute_async(
        self,
        action: str,
        source: str,
        query: Optional[str],
        max_sentences: Optional[int],
    ) -> Any:
        act = action.lower().strip()
        if act == "read" or act == "extract_text":
            return await self.facade.read_document(source)
        elif act == "parse":
            doc = await self.facade.parse_document(source)
            return doc.to_dict()
        elif act == "metadata":
            meta = await self.facade.get_metadata(source)
            return meta.to_dict()
        elif act == "extract_tables":
            tables = await self.facade.extract_tables(source)
            return [t.to_dict() for t in tables]
        elif act == "extract_images":
            images = await self.facade.extract_images(source)
            return [i.to_dict() for i in images]
        elif act == "chunk":
            chunks = await self.facade.chunk_document(source)
            return [c.to_dict() for c in chunks]
        elif act == "summarize":
            summary = await self.facade.summarize_document(source, max_sentences=max_sentences or 5)
            return summary.to_dict()
        elif act == "search":
            doc = await self.facade.parse_document(source)
            results = await self.facade.search_documents(query or "", doc.chunks)
            return [r.to_dict() for r in results]
        else:
            return f"Unknown document action '{action}'"
