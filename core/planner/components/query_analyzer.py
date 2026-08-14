"""QueryAnalyzer — extracts structured semantics from raw user queries.

Uses deterministic NLP heuristics (regex, keyword detection, entity extraction)
to produce a QueryAnalysis without requiring an LLM call, ensuring sub-millisecond
latency and full reliability under rate-limited conditions.
"""

from __future__ import annotations

import re
from typing import List

from core.planner.interfaces.base import IQueryAnalyzer
from core.planner.models.context import PlannerContext, QueryAnalysis
from infrastructure.logging.logger import StructuredLogger


# ---------------------------------------------------------------------------
# Keyword sets
# ---------------------------------------------------------------------------

_FILE_PATTERNS = re.compile(
    r"\b(?:file|pdf|document|upload|read|load|\.pdf|\.docx?|\.txt|\.md|\.csv)\b",
    re.IGNORECASE,
)
_URL_PATTERNS = re.compile(
    r"https?://[^\s]+|www\.[^\s]+|\burl\b|\bwebsite\b|\bwebpage\b|\blink\b",
    re.IGNORECASE,
)
_CODE_PATTERNS = re.compile(
    r"\b(?:code|execute|run|python|script|fibonacci|snippet|function|debug|compile|program)\b",
    re.IGNORECASE,
)
_COMPARISON_PATTERNS = re.compile(
    r"\b(?:compare|versus|vs\.?|difference|better|worse|pros\s+and\s+cons|contrast)\b",
    re.IGNORECASE,
)
_VISION_PATTERNS = re.compile(
    r"\b(?:image|photo|picture|screenshot|chart|graph|diagram|ocr|vision|analyze.*image)\b",
    re.IGNORECASE,
)
_MEMORY_PATTERNS = re.compile(
    r"\b(?:remember|store|recall|memory|memorize|forget|saved)\b",
    re.IGNORECASE,
)
_REPORT_PATTERNS = re.compile(
    r"\b(?:report|summarize|summary|validate|generate\s+report)\b",
    re.IGNORECASE,
)

_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "and", "but", "or", "nor", "not",
    "so", "yet", "both", "either", "neither", "each", "every", "all",
    "any", "few", "more", "most", "other", "some", "such", "no", "only",
    "same", "than", "too", "very", "just", "about", "it", "its", "this",
    "that", "these", "those", "i", "me", "my", "we", "our", "you", "your",
    "he", "him", "his", "she", "her", "they", "them", "their", "what",
    "which", "who", "whom", "how", "when", "where", "why",
})


class QueryAnalyzer(IQueryAnalyzer):
    """Deterministic query understanding using pattern matching and keyword extraction."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("QueryAnalyzer")

    @property
    def component_name(self) -> str:
        return "QueryAnalyzer"

    def analyze(self, ctx: PlannerContext) -> QueryAnalysis:
        """Parse the raw query and produce a structured QueryAnalysis."""
        raw = ctx.user_query.strip()
        normalized = raw.lower()

        analysis = QueryAnalysis(
            raw_query=raw,
            normalized_query=normalized,
            entities=self._extract_entities(raw),
            keywords=self._extract_keywords(normalized),
            research_requirements=self._infer_requirements(normalized),
            ambiguity_score=self._compute_ambiguity(normalized),
            has_file_reference=bool(_FILE_PATTERNS.search(normalized)),
            has_url_reference=bool(_URL_PATTERNS.search(normalized)),
            has_code_request=bool(_CODE_PATTERNS.search(normalized)),
            has_comparison=bool(_COMPARISON_PATTERNS.search(normalized)),
            source_count_hint=self._estimate_source_count(normalized),
        )

        ctx.query_analysis = analysis
        ctx.add_trace(
            stage="query_analysis",
            message=f"Analyzed query: {len(analysis.keywords)} keywords, "
                    f"ambiguity={analysis.ambiguity_score:.2f}",
            data={
                "keywords": analysis.keywords[:10],
                "entities": analysis.entities[:10],
                "has_file": analysis.has_file_reference,
                "has_url": analysis.has_url_reference,
                "has_code": analysis.has_code_request,
                "has_comparison": analysis.has_comparison,
            },
        )
        self._logger.info(
            f"Query analyzed: keywords={len(analysis.keywords)}, "
            f"entities={len(analysis.entities)}, ambiguity={analysis.ambiguity_score:.2f}"
        )
        return analysis

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_entities(raw: str) -> List[str]:
        """Extract capitalized multi-word entities (simple NER heuristic)."""
        # Match sequences of capitalized words (2+ chars each)
        entity_pattern = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b")
        candidates = entity_pattern.findall(raw)
        # Filter out sentence starters by checking position
        entities: List[str] = []
        for ent in candidates:
            if len(ent) > 2 and ent.lower() not in _STOP_WORDS:
                entities.append(ent)
        return list(dict.fromkeys(entities))  # deduplicate preserving order

    @staticmethod
    def _extract_keywords(normalized: str) -> List[str]:
        """Extract meaningful keywords by stripping stop words and short tokens."""
        tokens = re.findall(r"[a-z0-9]+", normalized)
        return [t for t in tokens if t not in _STOP_WORDS and len(t) > 2]

    @staticmethod
    def _infer_requirements(normalized: str) -> List[str]:
        """Infer high-level research requirements from query text."""
        reqs: List[str] = []
        if any(w in normalized for w in ("search", "find", "look up", "research", "latest")):
            reqs.append("web_search")
        if _FILE_PATTERNS.search(normalized):
            reqs.append("document_processing")
        if _CODE_PATTERNS.search(normalized):
            reqs.append("code_execution")
        if _COMPARISON_PATTERNS.search(normalized):
            reqs.append("comparison_analysis")
        if _VISION_PATTERNS.search(normalized):
            reqs.append("vision_analysis")
        if _MEMORY_PATTERNS.search(normalized):
            reqs.append("memory_operation")
        if _REPORT_PATTERNS.search(normalized):
            reqs.append("report_generation")
        if _URL_PATTERNS.search(normalized):
            reqs.append("web_browsing")
        if not reqs:
            reqs.append("general_qa")
        return reqs

    @staticmethod
    def _compute_ambiguity(normalized: str) -> float:
        """Heuristic ambiguity score in [0.0, 1.0]."""
        score = 0.0
        word_count = len(normalized.split())
        # Very short queries are more ambiguous
        if word_count <= 3:
            score += 0.3
        # Question words reduce ambiguity (clearer intent)
        if re.search(r"\b(who|what|when|where|why|how|which)\b", normalized):
            score -= 0.1
        # Multiple question marks or vague phrasing increase ambiguity
        if normalized.count("?") > 1:
            score += 0.15
        if any(w in normalized for w in ("maybe", "perhaps", "something", "anything")):
            score += 0.2
        return max(0.0, min(1.0, score))

    @staticmethod
    def _estimate_source_count(normalized: str) -> int:
        """Estimate how many sources the query might require."""
        if _COMPARISON_PATTERNS.search(normalized):
            # Count comparison targets
            nums = re.findall(r"\b(two|three|four|five|\d+)\b", normalized)
            if nums:
                mapping = {"two": 2, "three": 3, "four": 4, "five": 5}
                return max(mapping.get(nums[0], int(nums[0]) if nums[0].isdigit() else 2), 2)
            return 2
        if any(w in normalized for w in ("multiple", "several", "various")):
            return 3
        return 1
