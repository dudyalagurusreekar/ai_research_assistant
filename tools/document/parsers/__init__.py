"""Parsers package exporting concrete document parsers."""

from tools.document.parsers.base import BaseDocumentParser
from tools.document.parsers.pdf_parser import PDFParser
from tools.document.parsers.docx_parser import DOCXParser
from tools.document.parsers.pptx_parser import PPTXParser
from tools.document.parsers.xlsx_parser import XLSXParser
from tools.document.parsers.csv_parser import CSVParser
from tools.document.parsers.txt_parser import TXTParser
from tools.document.parsers.markdown_parser import MarkdownParser
from tools.document.parsers.html_parser import HTMLParser
from tools.document.parsers.xml_parser import XMLParser
from tools.document.parsers.image_parser import ImageOCRParser
from tools.document.parsers.zip_parser import ZIPParser

__all__ = [
    "BaseDocumentParser",
    "PDFParser",
    "DOCXParser",
    "PPTXParser",
    "XLSXParser",
    "CSVParser",
    "TXTParser",
    "MarkdownParser",
    "HTMLParser",
    "XMLParser",
    "ImageOCRParser",
    "ZIPParser",
]
