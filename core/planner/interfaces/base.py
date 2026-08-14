"""Abstract interfaces for every planner pipeline component.

Each interface defines a single responsibility with a well-typed contract.
Concrete implementations live under ``core.planner.components``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from core.planner.models.context import (
    ComplexityEstimate,
    ExecutionConstraints,
    PlannerContext,
    QueryAnalysis,
    QueryIntent,
    SubTask,
    ToolSelection,
)
from core.planner.models.graph import ExecutionGraph


class IPlannerComponent(ABC):
    """Base interface shared by all planner pipeline components."""

    @property
    @abstractmethod
    def component_name(self) -> str:
        """Human-readable component identifier for logging and tracing."""


class IQueryAnalyzer(IPlannerComponent):
    """Extracts structured understanding from a raw user query."""

    @abstractmethod
    def analyze(self, ctx: PlannerContext) -> QueryAnalysis:
        """Analyze the user query and return structured semantics."""


class IIntentClassifier(IPlannerComponent):
    """Classifies a query into a standard intent category."""

    @abstractmethod
    def classify(self, ctx: PlannerContext) -> tuple[QueryIntent, float]:
        """Return (intent, confidence) for the current query analysis."""


class IComplexityEstimator(IPlannerComponent):
    """Estimates request complexity, cost, and resource requirements."""

    @abstractmethod
    def estimate(self, ctx: PlannerContext) -> ComplexityEstimate:
        """Produce a complexity estimate for the current planning context."""


class ITaskDecomposer(IPlannerComponent):
    """Decomposes a complex objective into atomic sub-tasks."""

    @abstractmethod
    def decompose(self, ctx: PlannerContext) -> List[SubTask]:
        """Return an ordered list of sub-tasks for the request."""


class IDAGGenerator(IPlannerComponent):
    """Generates an ExecutionGraph (DAG) from a list of sub-tasks."""

    @abstractmethod
    def generate(self, ctx: PlannerContext) -> ExecutionGraph:
        """Build and return a validated execution DAG."""


class IToolSelector(IPlannerComponent):
    """Determines which tools are actually required for a given request."""

    @abstractmethod
    def select(self, ctx: PlannerContext) -> ToolSelection:
        """Filter available tools to the minimum required set."""


class IDependencyAnalyzer(IPlannerComponent):
    """Analyzes data dependencies between DAG nodes."""

    @abstractmethod
    def analyze_dependencies(self, ctx: PlannerContext) -> None:
        """Refine edges in the execution graph based on data-flow analysis."""


class IParallelPlanner(IPlannerComponent):
    """Identifies independent DAG nodes that can execute concurrently."""

    @abstractmethod
    def plan_parallelism(self, ctx: PlannerContext) -> List[List[str]]:
        """Return grouped node IDs representing concurrent execution waves."""


class IConstraintEnforcer(IPlannerComponent):
    """Establishes and validates execution constraints and stopping criteria."""

    @abstractmethod
    def enforce(self, ctx: PlannerContext) -> ExecutionConstraints:
        """Compute and attach execution constraints to the plan."""


class IDecisionLogger(IPlannerComponent):
    """Records and exposes structured decision metrics and reasoning traces."""

    @abstractmethod
    def log_decision(
        self,
        ctx: PlannerContext,
        stage: str,
        description: str,
        rationale: str = "",
        confidence: float = 1.0,
        data: Dict[str, Any] | None = None,
    ) -> None:
        """Record a structured planning decision."""

    @abstractmethod
    def finalize(self, ctx: PlannerContext) -> Dict[str, Any]:
        """Finalize metrics and return the complete decision summary."""


class IPlanningEngine(ABC):
    """Top-level orchestrator that runs the full planning pipeline."""

    @abstractmethod
    def plan(self, query: str, available_tools: List[Dict[str, Any]] | None = None,
             conversation_history: List[Dict[str, str]] | None = None,
             session_id: str | None = None) -> PlannerContext:
        """Execute the full planning pipeline and return the completed context."""
