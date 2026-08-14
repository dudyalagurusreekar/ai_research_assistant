"""ParallelPlanner — identifies concurrent execution opportunities.

Delegates to ExecutionGraph.compute_parallel_levels() and records the
resulting execution wave groupings in the PlannerContext.
"""

from __future__ import annotations

from typing import List

from core.planner.interfaces.base import IParallelPlanner
from core.planner.models.context import PlannerContext
from infrastructure.logging.logger import StructuredLogger


class ParallelPlanner(IParallelPlanner):
    """Computes parallel execution levels from the DAG structure."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ParallelPlanner")

    @property
    def component_name(self) -> str:
        return "ParallelPlanner"

    def plan_parallelism(self, ctx: PlannerContext) -> List[List[str]]:
        """Compute and attach parallel execution groups to the context."""
        graph = ctx.execution_graph
        if not graph or graph.node_count() == 0:
            ctx.add_trace(
                stage="parallel_planning",
                message="No graph available or graph is empty; no parallelism to plan.",
            )
            return []

        levels = graph.compute_parallel_levels()
        ctx.parallel_groups = levels
        ctx.metrics.parallel_groups = len(levels)

        # Build a human-readable summary
        level_summary = []
        for i, group in enumerate(levels):
            titles = [graph.nodes[nid].title for nid in group if nid in graph.nodes]
            level_summary.append({"level": i, "nodes": len(group), "titles": titles})

        ctx.add_trace(
            stage="parallel_planning",
            message=f"Identified {len(levels)} execution waves",
            data={"levels": level_summary},
        )
        self._logger.info(
            f"Parallel planning: {len(levels)} waves, "
            f"max concurrency={max(len(g) for g in levels) if levels else 0}"
        )
        return levels
