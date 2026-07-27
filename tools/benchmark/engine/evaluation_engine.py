"""Evaluation Engine constructing NormalizedBenchmarkResult containers."""

import asyncio
from typing import Optional
from tools.benchmark.interfaces.benchmark_interfaces import IEvaluationEngine, IScoringEngine, IErrorAnalyzer
from tools.benchmark.models.benchmark_models import GAIATask, NormalizedBenchmarkResult, ExecutionTrace, ErrorCategory
from tools.benchmark.scoring.scoring_engine import ScoringEngine
from tools.benchmark.analysis.error_analyzer import ErrorAnalyzer
from infrastructure.logging.logger import StructuredLogger


class EvaluationEngine(IEvaluationEngine):
    """Evaluates task outputs, scores accuracy, classifies errors, and returns NormalizedBenchmarkResult."""

    def __init__(
        self,
        scoring_engine: Optional[IScoringEngine] = None,
        error_analyzer: Optional[IErrorAnalyzer] = None,
    ) -> None:
        self._logger = StructuredLogger("EvaluationEngine")
        self._scoring_engine = scoring_engine or ScoringEngine()
        self._error_analyzer = error_analyzer or ErrorAnalyzer()

    async def evaluate_task(self, task: GAIATask, predicted_answer: str, trace: ExecutionTrace) -> NormalizedBenchmarkResult:
        """Evaluate task output against ground truth."""
        is_correct, score_val = self._scoring_engine.score(predicted_answer, task.ground_truth)
        err_cat = ErrorCategory.NONE if is_correct else self._error_analyzer.classify_error(predicted_answer, task.ground_truth, trace)

        result = NormalizedBenchmarkResult(
            task_id=task.task_id,
            is_correct=is_correct,
            score=score_val,
            predicted_answer=predicted_answer,
            ground_truth=task.ground_truth,
            error_category=err_cat,
            trace=trace,
        )

        self._logger.info(f"Evaluated GAIA task '{task.task_id}': correct={is_correct}, score={score_val}")
        return result
