"""DependencyAnalyzer — refines data-flow edges in the execution DAG.

Performs a second pass over the DAG to ensure that every node's input_keys
are satisfied by predecessor output_keys, adding missing edges where needed
and flagging unsatisfied data requirements.
"""

from __future__ import annotations

from typing import Dict, Set

from core.planner.interfaces.base import IDependencyAnalyzer
from core.planner.models.context import PlannerContext
from core.planner.models.graph import PlanEdge
from infrastructure.logging.logger import StructuredLogger


class DependencyAnalyzer(IDependencyAnalyzer):
    """Validates and refines data-flow dependencies within the execution graph."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("DependencyAnalyzer")

    @property
    def component_name(self) -> str:
        return "DependencyAnalyzer"

    def analyze_dependencies(self, ctx: PlannerContext) -> None:
        """Inspect every node's input_keys and ensure a producer edge exists."""
        graph = ctx.execution_graph
        if not graph:
            ctx.add_error(
                stage="dependency_analysis",
                error="No execution graph available for dependency analysis.",
                recoverable=False,
            )
            return

        # Build a map of output_key -> producer node_id
        key_producers: Dict[str, str] = {}
        for node in graph.nodes.values():
            for key in node.output_keys:
                key_producers[key] = node.node_id

        # Build existing edge set for fast lookup
        existing_edges: Set[tuple[str, str]] = {
            (e.source_id, e.target_id) for e in graph.edges
        }

        added_edges = 0
        unsatisfied: list[tuple[str, str]] = []

        for node in graph.nodes.values():
            for key in node.input_keys:
                producer_id = key_producers.get(key)
                if producer_id and producer_id != node.node_id:
                    if (producer_id, node.node_id) not in existing_edges:
                        try:
                            edge = PlanEdge(
                                source_id=producer_id,
                                target_id=node.node_id,
                                data_key=key,
                                is_required=True,
                            )
                            graph.add_edge(edge)
                            existing_edges.add((producer_id, node.node_id))
                            added_edges += 1
                        except ValueError as e:
                            self._logger.warning(f"Could not add data-flow edge: {e}")
                elif not producer_id and key:
                    unsatisfied.append((node.node_id, key))

        # Update metrics
        ctx.metrics.dag_edge_count = graph.edge_count()

        if unsatisfied:
            ctx.add_trace(
                stage="dependency_analysis",
                message=f"{len(unsatisfied)} unsatisfied input keys detected",
                data={"unsatisfied": [{"node": n, "key": k} for n, k in unsatisfied[:10]]},
            )

        ctx.add_trace(
            stage="dependency_analysis",
            message=f"Dependency analysis complete: {added_edges} edges added, "
                    f"{len(unsatisfied)} unsatisfied keys",
            data={"added_edges": added_edges, "unsatisfied_count": len(unsatisfied)},
        )
        self._logger.info(
            f"Dependency analysis: {added_edges} edges added, "
            f"{len(unsatisfied)} unsatisfied"
        )
