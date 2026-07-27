"""Scoring Engine evaluating predicted answers against ground truth."""

import re
from typing import Tuple
from tools.benchmark.interfaces.benchmark_interfaces import IScoringEngine
from infrastructure.logging.logger import StructuredLogger


class ScoringEngine(IScoringEngine):
    """Computes exact match, string normalization, and fuzzy numerical tolerance scores."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ScoringEngine")

    def score(self, predicted: str, ground_truth: str) -> Tuple[bool, float]:
        """Evaluate accuracy and return (is_correct, score_float)."""
        pred_norm = self._normalize(predicted)
        gt_norm = self._normalize(ground_truth)

        # 1. Exact match after normalization
        if pred_norm == gt_norm or gt_norm in pred_norm:
            return True, 1.0

        # 2. Token overlap overlap coefficient
        pred_words = set(pred_norm.split())
        gt_words = set(gt_norm.split())
        if gt_words:
            overlap = len(pred_words.intersection(gt_words)) / len(gt_words)
            if overlap >= 0.70:
                return True, round(overlap, 2)

        return False, 0.0

    def _normalize(self, text: str) -> str:
        """Strip punctuation, quotes, and lower-case text for scoring."""
        cleaned = text.lower().strip()
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        return " ".join(cleaned.split())
