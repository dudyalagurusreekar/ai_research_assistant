"""PlannerContext — shared state container for the planning pipeline.

Every planner component operates from PlannerContext rather than passing large
parameter lists between stages.  The context accumulates query understanding,
intent classification, complexity estimation, task decomposition, execution graph,
selected tools, constraints, metrics, and a reasoning trace.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.planner.models.graph import ExecutionGraph


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class QueryIntent(Enum):
    """Classified intent categories for incoming research queries."""

    FACTUAL_QA = "factual_qa"
    COMPARISON = "comparison"
    DOCUMENT_ANALYSIS = "document_analysis"
    CODE_EXECUTION = "code_execution"
    VISION_ANALYSIS = "vision_analysis"
    MULTI_STEP_RESEARCH = "multi_step_research"
    AMBIGUOUS = "ambiguous"
    MEMORY_OPERATION = "memory_operation"
    REPORT_GENERATION = "report_generation"


class PlannerStage(Enum):
    """Pipeline stages through which a planning request progresses."""

    INITIALIZED = "initialized"
    QUERY_ANALYZED = "query_analyzed"
    INTENT_CLASSIFIED = "intent_classified"
    COMPLEXITY_ESTIMATED = "complexity_estimated"
    TASKS_DECOMPOSED = "tasks_decomposed"
    DAG_GENERATED = "dag_generated"
    TOOLS_SELECTED = "tools_selected"
    DEPENDENCIES_ANALYZED = "dependencies_analyzed"
    PARALLELISM_PLANNED = "parallelism_planned"
    CONSTRAINTS_ENFORCED = "constraints_enforced"
    PLANNING_COMPLETE = "planning_complete"
    PLANNING_FAILED = "planning_failed"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

@dataclass
class QueryAnalysis:
    """Structured output of the query understanding stage."""

    raw_query: str = ""
    normalized_query: str = ""
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    research_requirements: List[str] = field(default_factory=list)
    ambiguity_score: float = 0.0
    language: str = "en"
    has_file_reference: bool = False
    has_url_reference: bool = False
    has_code_request: bool = False
    has_comparison: bool = False
    source_count_hint: int = 1


@dataclass
class ComplexityEstimate:
    """Estimated complexity metrics for the request."""

    score: int = 1  # 1-10 scale
    estimated_steps: int = 1
    estimated_tool_calls: int = 1
    estimated_tokens: int = 500
    estimated_latency_seconds: float = 5.0
    max_step_limit: int = 15
    reasoning: str = ""


@dataclass
class SubTask:
    """An atomic sub-task produced by the task decomposer."""

    task_id: str = field(default_factory=lambda: f"subtask_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    tool_name: str = ""
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    input_keys: List[str] = field(default_factory=list)
    output_keys: List[str] = field(default_factory=list)
    is_optional: bool = False
    estimated_latency_seconds: float = 1.0


@dataclass
class ToolSelection:
    """Result of the tool selection stage."""

    selected_tools: List[str] = field(default_factory=list)
    excluded_tools: List[str] = field(default_factory=list)
    selection_reasons: Dict[str, str] = field(default_factory=dict)
    total_available: int = 0
    reduction_percentage: float = 0.0


@dataclass
class ExecutionConstraints:
    """Hard and soft constraints governing the execution plan."""

    max_steps: int = 15
    max_tool_calls: int = 10
    max_tokens: int = 8192
    timeout_seconds: float = 300.0
    allow_parallel: bool = True
    require_verification: bool = True
    max_retries_per_step: int = 2
    stopping_criteria: List[str] = field(default_factory=list)


@dataclass
class PlannerMetrics:
    """Timing and performance metrics collected during planning."""

    planning_start_time: Optional[datetime] = None
    planning_end_time: Optional[datetime] = None
    planning_latency_ms: float = 0.0
    stages_completed: int = 0
    total_stages: int = 10
    tool_selection_accuracy: float = 0.0
    dag_node_count: int = 0
    dag_edge_count: int = 0
    parallel_groups: int = 0
    unnecessary_tools_removed: int = 0

    def compute_latency(self) -> None:
        """Compute planning latency from start/end timestamps."""
        if self.planning_start_time and self.planning_end_time:
            delta = self.planning_end_time - self.planning_start_time
            self.planning_latency_ms = delta.total_seconds() * 1000.0


# ---------------------------------------------------------------------------
# Main PlannerContext
# ---------------------------------------------------------------------------

@dataclass
class PlannerContext:
    """Shared mutable state container flowing through all planner pipeline stages.

    Every component reads from and writes to PlannerContext, ensuring a single
    source of truth for the entire planning pipeline.
    """

    # Identity
    plan_id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Input
    user_query: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    session_id: Optional[str] = None

    # Available tool metadata (populated before planning begins)
    available_tools: List[Dict[str, Any]] = field(default_factory=list)

    # Pipeline stage
    current_stage: PlannerStage = PlannerStage.INITIALIZED

    # Stage outputs
    query_analysis: Optional[QueryAnalysis] = None
    intent: Optional[QueryIntent] = None
    intent_confidence: float = 0.0
    complexity: Optional[ComplexityEstimate] = None
    sub_tasks: List[SubTask] = field(default_factory=list)
    execution_graph: Optional[ExecutionGraph] = None
    tool_selection: Optional[ToolSelection] = None
    constraints: ExecutionConstraints = field(default_factory=ExecutionConstraints)
    parallel_groups: List[List[str]] = field(default_factory=list)

    # Metrics & trace
    metrics: PlannerMetrics = field(default_factory=PlannerMetrics)
    reasoning_trace: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    # ---------------------------------------------------------------------------
    # Convenience methods
    # ---------------------------------------------------------------------------

    @property
    def parallel_levels(self) -> List[List[SubTask]]:
        """Return sub-tasks grouped by parallel wave execution levels."""
        if not self.parallel_groups:
            return [[t] for t in self.sub_tasks] if self.sub_tasks else []
        
        task_map = {t.task_id: t for t in self.sub_tasks}
        result = []
        for group in self.parallel_groups:
            wave_tasks = [task_map[tid] for tid in group if tid in task_map]
            if wave_tasks:
                result.append(wave_tasks)
        return result or ([[t] for t in self.sub_tasks] if self.sub_tasks else [])

    @property
    def selected_tools(self) -> List[str]:
        """Return list of selected tool names."""
        return self.tool_selection.selected_tools if self.tool_selection else [t.tool_name for t in self.sub_tasks if t.tool_name]

    @property
    def complexity_score(self) -> int:
        """Return complexity score 1-10."""
        return self.complexity.score if self.complexity else 5

    def add_trace(self, stage: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Append a structured entry to the reasoning trace."""

        self.reasoning_trace.append({
            "stage": stage,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def add_error(self, stage: str, error: str, recoverable: bool = True) -> None:
        """Record an error encountered during a pipeline stage."""
        self.errors.append({
            "stage": stage,
            "error": error,
            "recoverable": recoverable,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def advance_stage(self, stage: PlannerStage) -> None:
        """Move to the next pipeline stage and increment the stages-completed counter."""
        self.current_stage = stage
        self.metrics.stages_completed += 1

    def is_failed(self) -> bool:
        """Return True if the planning pipeline has entered a failed state."""
        return self.current_stage == PlannerStage.PLANNING_FAILED

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to a JSON-friendly dictionary for logging and persistence."""
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at.isoformat(),
            "user_query": self.user_query,
            "current_stage": self.current_stage.value,
            "intent": self.intent.value if self.intent else None,
            "intent_confidence": self.intent_confidence,
            "complexity_score": self.complexity.score if self.complexity else None,
            "sub_task_count": len(self.sub_tasks),
            "selected_tools": self.tool_selection.selected_tools if self.tool_selection else [],
            "parallel_groups": self.parallel_groups,
            "metrics": {
                "planning_latency_ms": self.metrics.planning_latency_ms,
                "stages_completed": self.metrics.stages_completed,
                "dag_node_count": self.metrics.dag_node_count,
                "parallel_groups": self.metrics.parallel_groups,
                "unnecessary_tools_removed": self.metrics.unnecessary_tools_removed,
            },
            "error_count": len(self.errors),
            "trace_length": len(self.reasoning_trace),
        }
