"""AdaptiveReplanningEngine — dynamically modifies execution graphs during reflection.

Prunes redundant/dead-end DAG nodes and injects target evidence-gathering or
conflict-resolution sub-tasks into the PlannerContext for execution.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from core.planner.models.context import PlannerContext, SubTask
from core.planner.models.graph import PlanNode
from core.reflection.models.reflection import ReflectionDecision
from infrastructure.logging.logger import StructuredLogger


class AdaptiveReplanningEngine:
    """Modifies execution DAGs by pruning nodes and injecting new sub-tasks."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("AdaptiveReplanningEngine")

    def apply_replan(self, ctx: PlannerContext, decision: ReflectionDecision) -> bool:
        """Apply nodes_to_remove pruning and nodes_to_add injections to PlannerContext.

        Args:
            ctx: PlannerContext detailing sub-tasks and execution graph.
            decision: ReflectionDecision containing removal node_ids and addition task specs.

        Returns:
            True if context/graph was modified, False otherwise.
        """
        graph = ctx.execution_graph
        modified = False

        # 1. Prune nodes identified by PlanCritic / ReflectionDecision
        for node_id in decision.nodes_to_remove:
            if graph and node_id in graph.nodes:
                graph.remove_node(node_id)
                ctx.sub_tasks = [t for t in ctx.sub_tasks if t.task_id != node_id]
                modified = True
                self._logger.info(f"AdaptiveReplanningEngine pruned node '{node_id}' from DAG")

        # 2. Inject new sub-tasks (e.g. conflict resolution or deep search)
        for task_spec in decision.nodes_to_add:
            tool_name = task_spec.get("tool_name", "search_tool")
            action = task_spec.get("action", "search")
            title = task_spec.get("title", "Targeted Evidence Collection")
            new_task_id = f"replan_node_{uuid.uuid4().hex[:8]}"

            new_sub_task = SubTask(
                task_id=new_task_id,
                title=title,
                description=task_spec.get("description", "Gather additional evidence to resolve reflection issue"),
                tool_name=tool_name,
                action=action,
                parameters=task_spec.get("parameters", {}),
            )
            ctx.sub_tasks.append(new_sub_task)

            if graph:
                graph.add_node(PlanNode(
                    node_id=new_task_id,
                    task_id=new_task_id,
                    title=title,
                    tool_name=tool_name,
                    action=action,
                    parameters=task_spec.get("parameters", {}),
                ))

            modified = True
            self._logger.info(f"AdaptiveReplanningEngine injected sub-task '{title}' (id={new_task_id}) into DAG")

        if modified:
            ctx.add_trace(
                stage="adaptive_replanning",
                message=f"Applied replan: {len(decision.nodes_to_remove)} nodes pruned, "
                        f"{len(decision.nodes_to_add)} tasks injected",
                data=decision.to_dict(),
            )

        return modified
