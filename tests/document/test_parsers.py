"""Unit tests for Document Parsers."""

import asyncio
from tools.document.models.context import ProcessingContext
from tools.document.parsers.txt_parser import TXTParser
from tools.document.parsers.markdown_parser import MarkdownParser
from tools.document.parsers.csv_parser import CSVParser
from tools.document.parsers.html_parser import HTMLParser
from tools.document.parsers.xml_parser import XMLParser
from tools.document.parsers.image_parser import ImageOCRParser


def test_txt_parser():
    async def _test():
        parser = TXTParser()
        ctx = ProcessingContext()
        doc = await parser.parse(b"Hello Plain Text World!", ctx)
        assert doc.full_text == "Hello Plain Text World!"
        assert len(doc.sections) == 1

    asyncio.run(_test())


def test_markdown_parser():
    async def _test():
        parser = MarkdownParser()
        ctx = ProcessingContext()
        md_content = b"# Document Title\n\nSection content text.\n\n## Sub Section\n\n[Google](https://google.com)"
        doc = await parser.parse(md_content, ctx)
        assert len(doc.sections) == 2
        assert doc.sections[0].title == "Document Title"
        assert len(doc.references) == 1
        assert doc.references[0].url == "https://google.com"

    asyncio.run(_test())


def test_csv_parser():
    async def _test():
        parser = CSVParser()
        ctx = ProcessingContext()
        csv_bytes = b"Name,Age,Role\nAlice,30,Engineer\nBob,25,Researcher\n"
        doc = await parser.parse(csv_bytes, ctx)
        assert len(doc.tables) == 1
        assert doc.tables[0].headers == ["Name", "Age", "Role"]
        assert len(doc.tables[0].rows) == 2

    asyncio.run(_test())


def test_html_parser():
    async def _test():
        parser = HTMLParser()
        ctx = ProcessingContext()
        html_bytes = b"<html><head><title>Test Page</title></head><body><h1>Heading 1</h1><p>Paragraph text.</p></body></html>"
        doc = await parser.parse(html_bytes, ctx)
        assert doc.metadata.title == "Test Page"
        assert len(doc.sections) == 1
        assert "Heading 1" in doc.full_text

    asyncio.run(_test())


def test_xml_parser():
    async def _test():
        parser = XMLParser()
        ctx = ProcessingContext()
        xml_bytes = b"<root><item>Item 1</item><item>Item 2</item></root>"
        doc = await parser.parse(xml_bytes, ctx)
        assert "<root>" in doc.metadata.title
        assert "Item 1" in doc.full_text

    asyncio.run(_test())


def test_image_parser():
    async def _test():
        parser = ImageOCRParser()
        ctx = ProcessingContext()
        img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        doc = await parser.parse(img_bytes, ctx)
        assert len(doc.images) == 1
        assert "Image Document" in doc.full_text

    asyncio.run(_test())
