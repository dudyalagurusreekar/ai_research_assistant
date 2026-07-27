"""Abstract interface contracts for the GAIA Benchmark Framework."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tools.benchmark.models.benchmark_models import (
    GAIATask,
    NormalizedBenchmarkResult,
    BenchmarkReportModel,
    ExecutionTrace,
    ErrorCategory,
    TaskLevel,
)


class ITaskLoader(ABC):
    """Abstract GAIA task loader interface."""

    @abstractmethod
    def load_tasks(self, level: Optional[TaskLevel] = None) -> List[GAIATask]:
        """Load benchmark tasks filtered by difficulty level."""
        pass


class IScoringEngine(ABC):
    """Abstract scoring engine interface evaluating answer accuracy."""

    @abstractmethod
    def score(self, predicted: str, ground_truth: str) -> tuple[bool, float]:
        """Evaluate accuracy and return (is_correct, score_float)."""
        pass


class IErrorAnalyzer(ABC):
    """Abstract error analyzer interface classifying failure taxonomy."""

    @abstractmethod
    def classify_error(self, predicted: str, ground_truth: str, trace: Optional[ExecutionTrace] = None) -> ErrorCategory:
        """Classify failure mode into ErrorCategory taxonomy."""
        pass


class IOptimizationManager(ABC):
    """Abstract optimization manager interface applying execution policies."""

    @abstractmethod
    def get_optimized_params(self, task: GAIATask) -> Dict[str, Any]:
        """Get optimization settings for task execution."""
        pass


class IEvaluationEngine(ABC):
    """Abstract evaluation engine interface recording traces and metrics."""

    @abstractmethod
    async def evaluate_task(self, task: GAIATask, predicted_answer: str, trace: ExecutionTrace) -> NormalizedBenchmarkResult:
        """Evaluate task answer, score, analyze errors, and construct result."""
        pass


class IBenchmarkRunner(ABC):
    """Abstract benchmark runner interface executing tasks against platform."""

    @abstractmethod
    async def run_benchmark(self, level: Optional[TaskLevel] = None) -> BenchmarkReportModel:
        """Execute benchmark suite and generate evaluation report."""
        pass
