"""Unit tests for FormatDetector."""

import asyncio
from tools.document.detector.format_detector import FormatDetector
from tools.document.models.format import DocumentFormat


def test_format_detector_magic_bytes_pdf():
    async def _test():
        detector = FormatDetector()
        pdf_bytes = b"%PDF-1.4 header contents"
        res = await detector.detect(pdf_bytes)
        assert res.format == DocumentFormat.PDF
        assert res.mime_type == "application/pdf"
        assert res.detected_by == "magic_bytes"

    asyncio.run(_test())


def test_format_detector_mime_type():
    async def _test():
        detector = FormatDetector()
        res = await detector.detect(b"some content", mime_type="text/csv")
        assert res.format == DocumentFormat.CSV
        assert res.mime_type == "text/csv"

    asyncio.run(_test())


def test_format_detector_file_extension():
    async def _test():
        detector = FormatDetector()
        res = await detector.detect(b"some content", filename="sample.md")
        assert res.format == DocumentFormat.MARKDOWN
        assert res.extension == ".md"

    asyncio.run(_test())


def test_format_detector_html():
    async def _test():
        detector = FormatDetector()
        html_bytes = b"<!DOCTYPE html><html><body><h1>Test</h1></body></html>"
        res = await detector.detect(html_bytes)
        assert res.format == DocumentFormat.HTML

    asyncio.run(_test())
