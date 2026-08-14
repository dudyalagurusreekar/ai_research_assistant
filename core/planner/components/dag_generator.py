"""DAGGenerator — constructs a validated ExecutionGraph from sub-tasks.

Converts the list of SubTask objects into PlanNode/PlanEdge structures,
validates acyclicity, and produces a ready-to-execute DAG.
"""

from __future__ import annotations

from core.planner.interfaces.base import IDAGGenerator
from core.planner.models.context import PlannerContext
from core.planner.models.graph import ExecutionGraph, PlanEdge, PlanNode
from infrastructure.logging.logger import StructuredLogger


class DAGGenerator(IDAGGenerator):
    """Builds an ExecutionGraph DAG from the decomposed sub-task list."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("DAGGenerator")

    @property
    def component_name(self) -> str:
        return "DAGGenerator"

    def generate(self, ctx: PlannerContext) -> ExecutionGraph:
        """Convert sub-tasks into a validated DAG with proper edges."""
        graph = ExecutionGraph()

        # 1. Create nodes from sub-tasks
        task_id_to_node_id: dict[str, str] = {}
        for sub_task in ctx.sub_tasks:
            node = PlanNode(
                task_id=sub_task.task_id,
                title=sub_task.title,
                tool_name=sub_task.tool_name,
                action=sub_task.action,
                parameters=sub_task.parameters,
                input_keys=list(sub_task.input_keys),
                output_keys=list(sub_task.output_keys),
                estimated_latency_seconds=sub_task.estimated_latency_seconds,
                is_optional=sub_task.is_optional,
            )
            graph.add_node(node)
            task_id_to_node_id[sub_task.task_id] = node.node_id

        # 2. Create edges from declared dependencies
        for sub_task in ctx.sub_tasks:
            target_node_id = task_id_to_node_id.get(sub_task.task_id)
            if not target_node_id:
                continue
            for dep_task_id in sub_task.dependencies:
                source_node_id = task_id_to_node_id.get(dep_task_id)
                if not source_node_id:
                    self._logger.warning(
                        f"Dependency '{dep_task_id}' not found for task '{sub_task.task_id}'; skipping edge."
                    )
                    continue

                # Determine data key from overlapping output->input keys
                source_task = next((t for t in ctx.sub_tasks if t.task_id == dep_task_id), None)
                data_key = ""
                if source_task:
                    shared = set(source_task.output_keys) & set(sub_task.input_keys)
                    data_key = next(iter(shared), "")

                try:
                    edge = PlanEdge(
                        source_id=source_node_id,
                        target_id=target_node_id,
                        data_key=data_key,
                        is_required=not sub_task.is_optional,
                    )
                    graph.add_edge(edge)
                except ValueError as e:
                    ctx.add_error(
                        stage="dag_generation",
                        error=f"Failed to add edge {dep_task_id} -> {sub_task.task_id}: {e}",
                        recoverable=True,
                    )
                    self._logger.warning(f"Edge creation failed: {e}")

        # 3. Validate — ensure no cycles remain
        if graph.has_cycle():
            ctx.add_error(
                stage="dag_generation",
                error="Generated graph contains a cycle — this should not happen.",
                recoverable=False,
            )
            self._logger.error("CRITICAL: Generated DAG contains a cycle!")

        ctx.execution_graph = graph
        ctx.metrics.dag_node_count = graph.node_count()
        ctx.metrics.dag_edge_count = graph.edge_count()
        ctx.add_trace(
            stage="dag_generation",
            message=f"Generated DAG with {graph.node_count()} nodes and {graph.edge_count()} edges",
            data=graph.to_dict(),
        )
        self._logger.info(
            f"DAG generated: {graph.node_count()} nodes, {graph.edge_count()} edges"
        )
        return graph
