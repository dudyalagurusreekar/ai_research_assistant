"""IntentClassifier — classifies queries into standard intent categories.

Uses a weighted keyword-scoring system with domain-specific boosters to determine
the most likely QueryIntent without requiring an LLM call.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from core.planner.interfaces.base import IIntentClassifier
from core.planner.models.context import PlannerContext, QueryIntent
from infrastructure.logging.logger import StructuredLogger


# ---------------------------------------------------------------------------
# Intent scoring rules: keyword -> (intent, weight)
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: Dict[str, List[Tuple[QueryIntent, float]]] = {
    # Factual QA
    "who": [(QueryIntent.FACTUAL_QA, 0.6)],
    "what": [(QueryIntent.FACTUAL_QA, 0.5)],
    "when": [(QueryIntent.FACTUAL_QA, 0.6)],
    "where": [(QueryIntent.FACTUAL_QA, 0.5)],
    "explain": [(QueryIntent.FACTUAL_QA, 0.5)],
    "define": [(QueryIntent.FACTUAL_QA, 0.6)],
    "describe": [(QueryIntent.FACTUAL_QA, 0.4)],
    "won": [(QueryIntent.FACTUAL_QA, 0.4)],
    "invented": [(QueryIntent.FACTUAL_QA, 0.5)],
    "discovery": [(QueryIntent.FACTUAL_QA, 0.4)],
    "nobel": [(QueryIntent.FACTUAL_QA, 0.5)],
    "prize": [(QueryIntent.FACTUAL_QA, 0.4)],
    # Comparison
    "compare": [(QueryIntent.COMPARISON, 0.9)],
    "versus": [(QueryIntent.COMPARISON, 0.9)],
    "difference": [(QueryIntent.COMPARISON, 0.7)],
    "better": [(QueryIntent.COMPARISON, 0.5)],
    "worse": [(QueryIntent.COMPARISON, 0.5)],
    "pros": [(QueryIntent.COMPARISON, 0.6)],
    "cons": [(QueryIntent.COMPARISON, 0.6)],
    "contrast": [(QueryIntent.COMPARISON, 0.8)],
    # Document analysis
    "pdf": [(QueryIntent.DOCUMENT_ANALYSIS, 0.8)],
    "document": [(QueryIntent.DOCUMENT_ANALYSIS, 0.7)],
    "file": [(QueryIntent.DOCUMENT_ANALYSIS, 0.6)],
    "upload": [(QueryIntent.DOCUMENT_ANALYSIS, 0.7)],
    "read": [(QueryIntent.DOCUMENT_ANALYSIS, 0.4)],
    "summarize": [(QueryIntent.DOCUMENT_ANALYSIS, 0.5), (QueryIntent.REPORT_GENERATION, 0.4)],
    "summary": [(QueryIntent.DOCUMENT_ANALYSIS, 0.5), (QueryIntent.REPORT_GENERATION, 0.4)],
    # Code execution
    "code": [(QueryIntent.CODE_EXECUTION, 0.7)],
    "execute": [(QueryIntent.CODE_EXECUTION, 0.7)],
    "run": [(QueryIntent.CODE_EXECUTION, 0.5)],
    "python": [(QueryIntent.CODE_EXECUTION, 0.7)],
    "script": [(QueryIntent.CODE_EXECUTION, 0.7)],
    "fibonacci": [(QueryIntent.CODE_EXECUTION, 0.8)],
    "snippet": [(QueryIntent.CODE_EXECUTION, 0.6)],
    "function": [(QueryIntent.CODE_EXECUTION, 0.5)],
    "debug": [(QueryIntent.CODE_EXECUTION, 0.6)],
    "program": [(QueryIntent.CODE_EXECUTION, 0.5)],
    # Vision
    "image": [(QueryIntent.VISION_ANALYSIS, 0.8)],
    "photo": [(QueryIntent.VISION_ANALYSIS, 0.8)],
    "screenshot": [(QueryIntent.VISION_ANALYSIS, 0.8)],
    "chart": [(QueryIntent.VISION_ANALYSIS, 0.7)],
    "diagram": [(QueryIntent.VISION_ANALYSIS, 0.7)],
    "ocr": [(QueryIntent.VISION_ANALYSIS, 0.9)],
    "picture": [(QueryIntent.VISION_ANALYSIS, 0.7)],
    # Memory
    "remember": [(QueryIntent.MEMORY_OPERATION, 0.8)],
    "store": [(QueryIntent.MEMORY_OPERATION, 0.7)],
    "recall": [(QueryIntent.MEMORY_OPERATION, 0.8)],
    "memory": [(QueryIntent.MEMORY_OPERATION, 0.7)],
    "memory_tool": [(QueryIntent.MEMORY_OPERATION, 0.95)],
    # Report
    "report": [(QueryIntent.REPORT_GENERATION, 0.7)],
    "validate": [(QueryIntent.REPORT_GENERATION, 0.5)],
    "report_tool": [(QueryIntent.REPORT_GENERATION, 0.9)],
    "document_tool": [(QueryIntent.DOCUMENT_ANALYSIS, 0.9)],
    "code_tool": [(QueryIntent.CODE_EXECUTION, 0.9)],
    # Multi-step research
    "research": [(QueryIntent.MULTI_STEP_RESEARCH, 0.6)],
    "investigate": [(QueryIntent.MULTI_STEP_RESEARCH, 0.7)],
    "latest": [(QueryIntent.MULTI_STEP_RESEARCH, 0.4)],
    "advancements": [(QueryIntent.MULTI_STEP_RESEARCH, 0.5)],
    "comprehensive": [(QueryIntent.MULTI_STEP_RESEARCH, 0.5)],
    "multiple": [(QueryIntent.MULTI_STEP_RESEARCH, 0.4)],
    "several": [(QueryIntent.MULTI_STEP_RESEARCH, 0.4)],
    "search": [(QueryIntent.MULTI_STEP_RESEARCH, 0.3)],
}


class IntentClassifier(IIntentClassifier):
    """Deterministic weighted-keyword intent classifier."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("IntentClassifier")

    @property
    def component_name(self) -> str:
        return "IntentClassifier"

    def classify(self, ctx: PlannerContext) -> Tuple[QueryIntent, float]:
        """Score each intent using keyword weights and contextual signals."""
        if not ctx.query_analysis:
            return QueryIntent.AMBIGUOUS, 0.0

        scores: Dict[QueryIntent, float] = {intent: 0.0 for intent in QueryIntent}
        keywords = ctx.query_analysis.keywords
        normalized = ctx.query_analysis.normalized_query

        # 1. Keyword scoring
        for token in normalized.split():
            clean = token.strip(".,?!;:'\"()[]{}").lower()
            if clean in _INTENT_KEYWORDS:
                for intent, weight in _INTENT_KEYWORDS[clean]:
                    scores[intent] += weight

        # 2. Contextual signal boosters from QueryAnalysis flags
        if ctx.query_analysis.has_file_reference:
            scores[QueryIntent.DOCUMENT_ANALYSIS] += 0.5
        if ctx.query_analysis.has_url_reference:
            scores[QueryIntent.MULTI_STEP_RESEARCH] += 0.3
        if ctx.query_analysis.has_code_request:
            scores[QueryIntent.CODE_EXECUTION] += 0.5
        if ctx.query_analysis.has_comparison:
            scores[QueryIntent.COMPARISON] += 0.5
        if ctx.query_analysis.source_count_hint >= 3:
            scores[QueryIntent.MULTI_STEP_RESEARCH] += 0.3

        # 3. Select top intent
        best_intent = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_score = scores[best_intent]

        # Normalize confidence to [0, 1]
        total = sum(scores.values())
        confidence = (best_score / total) if total > 0 else 0.0
        confidence = max(0.0, min(1.0, confidence))

        # If confidence is very low, classify as AMBIGUOUS
        if confidence < 0.15 or best_score < 0.3:
            best_intent = QueryIntent.AMBIGUOUS
            confidence = max(confidence, 0.1)

        ctx.intent = best_intent
        ctx.intent_confidence = confidence
        ctx.add_trace(
            stage="intent_classification",
            message=f"Classified intent: {best_intent.value} (confidence={confidence:.2f})",
            data={"scores": {k.value: round(v, 3) for k, v in scores.items() if v > 0}},
        )
        self._logger.info(
            f"Intent classified: {best_intent.value}, confidence={confidence:.2f}"
        )
        return best_intent, confidence
