"""Language Detection Service for the Browser Tool Subsystem.

This module provides the `LanguageDetector` class, responsible for identifying
the document primary language without forcing translation.
"""

import re
from typing import Optional
from tools.browser.models.response import PageMetadata


COMMON_WORD_PATTERNS = {
    "en": r"\b(the|and|is|in|it|you|that|was|for|on|are|with|as|at|be|this|have|from)\b",
    "es": r"\b(el|la|los|las|un|una|que|del|en|por|con|para|como|esta|este|son|mas)\b",
    "fr": r"\b(le|la|les|un|une|des|que|est|dans|pour|sur|avec|sont|plus|par|qui)\b",
    "de": r"\b(der|die|das|und|in|den|von|zu|das|mit|sich|des|auf|fur|ist|im|dem)\b",
}


class LanguageDetector:
    """Language Detector identifying primary document language for multilingual AI agents."""

    def detect(self, metadata: PageMetadata, main_text: str = "") -> str:
        """Detect document language ISO code.

        Args:
            metadata (PageMetadata): Document metadata container.
            main_text (str): Main text snippet for heuristic fallback.

        Returns:
            str: Detected 2-character ISO language code (e.g. 'en', 'es', 'fr', 'de').
        """
        # 1. Existing metadata language attribute
        if metadata.language:
            lang = metadata.language.strip().lower()
            if "-" in lang:
                lang = lang.split("-")[0]
            if len(lang) == 2:
                return lang

        # 2. Open Graph Locale
        if "og:locale" in metadata.open_graph:
            locale = metadata.open_graph["og:locale"].strip().lower()
            lang = locale.split("_")[0]
            if len(lang) == 2:
                return lang

        # 3. Text Heuristic Fallback
        if main_text:
            snippet = main_text[:2000].lower()
            scores = {}
            for lang, pattern in COMMON_WORD_PATTERNS.items():
                matches = len(re.findall(pattern, snippet, re.IGNORECASE))
                scores[lang] = matches

            best_lang = max(scores, key=scores.get)
            if scores[best_lang] > 3:
                return best_lang

        return "en"  # Default fallback
