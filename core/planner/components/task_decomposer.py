"""TaskDecomposer — breaks complex objectives into atomic sub-tasks.

Uses intent-driven decomposition templates to generate a list of typed SubTask
objects with tool assignments, parameters, and dependency declarations.
"""

from __future__ import annotations

from typing import Dict, List

from core.planner.interfaces.base import ITaskDecomposer
from core.planner.models.context import PlannerContext, QueryIntent, SubTask
from infrastructure.logging.logger import StructuredLogger


class TaskDecomposer(ITaskDecomposer):
    """Deterministic task decomposer using intent-based decomposition templates."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("TaskDecomposer")

    @property
    def component_name(self) -> str:
        return "TaskDecomposer"

    def decompose(self, ctx: PlannerContext) -> List[SubTask]:
        """Decompose the query into atomic sub-tasks based on classified intent."""
        intent = ctx.intent or QueryIntent.AMBIGUOUS
        raw_query = ctx.user_query

        dispatch = {
            QueryIntent.FACTUAL_QA: self._decompose_factual_qa,
            QueryIntent.COMPARISON: self._decompose_comparison,
            QueryIntent.DOCUMENT_ANALYSIS: self._decompose_document_analysis,
            QueryIntent.CODE_EXECUTION: self._decompose_code_execution,
            QueryIntent.VISION_ANALYSIS: self._decompose_vision_analysis,
            QueryIntent.MULTI_STEP_RESEARCH: self._decompose_multi_step_research,
            QueryIntent.AMBIGUOUS: self._decompose_ambiguous,
            QueryIntent.MEMORY_OPERATION: self._decompose_memory_operation,
            QueryIntent.REPORT_GENERATION: self._decompose_report_generation,
        }

        decomposer = dispatch.get(intent, self._decompose_ambiguous)
        sub_tasks = decomposer(raw_query, ctx)

        ctx.sub_tasks = sub_tasks
        ctx.add_trace(
            stage="task_decomposition",
            message=f"Decomposed into {len(sub_tasks)} sub-tasks for intent '{intent.value}'",
            data={"tasks": [{"id": t.task_id, "title": t.title, "tool": t.tool_name} for t in sub_tasks]},
        )
        self._logger.info(f"Decomposed query into {len(sub_tasks)} sub-tasks")
        return sub_tasks

    # ------------------------------------------------------------------
    # Decomposition strategies
    # ------------------------------------------------------------------

    def _decompose_factual_qa(self, query: str, ctx: PlannerContext) -> List[SubTask]:
        search = SubTask(
            title=f"Search for: {query[:80]}",
            tool_name="search_tool",
            action="search",
            parameters={"query": query},
            output_keys=["search_results"],
            estimated_latency_seconds=10.0,
        )
        synthesize = SubTask(
            title="Synthesize factual answer",
            tool_name="python_interpreter",
            action="synthesize",
            parameters={"task": "synthesize_answer", "query": query},
            dependencies=[search.task_id],
            input_keys=["search_results"],
            output_keys=["answer"],
            estimated_latency_seconds=5.0,
        )
        return [search, synthesize]

    def _decompose_comparison(self, query: str, ctx: PlannerContext) -> List[SubTask]:
        source_count = ctx.query_analysis.source_count_hint if ctx.query_analysis else 2

        search_tasks: List[SubTask] = []
        for i in range(source_count):
            t = SubTask(
                title=f"Research source {i + 1} for comparison",
                tool_name="search_tool",
                action="search",
                parameters={"query": query, "source_index": i},
                output_keys=[f"source_{i}_results"],
                estimated_latency_seconds=10.0,
            )
            search_tasks.append(t)

        compare = SubTask(
            title="Compare and contrast findings",
            tool_name="python_interpreter",
            action="compare",
            parameters={"task": "compare_results", "query": query},
            dependencies=[t.task_id for t in search_tasks],
            input_keys=[f"source_{i}_results" for i in range(source_count)],
            output_keys=["comparison_result"],
            estimated_latency_seconds=10.0,
        )
        return search_tasks + [compare]

    def _decompose_document_analysis(self, query: str, ctx: PlannerContext) -> List[SubTask]:
        load = SubTask(
            title="Load and parse document",
            tool_name="document_tool",
            action="read",
            parameters={"query": query},
            output_keys=["document_content"],
            estimated_latency_seconds=15.0,
        )
        analyze = SubTask(
            title="Analyze document content",
            tool_name="python_interpreter",
            action="analyze",
            parameters={"task": "document_analysis", "query": query},
            dependencies=[load.task_id],
            input_keys=["document_content"],
            output_keys=["analysis_result"],
            estimated_latency_seconds=10.0,
        )
        return [load, analyze]

    def _decompose_code_execution(self, query: str, ctx: PlannerContext) -> List[SubTask]:
        execute = SubTask(
            title="Execute code snippet",
            tool_name="code_tool",
            action="execute",
            parameters={"query": query},
            output_keys=["code_output"],
            estimated_latency_seconds=10.0,
        )
        return [execute]

    def _decompose_vision_analysis(self, query: str, ctx: PlannerContext) -> List[SubTask]:
        capture = SubTask(
            title="Capture or load image",
            tool_name="vision_tool",
            action="capture",
            parameters={"query": query},
            output_keys=["image_data"],
            estimated_latency_seconds=5.0,
        )
        analyze = SubTask(
            title="Analyze visual content",
            tool_name="vision_tool",
            action="analyze",
            parameters={"query": query},
            dependencies=[capture.task_id],
            input_keys=["image_data"],
            output_keys=["vision_result"],
            estimated_latency_seconds=15.0,
        )
        return [capture, analyze]

    def _decompose_multi_step_research(self, query: str, ctx: PlannerContext) -> List[SubTask]:
        plan = SubTask(
            title="Plan research strategy",
            tool_name="python_interpreter",
            action="plan",
            parameters={"task": "research_planning", "query": query},
            output_keys=["research_plan"],
            estimated_latency_seconds=5.0,
        )
        search = SubTask(
            title="Execute multi-source search",
            tool_name="search_tool",
            action="search",
            parameters={"query": query},
            dependencies=[plan.task_id],
            input_keys=["research_plan"],
            output_keys=["search_results"],
            estimated_latency_seconds=20.0,
        )
        browse = SubTask(
            title="Browse key sources for details",
            tool_name="browser_tool",
            action="browse",
            parameters={"query": query},
            dependencies=[search.task_id],
            input_keys=["search_results"],
            output_keys=["browsed_content"],
            estimated_latency_seconds=30.0,
            is_optional=True,
        )
        synthesize = SubTask(
            title="Synthesize comprehensive research report",
            tool_name="python_interpreter",
            action="synthesize",
            parameters={"task": "research_synthesis", "query": query},
            dependencies=[search.task_id, browse.task_id],
            input_keys=["search_results", "browsed_content"],
            output_keys=["research_report"],
            estimated_latency_seconds=15.0,
        )
        return [plan, search, browse, synthesize]

    def _decompose_memory_operation(self, query: str, ctx: PlannerContext) -> List[SubTask]:
        memory = SubTask(
            title="Perform memory operation",
            tool_name="memory_tool",
            action="store_or_recall",
            parameters={"query": query},
            output_keys=["memory_result"],
            estimated_latency_seconds=3.0,
        )
        return [memory]

    def _decompose_report_generation(self, query: str, ctx: PlannerContext) -> List[SubTask]:
        gather = SubTask(
            title="Gather content for report",
            tool_name="document_tool",
            action="read",
            parameters={"query": query},
            output_keys=["source_content"],
            estimated_latency_seconds=10.0,
        )
        generate = SubTask(
            title="Generate structured report",
            tool_name="python_interpreter",
            action="generate_report",
            parameters={"task": "report_generation", "query": query},
            dependencies=[gather.task_id],
            input_keys=["source_content"],
            output_keys=["report"],
            estimated_latency_seconds=15.0,
        )
        validate = SubTask(
            title="Validate report structure",
            tool_name="report_tool",
            action="validate",
            parameters={"task": "validate_report"},
            dependencies=[generate.task_id],
            input_keys=["report"],
            output_keys=["validation_result"],
            estimated_latency_seconds=5.0,
        )
        return [gather, generate, validate]

    def _decompose_ambiguous(self, query: str, ctx: PlannerContext) -> List[SubTask]:
        search = SubTask(
            title=f"General search: {query[:80]}",
            tool_name="search_tool",
            action="search",
            parameters={"query": query},
            output_keys=["search_results"],
            estimated_latency_seconds=10.0,
        )
        answer = SubTask(
            title="Generate answer from search results",
            tool_name="python_interpreter",
            action="synthesize",
            parameters={"task": "answer_generation", "query": query},
            dependencies=[search.task_id],
            input_keys=["search_results"],
            output_keys=["answer"],
            estimated_latency_seconds=10.0,
        )
        return [search, answer]
