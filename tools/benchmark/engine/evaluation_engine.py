"""Evaluation Engine constructing NormalizedBenchmarkResult containers."""

from typing import Optional
from tools.benchmark.interfaces.benchmark_interfaces import (
    IEvaluationEngine,
    ILocalScoringEngine,
    IFailureAnalyzer,
    IAnswerFormatter,
)
from tools.benchmark.models.benchmark_models import (
    GAIATask,
    NormalizedBenchmarkResult,
    ExecutionTrace,
    ErrorCategory,
    FailureReport,
)
from tools.benchmark.scoring.scoring_engine import LocalScoringEngine
from tools.benchmark.analysis.error_analyzer import FailureAnalyzer
from tools.benchmark.formatter.answer_formatter import AnswerFormatter
from infrastructure.logging.logger import StructuredLogger


class EvaluationEngine(IEvaluationEngine):
    """Evaluates task outputs, scores accuracy, formats answers, classifies errors, and constructs NormalizedBenchmarkResult."""

    def __init__(
        self,
        scoring_engine: Optional[ILocalScoringEngine] = None,
        error_analyzer: Optional[IFailureAnalyzer] = None,
        answer_formatter: Optional[IAnswerFormatter] = None,
    ) -> None:
        self._logger = StructuredLogger("EvaluationEngine")
        self._answer_formatter = answer_formatter or AnswerFormatter()
        self._scoring_engine = scoring_engine or LocalScoringEngine(formatter=self._answer_formatter)
        self._error_analyzer = error_analyzer or FailureAnalyzer()

    async def evaluate_task(
        self, task: GAIATask, predicted_answer: str, trace: ExecutionTrace
    ) -> NormalizedBenchmarkResult:
        """Evaluate task output against ground truth."""
        # 1. Format raw prediction to GAIA standard
        formatted_pred = self._answer_formatter.format_answer(predicted_answer)

        # 2. Score formatted prediction against ground truth
        score_res = self._scoring_engine.score_detailed(formatted_pred, task.ground_truth)
        is_correct = score_res.is_correct
        score_val = score_res.score

        # 3. Analyze failure if incorrect
        failure_rep: Optional[FailureReport] = None
        err_cat = ErrorCategory.NONE

        if not is_correct:
            failure_rep = self._error_analyzer.generate_failure_report(
                task=task, predicted=formatted_pred, trace=trace
            )
            err_cat = failure_rep.error_category

        result = NormalizedBenchmarkResult(
            task_id=task.task_id,
            is_correct=is_correct,
            score=score_val,
            predicted_answer=formatted_pred,
            ground_truth=task.ground_truth,
            error_category=err_cat,
            trace=trace,
            failure_report=failure_rep,
        )

        self._logger.info(f"Evaluated task '{task.task_id}': correct={is_correct}, score={score_val}, error={err_cat.value}")
        return result
