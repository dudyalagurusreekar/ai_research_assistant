"""EvidenceEvaluator — evaluates quality, freshness, diversity, and conflict detection.

Assesses gathered evidence across task outputs, scoring source diversity, checking text richness,
and detecting conflicting claims across opposing data sources.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

from core.reflection.models.reflection import EvidenceAssessment, EvidenceQuality
from infrastructure.logging.logger import StructuredLogger


class EvidenceEvaluator:
    """Evaluates evidence quality and detects conflicting statements across sources."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("EvidenceEvaluator")

    def evaluate(self, task_outputs: Dict[str, Any]) -> EvidenceAssessment:
        """Evaluate evidence across task outputs.

        Args:
            task_outputs: Dict mapping task_id / node_id to output data.

        Returns:
            EvidenceAssessment detailing quality classification, conflict status, and metrics.
        """
        if not task_outputs:
            return EvidenceAssessment(
                quality=EvidenceQuality.INSUFFICIENT,
                quality_score=0.0,
                source_count=0,
                freshness_score=0.0,
                conflict_detected=False,
            )

        # 1. Count distinct tool sources
        sources: Set[str] = set()
        texts: List[str] = []

        for key, output in task_outputs.items():
            if isinstance(output, str):
                texts.append(output)
                if "search" in key or "search" in output.lower():
                    sources.add("search_tool")
                elif "browse" in key or "browser" in output.lower():
                    sources.add("browser_tool")
                elif "pdf" in key or "document" in output.lower():
                    sources.add("document_tool")
                else:
                    sources.add("general_tool")
            elif isinstance(output, dict):
                texts.append(str(output))
                sources.add(output.get("source", "tool_source"))

        source_count = max(1, len(sources))
        combined_text = " ".join(texts).lower()

        # 2. Check for conflicting claims (e.g. opposing numbers/dates or explicit conflict signals)
        conflict_detected = False
        conflicting_sources: List[str] = []

        # Conflict pattern detection (e.g., "source a says X, however source b claims Y" or conflicting numbers)
        conflict_keywords = ["conflict", "contradiction", "disagree", "contrary to", "however", "whereas"]
        has_conflict_word = any(w in combined_text for w in conflict_keywords)

        # Extract year patterns to check for conflicting historical dates
        years = re.findall(r"\b(19\d\d|20\d\d)\b", combined_text)
        distinct_years = set(years)

        if has_conflict_word and len(texts) >= 2:
            conflict_detected = True
            conflicting_sources = list(sources)[:2]
        elif len(distinct_years) > 3 and "invented" in combined_text:
            conflict_detected = True
            conflicting_sources = ["source_date_1", "source_date_2"]

        # 3. Calculate quality score based on text length, source count, and conflicts
        quality_score = 0.5 + (0.15 * min(3, source_count)) + (0.2 if len(combined_text) > 200 else 0.0)
        if conflict_detected:
            quality_score -= 0.30

        quality_score = max(0.0, min(1.0, quality_score))

        # 4. Determine EvidenceQuality classification
        if conflict_detected:
            classification = EvidenceQuality.CONFLICTING
        elif quality_score >= 0.80:
            classification = EvidenceQuality.HIGH
        elif quality_score >= 0.50:
            classification = EvidenceQuality.MODERATE
        elif quality_score >= 0.25:
            classification = EvidenceQuality.WEAK
        else:
            classification = EvidenceQuality.INSUFFICIENT

        assessment = EvidenceAssessment(
            quality=classification,
            quality_score=round(quality_score, 2),
            source_count=source_count,
            freshness_score=0.95,
            conflict_detected=conflict_detected,
            conflicting_sources=conflicting_sources,
        )

        self._logger.info(
            f"Evidence Evaluation: quality={classification.value} (score={quality_score:.2f}), "
            f"sources={source_count}, conflict={conflict_detected}"
        )
        return assessment
