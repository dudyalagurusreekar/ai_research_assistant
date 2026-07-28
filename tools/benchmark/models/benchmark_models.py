"""Data models for the GAIA Benchmark Evaluation & Optimization Framework."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_isoformat


class TaskLevel(str, Enum):
    """GAIA benchmark difficulty levels."""
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"


class TaskCategory(str, Enum):
    """GAIA task functional category."""
    WEB_RESEARCH = "web_research"
    FILE_ANALYSIS = "file_analysis"
    CODE_EXECUTION = "code_execution"
    MULTIMODAL_VISION = "multimodal_vision"
    DATA_INTEGRATION = "data_integration"
    MULTI_STEP_REASONING = "multi_step_reasoning"
    CUSTOM = "custom"


class ErrorCategory(str, Enum):
    """Taxonomy categorization of task failures across 16 explicit categories."""
    NONE = "none"
    PLANNING = "planning"
    TOOL_SELECTION = "tool_selection"
    BROWSER = "browser"
    SEARCH = "search"
    DOCUMENT_PARSING = "document_parsing"
    OCR = "ocr"
    VISION = "vision"
    CODE_EXECUTION = "code_execution"
    MEMORY_RETRIEVAL = "memory_retrieval"
    EXTERNAL_INTEGRATION = "external_integration"
    REASONING = "reasoning"
    VERIFICATION = "verification"
    FORMATTING = "formatting"
    TIMEOUT = "timeout"
    INFRASTRUCTURE = "infrastructure"
    UNKNOWN = "unknown"

    # Aliases for backward compatibility
    DOCUMENT = "document_parsing"
    CODE = "code_execution"
    MEMORY = "memory_retrieval"
    INTEGRATION = "external_integration"
    WORKFLOW = "planning"


@dataclass
class BenchmarkSuiteMetadata:
    """Metadata describing a registered benchmark suite."""
    suite_id: str
    name: str
    description: str
    version: str = "1.0.0"
    categories: List[str] = field(default_factory=list)
    difficulty_levels: List[str] = field(default_factory=list)
    default_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "categories": self.categories,
            "difficulty_levels": self.difficulty_levels,
            "default_config": self.default_config,
        }


@dataclass
class DatasetIntegrityResult:
    """Validation output for a loaded benchmark dataset."""
    is_valid: bool = True
    total_tasks: int = 0
    invalid_tasks: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_tasks": self.total_tasks,
            "invalid_tasks": self.invalid_tasks,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass
class GAIATask:
    """Model representing a single GAIA benchmark task."""
    task_id: str = field(default_factory=lambda: generate_id("gaia_"))
    question: str = ""
    level: TaskLevel = TaskLevel.LEVEL_1
    category: TaskCategory = TaskCategory.WEB_RESEARCH
    ground_truth: str = ""
    file_attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "question": self.question,
            "level": self.level.value if isinstance(self.level, TaskLevel) else str(self.level),
            "category": self.category.value if isinstance(self.category, TaskCategory) else str(self.category),
            "ground_truth": self.ground_truth,
            "file_attachments": self.file_attachments,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionStep:
    """Individual workflow execution step trace."""
    step_id: str = field(default_factory=lambda: generate_id("step_"))
    step_type: str = "tool_invocation"
    tool_name: str = ""
    input_params: Dict[str, Any] = field(default_factory=dict)
    output_data: Any = None
    duration_ms: float = 0.0
    status: str = "success"
    error: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type,
            "tool_name": self.tool_name,
            "input_params": self.input_params,
            "output_data": str(self.output_data) if self.output_data is not None else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "retry_count": self.retry_count,
        }


@dataclass
class ExecutionTrace:
    """Record of tool invocations, steps, and intermediate results for a benchmark task."""
    trace_id: str = field(default_factory=lambda: generate_id("tr_"))
    task_id: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    tool_invocations: List[str] = field(default_factory=list)
    final_answer: str = ""
    execution_time_ms: float = 0.0
    retry_history: List[Dict[str, Any]] = field(default_factory=list)
    error_propagation: List[str] = field(default_factory=list)
    timing_info: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "steps": self.steps,
            "tool_invocations": self.tool_invocations,
            "final_answer": self.final_answer,
            "execution_time_ms": self.execution_time_ms,
            "retry_history": self.retry_history,
            "error_propagation": self.error_propagation,
            "timing_info": self.timing_info,
        }


@dataclass
class AnswerFormatConfig:
    """Benchmark formatting rules configuration."""
    rule_type: str = "gaia_default"
    remove_explanations: bool = True
    normalize_numbers: bool = True
    normalize_lists: bool = True
    normalize_strings: bool = True
    custom_regex: Optional[str] = None


@dataclass
class ScoringResult:
    """Scoring result details."""
    is_correct: bool = False
    score: float = 0.0
    match_type: str = "none"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureReport:
    """Detailed failure diagnostic analysis report."""
    task_id: str = ""
    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    probable_root_cause: str = ""
    step_index: int = -1
    stack_trace: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "error_category": self.error_category.value,
            "probable_root_cause": self.probable_root_cause,
            "step_index": self.step_index,
            "stack_trace": self.stack_trace,
            "details": self.details,
        }


@dataclass
class EvaluationMetrics:
    """Telemetry metrics for benchmark execution."""
    total_tasks: int = 0
    passed_tasks: int = 0
    failed_tasks: int = 0
    accuracy_percentage: float = 0.0
    avg_latency_ms: float = 0.0
    median_latency_ms: float = 0.0
    level_1_accuracy: float = 0.0
    level_2_accuracy: float = 0.0
    level_3_accuracy: float = 0.0
    category_accuracies: Dict[str, float] = field(default_factory=dict)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    tool_usage_frequency: Dict[str, int] = field(default_factory=dict)
    retry_count: int = 0
    browser_success_rate: float = 100.0
    ocr_success_rate: float = 100.0
    verification_success_rate: float = 100.0
    memory_hit_rate: float = 100.0
    throughput_tasks_per_sec: float = 0.0
    resource_utilization: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "passed_tasks": self.passed_tasks,
            "failed_tasks": self.failed_tasks,
            "accuracy_percentage": self.accuracy_percentage,
            "avg_latency_ms": self.avg_latency_ms,
            "median_latency_ms": self.median_latency_ms,
            "level_1_accuracy": self.level_1_accuracy,
            "level_2_accuracy": self.level_2_accuracy,
            "level_3_accuracy": self.level_3_accuracy,
            "category_accuracies": self.category_accuracies,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "tool_usage_frequency": self.tool_usage_frequency,
            "retry_count": self.retry_count,
            "browser_success_rate": self.browser_success_rate,
            "ocr_success_rate": self.ocr_success_rate,
            "verification_success_rate": self.verification_success_rate,
            "memory_hit_rate": self.memory_hit_rate,
            "throughput_tasks_per_sec": self.throughput_tasks_per_sec,
            "resource_utilization": self.resource_utilization,
        }


@dataclass
class RegressionReport:
    """Report comparing execution metrics between benchmark runs."""
    run_a_id: str = ""
    run_b_id: str = ""
    improvements: List[str] = field(default_factory=list)
    regressions: List[str] = field(default_factory=list)
    stability_changes: List[str] = field(default_factory=list)
    performance_regressions: List[str] = field(default_factory=list)
    total_delta_accuracy: float = 0.0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_a_id": self.run_a_id,
            "run_b_id": self.run_b_id,
            "improvements": self.improvements,
            "regressions": self.regressions,
            "stability_changes": self.stability_changes,
            "performance_regressions": self.performance_regressions,
            "total_delta_accuracy": self.total_delta_accuracy,
            "summary": self.summary,
        }


@dataclass
class OptimizationRecommendation:
    """Optimization advisor recommendation entry."""
    category: str = ""
    recommendation: str = ""
    reason: str = ""
    priority: str = "medium"
    scope: str = "global"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "recommendation": self.recommendation,
            "reason": self.reason,
            "priority": self.priority,
            "scope": self.scope,
        }


@dataclass
class SubmissionEntry:
    """Entry in official benchmark submission."""
    task_id: str
    model_answer: str
    reasoning_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "task_id": self.task_id,
            "model_answer": self.model_answer,
        }
        if self.reasoning_trace:
            res["reasoning_trace"] = self.reasoning_trace
        if self.metadata:
            res["metadata"] = self.metadata
        return res


@dataclass
class SubmissionPackage:
    """Validated submission file package."""
    submission_id: str = field(default_factory=lambda: generate_id("sub_"))
    suite_name: str = "GAIA Benchmark"
    entries: List[SubmissionEntry] = field(default_factory=list)
    total_tasks: int = 0
    timestamp: str = field(default_factory=utc_isoformat)
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "suite_name": self.suite_name,
            "entries": [e.to_dict() for e in self.entries],
            "total_tasks": self.total_tasks,
            "timestamp": self.timestamp,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }


@dataclass
class NormalizedBenchmarkResult:
    """Result container for a single GAIA task evaluation."""
    result_id: str = field(default_factory=lambda: generate_id("bmres_"))
    task_id: str = ""
    is_correct: bool = True
    score: float = 1.0
    predicted_answer: str = ""
    ground_truth: str = ""
    error_category: ErrorCategory = ErrorCategory.NONE
    trace: Optional[ExecutionTrace] = None
    failure_report: Optional[FailureReport] = None
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "is_correct": self.is_correct,
            "score": self.score,
            "predicted_answer": self.predicted_answer,
            "ground_truth": self.ground_truth,
            "error_category": self.error_category.value if isinstance(self.error_category, ErrorCategory) else str(self.error_category),
            "trace": self.trace.to_dict() if self.trace else None,
            "failure_report": self.failure_report.to_dict() if self.failure_report else None,
            "created_at": self.created_at,
        }


@dataclass
class BenchmarkReportModel:
    """Aggregated report model summarizing a benchmark evaluation run."""
    report_id: str = field(default_factory=lambda: generate_id("bmrep_"))
    suite_name: str = "GAIA Benchmark Evaluation"
    metrics: EvaluationMetrics = field(default_factory=EvaluationMetrics)
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    optimization_recommendations: List[str] = field(default_factory=list)
    detailed_recommendations: List[OptimizationRecommendation] = field(default_factory=list)
    failure_reports: List[FailureReport] = field(default_factory=list)
    regression_report: Optional[RegressionReport] = None
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "suite_name": self.suite_name,
            "metrics": self.metrics.to_dict(),
            "error_breakdown": self.error_breakdown,
            "optimization_recommendations": self.optimization_recommendations,
            "detailed_recommendations": [r.to_dict() for r in self.detailed_recommendations],
            "failure_reports": [f.to_dict() for f in self.failure_reports],
            "regression_report": self.regression_report.to_dict() if self.regression_report else None,
            "created_at": self.created_at,
        }
