"""GAIA Evaluation & Optimization Framework for AI Research Assistant Platform."""

from tools.benchmark.facade.facade import BenchmarkToolFacade
from tools.benchmark.tool import BenchmarkTool
from tools.benchmark.models.benchmark_models import (
    GAIATask,
    TaskLevel,
    TaskCategory,
    ErrorCategory,
    ExecutionTrace,
    ExecutionStep,
    EvaluationMetrics,
    BenchmarkReportModel,
    NormalizedBenchmarkResult,
    BenchmarkSuiteMetadata,
    DatasetIntegrityResult,
    AnswerFormatConfig,
    ScoringResult,
    FailureReport,
    RegressionReport,
    OptimizationRecommendation,
    SubmissionEntry,
    SubmissionPackage,
)
from tools.benchmark.registry.benchmark_registry import BenchmarkRegistry
from tools.benchmark.loader.task_loader import TaskLoader
from tools.benchmark.tracer.execution_tracer import ExecutionTracer
from tools.benchmark.formatter.answer_formatter import AnswerFormatter
from tools.benchmark.scoring.scoring_engine import LocalScoringEngine, ScoringEngine
from tools.benchmark.analysis.error_analyzer import FailureAnalyzer, ErrorAnalyzer
from tools.benchmark.metrics.metrics_engine import MetricsEngine
from tools.benchmark.regression.regression_engine import RegressionEngine
from tools.benchmark.optimization.optimization_manager import OptimizationAdvisor, OptimizationManager
from tools.benchmark.submission.submission_generator import SubmissionGenerator
from tools.benchmark.report.report_generator import BenchmarkReportGenerator
from tools.benchmark.engine.evaluation_engine import EvaluationEngine
from tools.benchmark.runner.benchmark_runner import BenchmarkRunner

__all__ = [
    "BenchmarkToolFacade",
    "BenchmarkTool",
    "BenchmarkRegistry",
    "TaskLoader",
    "ExecutionTracer",
    "AnswerFormatter",
    "LocalScoringEngine",
    "ScoringEngine",
    "FailureAnalyzer",
    "ErrorAnalyzer",
    "MetricsEngine",
    "RegressionEngine",
    "OptimizationAdvisor",
    "OptimizationManager",
    "SubmissionGenerator",
    "BenchmarkReportGenerator",
    "EvaluationEngine",
    "BenchmarkRunner",
    "GAIATask",
    "TaskLevel",
    "TaskCategory",
    "ErrorCategory",
    "ExecutionTrace",
    "ExecutionStep",
    "EvaluationMetrics",
    "BenchmarkReportModel",
    "NormalizedBenchmarkResult",
    "BenchmarkSuiteMetadata",
    "DatasetIntegrityResult",
    "AnswerFormatConfig",
    "ScoringResult",
    "FailureReport",
    "RegressionReport",
    "OptimizationRecommendation",
    "SubmissionEntry",
    "SubmissionPackage",
]
