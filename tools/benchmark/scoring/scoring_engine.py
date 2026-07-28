"""Local Scoring Engine integrating official GAIA scoring logic, numerical tolerance, and list comparisons."""

import re
import math
from typing import Tuple, Optional
from tools.benchmark.interfaces.benchmark_interfaces import ILocalScoringEngine
from tools.benchmark.models.benchmark_models import ScoringResult
from tools.benchmark.formatter.answer_formatter import AnswerFormatter
from infrastructure.logging.logger import StructuredLogger


class LocalScoringEngine(ILocalScoringEngine):
    """Computes exact string match, normalized string match, numeric tolerance match, and set-based list scoring."""

    def __init__(self, formatter: Optional[AnswerFormatter] = None) -> None:
        self._logger = StructuredLogger("LocalScoringEngine")
        self._formatter = formatter or AnswerFormatter()

    def score(self, predicted: str, ground_truth: str) -> Tuple[bool, float]:
        """Evaluate accuracy and return (is_correct, score_float)."""
        res = self.score_detailed(predicted, ground_truth)
        return res.is_correct, res.score

    def score_detailed(self, predicted: str, ground_truth: str) -> ScoringResult:
        """Evaluate predicted answer against ground truth using GAIA multi-strategy comparison."""
        if not predicted or not ground_truth:
            if not predicted and not ground_truth:
                return ScoringResult(is_correct=True, score=1.0, match_type="empty_match")
            return ScoringResult(is_correct=False, score=0.0, match_type="empty_mismatch")

        # Format answers
        pred_fmt = self._formatter.format_answer(predicted)
        gt_fmt = self._formatter.format_answer(ground_truth)

        # 1. Exact string match
        if pred_fmt == gt_fmt:
            return ScoringResult(is_correct=True, score=1.0, match_type="exact_match")

        # 2. Case-insensitive normalized string match
        pred_clean = self._clean_str(pred_fmt)
        gt_clean = self._clean_str(gt_fmt)
        if pred_clean == gt_clean:
            return ScoringResult(is_correct=True, score=1.0, match_type="normalized_string")

        # 3. Ground truth substring containment (if gt is concise and contained in pred)
        if gt_clean and gt_clean in pred_clean and len(gt_clean) > 3:
            return ScoringResult(is_correct=True, score=1.0, match_type="substring_match")

        # 4. Numeric evaluation (floats / ints / relative tolerance)
        num_score = self._score_numeric(pred_fmt, gt_fmt)
        if num_score is not None:
            return num_score

        # 5. Comma-separated list evaluation
        if "," in pred_fmt or "," in gt_fmt:
            list_score = self._score_list(pred_fmt, gt_fmt)
            if list_score is not None:
                return list_score

        # 6. Token overlap fuzzy matching (fallback for descriptive answers)
        pred_words = set(pred_clean.split())
        gt_words = set(gt_clean.split())
        if gt_words:
            intersection = pred_words.intersection(gt_words)
            overlap = len(intersection) / len(gt_words)
            if overlap >= 0.75:
                return ScoringResult(is_correct=True, score=round(overlap, 2), match_type="token_overlap")

        return ScoringResult(is_correct=False, score=0.0, match_type="no_match")

    def _score_numeric(self, pred: str, gt: str) -> Optional[ScoringResult]:
        """Try numeric parsing and comparison with relative/absolute tolerance."""
        try:
            # Extract numbers from string if string contains single number
            pred_num_str = self._extract_single_number(pred)
            gt_num_str = self._extract_single_number(gt)

            if pred_num_str is not None and gt_num_str is not None:
                p_val = float(pred_num_str)
                g_val = float(gt_num_str)

                # Absolute tolerance 1e-3 or relative tolerance 1e-3
                if math.isclose(p_val, g_val, rel_tol=1e-3, abs_tol=1e-3):
                    return ScoringResult(is_correct=True, score=1.0, match_type="numeric_exact")
        except (ValueError, TypeError):
            pass
        return None

    def _score_list(self, pred: str, gt: str) -> Optional[ScoringResult]:
        """Compare comma-separated lists as sets."""
        try:
            pred_set = {self._clean_str(x) for x in pred.split(",") if x.strip()}
            gt_set = {self._clean_str(x) for x in gt.split(",") if x.strip()}

            if pred_set and gt_set:
                if pred_set == gt_set:
                    return ScoringResult(is_correct=True, score=1.0, match_type="list_exact_set")
                # Partial list overlap
                overlap = len(pred_set.intersection(gt_set)) / len(gt_set)
                if overlap >= 0.8:
                    return ScoringResult(is_correct=True, score=round(overlap, 2), match_type="list_partial_set")
        except Exception:
            pass
        return None

    def _clean_str(self, text: str) -> str:
        """Strip punctuation and lowercase."""
        cleaned = text.lower().strip()
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        return " ".join(cleaned.split())

    def _extract_single_number(self, text: str) -> Optional[str]:
        """Extract number from string if it represents a single numeric answer."""
        s = text.replace("$", "").replace("%", "").replace(",", "").strip()
        try:
            float(s)
            return s
        except ValueError:
            # Search for isolated float pattern
            matches = re.findall(r"[-+]?\d*\.\d+|\d+", s)
            if len(matches) == 1:
                return matches[0]
        return None


# Alias for backward compatibility
ScoringEngine = LocalScoringEngine
