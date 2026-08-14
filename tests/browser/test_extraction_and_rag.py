"""Integration tests for Browser Data Extraction & Download RAG Ingestion."""

import asyncio
import pytest
from core.browser.extraction_engine import ExtractionEngine
from core.browser.download_manager import DownloadManager
from core.browser.dom_intelligence import DOMIntelligenceEngine


def test_extraction_engine_tables():
    async def _test():
        engine = ExtractionEngine()
        session = {"session_id": "bs_ext_01", "page": None, "current_url": "https://ncbi.nlm.nih.gov"}

        result = await engine.extract_content(session)
        assert result.url == "https://ncbi.nlm.nih.gov"
        assert len(result.tables) > 0
        assert result.tables[0][0][0] == "Gene Target"

    asyncio.run(_test())


def test_download_manager_ingestion():
    async def _test():
        dl_mgr = DownloadManager()
        pdf_bytes = b"%PDF-1.4 Fake Test Paper Data"

        download = await dl_mgr.handle_download(
            session_id="bs_dl_01",
            download_url="https://nature.com/paper.pdf",
            filename="paper.pdf",
            file_bytes=pdf_bytes,
        )

        assert download.filename == "paper.pdf"
        assert download.file_size == len(pdf_bytes)
        assert download.rag_document_id is not None

    asyncio.run(_test())


def test_dom_intelligence_truncation():
    async def _test():
        dom_intel = DOMIntelligenceEngine()
        session = {"session_id": "bs_dom_01", "page": None}

        nodes = await dom_intel.get_interactive_elements(session)
        assert len(nodes) > 0

        truncated_str = dom_intel.truncate_dom_for_llm(nodes)
        assert "# Interactive Page Elements:" in truncated_str
        assert "selector=" in truncated_str

    asyncio.run(_test())
