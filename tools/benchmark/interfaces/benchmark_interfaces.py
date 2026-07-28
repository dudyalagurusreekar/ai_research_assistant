"""Abstract interface contracts for the GAIA Benchmark Framework."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from tools.benchmark.models.benchmark_models import (
    GAIATask,
    NormalizedBenchmarkResult,
    BenchmarkReportModel,
    ExecutionTrace,
    ExecutionStep,
    ErrorCategory,
    TaskLevel,
    BenchmarkSuiteMetadata,
    DatasetIntegrityResult,
    AnswerFormatConfig,
    ScoringResult,
    FailureReport,
    EvaluationMetrics,
    RegressionReport,
    OptimizationRecommendation,
    SubmissionPackage,
)


class IBenchmarkRegistry(ABC):
    """Abstract benchmark registry interface managing benchmark suites."""

    @abstractmethod
    def register_suite(self, metadata: BenchmarkSuiteMetadata) -> None:
        """Register a benchmark suite metadata descriptor."""

    @abstractmethod
    def get_suite(self, suite_id: str) -> Optional[BenchmarkSuiteMetadata]:
        """Get benchmark suite metadata by ID."""

    @abstractmethod
    def list_suites(self) -> List[BenchmarkSuiteMetadata]:
        """List all registered benchmark suites."""


class ITaskLoader(ABC):
    """Abstract task loader interface for dataset loading and integrity validation."""

    @abstractmethod
    def load_tasks(
        self,
        level: Optional[TaskLevel] = None,
        suite_id: str = "gaia",
        dataset_path: Optional[str] = None,
    ) -> List[GAIATask]:
        """Load benchmark tasks filtered by level or dataset path."""

    @abstractmethod
    def validate_dataset(self, tasks: List[GAIATask]) -> DatasetIntegrityResult:
        """Validate dataset structure, schema integrity, and attachments."""


class IExecutionTracer(ABC):
    """Abstract execution tracer interface capturing workflow telemetry."""

    @abstractmethod
    def start_trace(self, task_id: str) -> ExecutionTrace:
        """Initialize a new trace context for a task."""

    @abstractmethod
    def record_step(self, trace_id: str, step: ExecutionStep) -> None:
        """Record an execution step to an active trace."""

    @abstractmethod
    def finalize_trace(self, trace_id: str, final_answer: str) -> ExecutionTrace:
        """Finalize and return completed execution trace."""


class IAnswerFormatter(ABC):
    """Abstract answer formatter interface for benchmark normalization rules."""

    @abstractmethod
    def format_answer(self, raw_answer: str, config: Optional[AnswerFormatConfig] = None) -> str:
        """Format and normalize answer per GAIA formatting rules."""

    @abstractmethod
    def validate_format(self, formatted_answer: str, config: Optional[AnswerFormatConfig] = None) -> bool:
        """Validate whether answer complies with benchmark format rules."""


class ILocalScoringEngine(ABC):
    """Abstract scoring engine interface evaluating answer accuracy."""

    @abstractmethod
    def score(self, predicted: str, ground_truth: str) -> Tuple[bool, float]:
        """Evaluate accuracy and return (is_correct, score_float)."""

    @abstractmethod
    def score_detailed(self, predicted: str, ground_truth: str) -> ScoringResult:
        """Evaluate accuracy with detailed scoring metadata."""


class IFailureAnalyzer(ABC):
    """Abstract failure analyzer interface classifying failure taxonomy."""

    @abstractmethod
    def classify_error(
        self, predicted: str, ground_truth: str, trace: Optional[ExecutionTrace] = None
    ) -> ErrorCategory:
        """Classify failure mode into ErrorCategory taxonomy."""

    @abstractmethod
    def generate_failure_report(
        self, task: GAIATask, predicted: str, trace: Optional[ExecutionTrace] = None
    ) -> FailureReport:
        """Generate detailed failure report with root cause analysis."""


class IMetricsEngine(ABC):
    """Abstract metrics engine tracking evaluation metrics and telemetry."""

    @abstractmethod
    def compute_metrics(
        self, results: List[NormalizedBenchmarkResult], start_time_ms: float, end_time_ms: float
    ) -> EvaluationMetrics:
        """Compute comprehensive aggregated evaluation metrics."""


class IRegressionEngine(ABC):
    """Abstract regression engine comparing benchmark runs."""

    @abstractmethod
    def compare_runs(
        self, baseline_report: BenchmarkReportModel, target_report: BenchmarkReportModel
    ) -> RegressionReport:
        """Compare two benchmark runs to detect improvements and regressions."""


class IOptimizationAdvisor(ABC):
    """Abstract optimization advisor interface generating actionable recommendations."""

    @abstractmethod
    def analyze_and_recommend(
        self, report: BenchmarkReportModel
    ) -> List[OptimizationRecommendation]:
        """Analyze evaluation results and recommend system optimizations."""

    @abstractmethod
    def get_optimized_params(self, task: GAIATask) -> Dict[str, Any]:
        """Get optimization settings for task execution."""


class ISubmissionGenerator(ABC):
    """Abstract submission generator producing benchmark export artifacts."""

    @abstractmethod
    def generate_submission(
        self, results: List[NormalizedBenchmarkResult], output_file: str
    ) -> SubmissionPackage:
        """Generate official GAIA jsonl submission file."""


class IBenchmarkReportGenerator(ABC):
    """Abstract report generator producing formatted reports."""

    @abstractmethod
    def generate_report(self, report_model: BenchmarkReportModel) -> str:
        """Generate formatted report text/markdown."""


class IEvaluationEngine(ABC):
    """Abstract evaluation engine interface recording traces and metrics."""

    @abstractmethod
    async def evaluate_task(
        self, task: GAIATask, predicted_answer: str, trace: ExecutionTrace
    ) -> NormalizedBenchmarkResult:
        """Evaluate task answer, score, analyze errors, and construct result."""


class IBenchmarkRunner(ABC):
    """Abstract benchmark runner interface executing tasks against platform."""

    @abstractmethod
    async def run_benchmark(
        self,
        level: Optional[TaskLevel] = None,
        suite_id: str = "gaia",
        dataset_path: Optional[str] = None,
        max_tasks: Optional[int] = None,
        concurrency: int = 1,
        checkpoint_file: Optional[str] = None,
    ) -> BenchmarkReportModel:
        """Execute benchmark suite and generate evaluation report."""
