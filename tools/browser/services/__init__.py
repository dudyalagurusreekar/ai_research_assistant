"""Browser Subsystem Services Package.

Provides high-level services including ContentRouter, LanguageDetector, and CrawlerEngine.
"""

from tools.browser.services.content_router import ContentRouter, JSONParser, TextParser, PDFParser
from tools.browser.services.language import LanguageDetector
from tools.browser.services.crawler import CrawlerEngine

__all__ = [
    "ContentRouter",
    "JSONParser",
    "TextParser",
    "PDFParser",
    "LanguageDetector",
    "CrawlerEngine",
]
