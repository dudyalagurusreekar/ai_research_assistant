"""IntelligentPlanningEngine — orchestrates the full planning pipeline.

Coordinates all pipeline components in sequence: query analysis, intent
classification, complexity estimation, task decomposition, DAG generation,
tool selection, dependency analysis, parallel planning, constraint
enforcement, and decision logging.

Produces a fully-populated PlannerContext containing the optimized execution
plan ready for downstream consumption by SafeCodeAgent or SessionOrchestrator.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.planner.interfaces.base import IPlanningEngine
from core.planner.models.context import PlannerContext, PlannerStage
from core.planner.components.query_analyzer import QueryAnalyzer
from core.planner.components.intent_classifier import IntentClassifier
from core.planner.components.complexity_estimator import ComplexityEstimator
from core.planner.components.task_decomposer import TaskDecomposer
from core.planner.components.dag_generator import DAGGenerator
from core.planner.components.tool_selector import ToolSelector
from core.planner.components.dependency_analyzer import DependencyAnalyzer
from core.planner.components.parallel_planner import ParallelPlanner
from core.planner.components.constraint_enforcer import ConstraintEnforcer
from core.planner.components.decision_logger import DecisionLogger
from infrastructure.logging.logger import StructuredLogger


class IntelligentPlanningEngine(IPlanningEngine):
    """Production planning engine executing the 10-stage pipeline.

    All components are injected at construction time, allowing full testability
    and extensibility.  Each stage writes its output into the shared
    PlannerContext, and errors in non-critical stages are recorded but do not
    abort the pipeline.
    """

    def __init__(
        self,
        query_analyzer: Optional[QueryAnalyzer] = None,
        intent_classifier: Optional[IntentClassifier] = None,
        complexity_estimator: Optional[ComplexityEstimator] = None,
        task_decomposer: Optional[TaskDecomposer] = None,
        dag_generator: Optional[DAGGenerator] = None,
        tool_selector: Optional[ToolSelector] = None,
        dependency_analyzer: Optional[DependencyAnalyzer] = None,
        parallel_planner: Optional[ParallelPlanner] = None,
        constraint_enforcer: Optional[ConstraintEnforcer] = None,
        decision_logger: Optional[DecisionLogger] = None,
    ) -> None:
        self._query_analyzer = query_analyzer or QueryAnalyzer()
        self._intent_classifier = intent_classifier or IntentClassifier()
        self._complexity_estimator = complexity_estimator or ComplexityEstimator()
        self._task_decomposer = task_decomposer or TaskDecomposer()
        self._dag_generator = dag_generator or DAGGenerator()
        self._tool_selector = tool_selector or ToolSelector()
        self._dependency_analyzer = dependency_analyzer or DependencyAnalyzer()
        self._parallel_planner = parallel_planner or ParallelPlanner()
        self._constraint_enforcer = constraint_enforcer or ConstraintEnforcer()
        self._decision_logger = decision_logger or DecisionLogger()
        self._logger = StructuredLogger("IntelligentPlanningEngine")

    def plan(
        self,
        query: str,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> PlannerContext:
        """Execute the full 10-stage planning pipeline.

        Args:
            query: Raw user request string.
            available_tools: List of tool metadata dicts (name, description, capabilities).
            conversation_history: Prior conversation turns for context.
            session_id: Optional session identifier for correlation.

        Returns:
            Fully-populated PlannerContext with execution plan, tool selection,
            DAG, constraints, metrics, and reasoning trace.
        """
        ctx = PlannerContext(
            user_query=query,
            available_tools=available_tools or [],
            conversation_history=conversation_history or [],
            session_id=session_id,
        )
        ctx.metrics.planning_start_time = datetime.now(timezone.utc)
        self._decision_logger.initialize(ctx.plan_id)

        self._logger.info(f"Planning started for query: '{query[:100]}' (plan_id={ctx.plan_id})")

        # Execute pipeline stages — each is wrapped in error handling
        stages = [
            ("query_analysis", PlannerStage.QUERY_ANALYZED, self._run_query_analysis),
            ("intent_classification", PlannerStage.INTENT_CLASSIFIED, self._run_intent_classification),
            ("complexity_estimation", PlannerStage.COMPLEXITY_ESTIMATED, self._run_complexity_estimation),
            ("task_decomposition", PlannerStage.TASKS_DECOMPOSED, self._run_task_decomposition),
            ("dag_generation", PlannerStage.DAG_GENERATED, self._run_dag_generation),
            ("tool_selection", PlannerStage.TOOLS_SELECTED, self._run_tool_selection),
            ("dependency_analysis", PlannerStage.DEPENDENCIES_ANALYZED, self._run_dependency_analysis),
            ("parallel_planning", PlannerStage.PARALLELISM_PLANNED, self._run_parallel_planning),
            ("constraint_enforcement", PlannerStage.CONSTRAINTS_ENFORCED, self._run_constraint_enforcement),
            ("decision_logging", PlannerStage.PLANNING_COMPLETE, self._run_decision_finalization),
        ]

        for stage_name, stage_enum, stage_fn in stages:
            try:
                stage_fn(ctx)
                ctx.advance_stage(stage_enum)
            except Exception as e:
                ctx.add_error(stage=stage_name, error=str(e), recoverable=True)
                self._logger.error(f"Stage '{stage_name}' failed: {e}")
                # Non-critical stages continue; critical stages mark failure
                if stage_name in ("query_analysis", "task_decomposition", "dag_generation"):
                    ctx.advance_stage(PlannerStage.PLANNING_FAILED)
                    break

        ctx.metrics.planning_end_time = datetime.now(timezone.utc)
        ctx.metrics.compute_latency()

        self._logger.info(
            f"Planning completed: stage={ctx.current_stage.value}, "
            f"latency={ctx.metrics.planning_latency_ms:.1f}ms, "
            f"errors={len(ctx.errors)}"
        )
        return ctx

    # ------------------------------------------------------------------
    # Pipeline stage runners
    # ------------------------------------------------------------------

    def _run_query_analysis(self, ctx: PlannerContext) -> None:
        self._query_analyzer.analyze(ctx)
        self._decision_logger.log_decision(
            ctx, stage="query_analysis",
            description=f"Query analyzed: {len(ctx.query_analysis.keywords)} keywords extracted",
            rationale="Deterministic NLP heuristics for fast, reliable query understanding",
            confidence=1.0,
            data={"ambiguity": ctx.query_analysis.ambiguity_score},
        )

    def _run_intent_classification(self, ctx: PlannerContext) -> None:
        intent, confidence = self._intent_classifier.classify(ctx)
        
        # Consult Continuous Learning & Experience Engine for historical strategy recommendations
        try:
            from core.learning.integration import get_learning_engine
            learning_engine = get_learning_engine()
            rec = learning_engine.consult_experience(query=ctx.user_query, intent=intent.value if intent else None)
            if not hasattr(ctx, "metadata") or ctx.metadata is None:
                ctx.metadata = {}
            ctx.metadata["strategy_recommendation"] = rec
        except Exception as e:
            self._logger.warning(f"Could not consult Learning Engine: {e}")

        self._decision_logger.log_decision(
            ctx, stage="intent_classification",
            description=f"Intent classified as '{intent.value}'",
            rationale="Weighted keyword scoring with contextual signal boosters and historical experience lookup",
            confidence=confidence,
            data={"intent": intent.value},
        )

    def _run_complexity_estimation(self, ctx: PlannerContext) -> None:
        estimate = self._complexity_estimator.estimate(ctx)
        self._decision_logger.log_decision(
            ctx, stage="complexity_estimation",
            description=f"Complexity score: {estimate.score}/10, {estimate.estimated_steps} steps",
            rationale=estimate.reasoning,
            confidence=0.9,
            data={"score": estimate.score, "steps": estimate.estimated_steps},
        )

    def _run_task_decomposition(self, ctx: PlannerContext) -> None:
        sub_tasks = self._task_decomposer.decompose(ctx)
        self._decision_logger.log_decision(
            ctx, stage="task_decomposition",
            description=f"Decomposed into {len(sub_tasks)} sub-tasks",
            rationale=f"Intent-driven template for '{ctx.intent.value if ctx.intent else 'unknown'}'",
            confidence=0.95,
            data={"task_count": len(sub_tasks)},
        )

    def _run_dag_generation(self, ctx: PlannerContext) -> None:
        graph = self._dag_generator.generate(ctx)
        self._decision_logger.log_decision(
            ctx, stage="dag_generation",
            description=f"DAG generated: {graph.node_count()} nodes, {graph.edge_count()} edges",
            rationale="Nodes from sub-tasks, edges from declared dependencies",
            confidence=1.0 if not graph.has_cycle() else 0.0,
            data={"nodes": graph.node_count(), "edges": graph.edge_count()},
        )

    def _run_tool_selection(self, ctx: PlannerContext) -> None:
        selection = self._tool_selector.select(ctx)
        self._decision_logger.log_decision(
            ctx, stage="tool_selection",
            description=f"Selected {len(selection.selected_tools)}/{selection.total_available} tools "
                        f"({selection.reduction_percentage}% reduction)",
            rationale="Minimum tool set matching sub-task requirements",
            confidence=0.95,
            data={"selected": selection.selected_tools, "reduction": selection.reduction_percentage},
        )

    def _run_dependency_analysis(self, ctx: PlannerContext) -> None:
        self._dependency_analyzer.analyze_dependencies(ctx)
        self._decision_logger.log_decision(
            ctx, stage="dependency_analysis",
            description="Data-flow dependencies validated and refined",
            rationale="Second-pass edge validation ensuring input_key satisfaction",
            confidence=1.0,
        )

    def _run_parallel_planning(self, ctx: PlannerContext) -> None:
        levels = self._parallel_planner.plan_parallelism(ctx)
        self._decision_logger.log_decision(
            ctx, stage="parallel_planning",
            description=f"Identified {len(levels)} execution waves",
            rationale="DAG topological level computation",
            confidence=1.0,
            data={"wave_count": len(levels), "max_concurrency": max(len(g) for g in levels) if levels else 0},
        )

    def _run_constraint_enforcement(self, ctx: PlannerContext) -> None:
        constraints = self._constraint_enforcer.enforce(ctx)
        self._decision_logger.log_decision(
            ctx, stage="constraint_enforcement",
            description=f"Constraints set: {constraints.max_steps} steps, "
                        f"{constraints.timeout_seconds:.0f}s timeout",
            rationale="Derived from complexity estimate and intent profile",
            confidence=1.0,
            data={"max_steps": constraints.max_steps, "timeout": constraints.timeout_seconds},
        )

    def _run_decision_finalization(self, ctx: PlannerContext) -> None:
        self._decision_logger.finalize(ctx)
