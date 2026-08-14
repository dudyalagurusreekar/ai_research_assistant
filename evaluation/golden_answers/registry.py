"""Golden Answers Reference Registry."""

from __future__ import annotations

from typing import Any, Dict, Optional

from evaluation.models.task import GoldenAnswer
from utils.logger import get_logger

logger = get_logger("GoldenAnswerRegistry")


class GoldenAnswerRegistry:
    """Registry maintaining reference ground truth standards and assertion evaluators."""

    def __init__(self) -> None:
        self._registry: Dict[str, GoldenAnswer] = {}

    def register(self, task_id: str, golden_answer: GoldenAnswer) -> None:
        """Register golden reference answer for a task ID."""
        self._registry[task_id] = golden_answer

    def get(self, task_id: str) -> Optional[GoldenAnswer]:
        """Get golden reference answer for a task ID."""
        return self._registry.get(task_id)

    def validate_output(self, golden_answer: GoldenAnswer, actual_output: Any, latency_ms: float = 0.0) -> tuple[bool, float, str]:
        """Validate actual output against golden answer criteria.

        Returns: (passed, score [0.0..1.0], justification)
        """
        out_str = str(actual_output).lower() if actual_output is not None else ""

        # Check forbidden keywords (security / hallucination)
        for fk in golden_answer.forbidden_keywords:
            if fk.lower() in out_str:
                return False, 0.0, f"Forbidden keyword detected: '{fk}'"

        # Check expected keywords
        missing_kw = []
        for ek in golden_answer.expected_keywords:
            if ek.lower() not in out_str:
                missing_kw.append(ek)

        if missing_kw and golden_answer.expected_keywords:
            match_pct = (len(golden_answer.expected_keywords) - len(missing_kw)) / len(golden_answer.expected_keywords)
            if match_pct < 0.5:
                return False, round(match_pct, 2), f"Missing required keywords: {missing_kw}"

        # Check max allowed latency
        if golden_answer.max_allowed_latency_ms > 0 and latency_ms > golden_answer.max_allowed_latency_ms:
            return False, 0.6, f"Latency ({latency_ms:.1f}ms) exceeded threshold ({golden_answer.max_allowed_latency_ms}ms)"

        return True, 1.0, "Output matched golden answer criteria."
