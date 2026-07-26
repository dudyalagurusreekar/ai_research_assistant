"""Parsers Package for the Browser Tool Subsystem.

This package provides concrete implementations of `BaseParser`, `HTMLCleaner`,
modular extractors, and `ParserFactory` strategy factory.
"""

from tools.browser.core.base_parser import BaseParser
from tools.browser.parsers.cleaner import HTMLCleaner
from tools.browser.parsers.extractors import (
    MetadataExtractor,
    TextExtractor,
    LinkExtractor,
    ImageExtractor,
    TableExtractor,
    FormExtractor,
    StructuredDataExtractor,
)
from tools.browser.parsers.bs4_parser import BS4Parser
from tools.browser.parsers.factory import ParserFactory

__all__ = [
    "BaseParser",
    "HTMLCleaner",
    "MetadataExtractor",
    "TextExtractor",
    "LinkExtractor",
    "ImageExtractor",
    "TableExtractor",
    "FormExtractor",
    "StructuredDataExtractor",
    "BS4Parser",
    "ParserFactory",
]
