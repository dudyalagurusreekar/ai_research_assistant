"""Unit tests for DocumentToolFacade."""

import asyncio
from tools.document.facade.facade import DocumentToolFacade
from tools.document.models.document import NormalizedDocument


def test_document_tool_facade_parse_and_extract():
    async def _test():
        facade = DocumentToolFacade()
        sample_text = (
            "# Artificial Intelligence\n\n"
            "AI is revolutionizing document processing and knowledge extraction.\n\n"
            "## Features\n\n"
            "- Clean Architecture\n- SOLID principles\n- Dynamic parsers\n"
        )

        doc = await facade.parse_document(sample_text.encode("utf-8"), filename="test_doc.md")
        assert isinstance(doc, NormalizedDocument)
        assert doc.metadata.file_name == "test_doc.md"
        assert doc.metadata.word_count > 0
        assert len(doc.sections) == 2
        assert len(doc.chunks) > 0

        # Test read_document
        read_text = await facade.read_document(sample_text.encode("utf-8"))
        assert "Artificial Intelligence" in read_text

        # Test chunk_document
        chunks = await facade.chunk_document(sample_text.encode("utf-8"), chunk_size=50)
        assert len(chunks) > 0

        # Test summarize_document
        summary = await facade.summarize_document(sample_text.encode("utf-8"))
        assert summary.summary_text != ""

    asyncio.run(_test())
