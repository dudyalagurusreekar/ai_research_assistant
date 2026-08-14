"""PlanCritic — critiques the execution graph for redundant or dead-end steps.

Analyzes the ExecutionGraph (DAG) against executed outputs to identify redundant
tool calls, unneeded intermediate nodes, and missing dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from core.planner.models.context import PlannerContext
from core.planner.models.graph import ExecutionGraph
from core.reflection.models.reflection import PlanCriticReport
from infrastructure.logging.logger import StructuredLogger


class PlanCritic:
    """Critiques DAG execution plans to prune redundant and dead-end nodes."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("PlanCritic")

    def critique(self, ctx: PlannerContext, task_outputs: Dict[str, Any]) -> PlanCriticReport:
        """Critique the current DAG graph in PlannerContext.

        Args:
            ctx: PlannerContext detailing execution graph and sub-tasks.
            task_outputs: Dict of completed task outputs.

        Returns:
            PlanCriticReport with redundant_node_ids, dead_end_node_ids, and suggested_prunings.
        """
        graph = ctx.execution_graph
        report = PlanCriticReport()

        if not graph or graph.node_count() == 0:
            return report

        # 1. Detect redundant nodes (nodes calling same tool with identical action/parameters)
        seen_calls: Dict[str, str] = {}
        redundant_ids: List[str] = []

        for node_id, node in graph.nodes.items():
            call_sig = f"{node.tool_name}:{node.action}:{sorted(node.parameters.items())}"
            if call_sig in seen_calls:
                redundant_ids.append(node_id)
                self._logger.debug(f"PlanCritic identified redundant node '{node_id}' (duplicate of '{seen_calls[call_sig]}')")
            else:
                seen_calls[call_sig] = node_id

        # 2. Detect dead-end nodes (nodes that produced empty output or whose output isn't used by target edges or final synthesis)
        dead_end_ids: List[str] = []

        for node_id, node in graph.nodes.items():
            # If node output is empty/None
            output = task_outputs.get(node_id) if node_id in task_outputs else task_outputs.get(node.task_id)
            if output is not None and (output == "" or output == [] or output == {}):
                # Out-edges check
                successors = graph.get_successors(node_id)
                if not successors and node.tool_name != "python_interpreter":
                    dead_end_ids.append(node_id)
                    self._logger.debug(f"PlanCritic identified dead-end node '{node_id}' with empty output")

        suggested_prunings = sorted(set(redundant_ids + dead_end_ids))

        report = PlanCriticReport(
            redundant_node_ids=redundant_ids,
            dead_end_node_ids=dead_end_ids,
            suggested_prunings=suggested_prunings,
        )

        if report.has_issues:
            self._logger.info(
                f"PlanCritic report: {len(redundant_ids)} redundant nodes, "
                f"{len(dead_end_ids)} dead-end nodes identified for pruning"
            )
        return report
