"""Data models for the GAIA Benchmark Evaluation & Optimization Framework."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now, utc_isoformat


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


class ErrorCategory(str, Enum):
    """Taxonomy categorization of task failures."""
    NONE = "none"
    PLANNING = "planning"
    BROWSER = "browser"
    SEARCH = "search"
    DOCUMENT = "document"
    VISION = "vision"
    CODE = "code"
    MEMORY = "memory"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"
    REASONING = "reasoning"
    VERIFICATION = "verification"


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
            "level": self.level.value,
            "category": self.category.value,
            "ground_truth": self.ground_truth,
            "file_attachments": self.file_attachments,
            "metadata": self.metadata,
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "steps": self.steps,
            "tool_invocations": self.tool_invocations,
            "final_answer": self.final_answer,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class EvaluationMetrics:
    """Telemetry metrics for benchmark execution."""
    total_tasks: int = 0
    passed_tasks: int = 0
    failed_tasks: int = 0
    accuracy_percentage: float = 0.0
    avg_latency_ms: float = 0.0
    level_1_accuracy: float = 0.0
    level_2_accuracy: float = 0.0
    level_3_accuracy: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "passed_tasks": self.passed_tasks,
            "failed_tasks": self.failed_tasks,
            "accuracy_percentage": self.accuracy_percentage,
            "avg_latency_ms": self.avg_latency_ms,
            "level_1_accuracy": self.level_1_accuracy,
            "level_2_accuracy": self.level_2_accuracy,
            "level_3_accuracy": self.level_3_accuracy,
        }


@dataclass
class BenchmarkReportModel:
    """Aggregated report model summarizing a GAIA evaluation run."""
    report_id: str = field(default_factory=lambda: generate_id("bmrep_"))
    suite_name: str = "GAIA Benchmark Evaluation"
    metrics: EvaluationMetrics = field(default_factory=EvaluationMetrics)
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    optimization_recommendations: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "suite_name": self.suite_name,
            "metrics": self.metrics.to_dict(),
            "error_breakdown": self.error_breakdown,
            "optimization_recommendations": self.optimization_recommendations,
            "created_at": self.created_at,
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
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "is_correct": self.is_correct,
            "score": self.score,
            "predicted_answer": self.predicted_answer,
            "ground_truth": self.ground_truth,
            "error_category": self.error_category.value,
            "trace": self.trace.to_dict() if self.trace else None,
            "created_at": self.created_at,
        }
