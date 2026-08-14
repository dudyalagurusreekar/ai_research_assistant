"""Execution graph models — DAG representation for planning.

Provides PlanNode, PlanEdge, and ExecutionGraph with topological sorting,
cycle detection, dependency tracking, and parallel-level computation.
"""

from __future__ import annotations

import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class NodeStatus(Enum):
    """Lifecycle status of a plan node."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanNode:
    """A single node in the execution DAG representing one atomic unit of work."""

    node_id: str = field(default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    title: str = ""
    tool_name: str = ""
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING
    input_keys: List[str] = field(default_factory=list)
    output_keys: List[str] = field(default_factory=list)
    estimated_latency_seconds: float = 1.0
    parallel_level: int = 0  # 0 = first wave, 1 = second wave, etc.
    is_optional: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize node for logging."""
        return {
            "node_id": self.node_id,
            "task_id": self.task_id,
            "title": self.title,
            "tool_name": self.tool_name,
            "action": self.action,
            "status": self.status.value,
            "parallel_level": self.parallel_level,
            "is_optional": self.is_optional,
        }


@dataclass
class PlanEdge:
    """A directed edge in the execution DAG indicating a dependency."""

    source_id: str = ""
    target_id: str = ""
    data_key: str = ""  # data key flowing along this edge
    is_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize edge for logging."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "data_key": self.data_key,
            "is_required": self.is_required,
        }


@dataclass
class ExecutionGraph:
    """Directed acyclic graph (DAG) of plan nodes with dependency edges.

    Supports topological sorting, cycle detection, root/leaf queries, and
    parallel-level computation for concurrent execution scheduling.
    """

    graph_id: str = field(default_factory=lambda: f"graph_{uuid.uuid4().hex[:8]}")
    nodes: Dict[str, PlanNode] = field(default_factory=dict)
    edges: List[PlanEdge] = field(default_factory=list)

    # Cached adjacency structures (rebuilt on mutation)
    _adjacency: Dict[str, List[str]] = field(default_factory=dict, repr=False)
    _reverse_adjacency: Dict[str, List[str]] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_node(self, node: PlanNode) -> None:
        """Add a node to the graph and rebuild adjacency caches."""
        self.nodes[node.node_id] = node
        self._rebuild_adjacency()

    def add_edge(self, edge: PlanEdge) -> None:
        """Add a directed edge and rebuild adjacency caches.

        Raises:
            ValueError: If source or target node does not exist or edge would create a cycle.
        """
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node '{edge.source_id}' not in graph.")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node '{edge.target_id}' not in graph.")
        self.edges.append(edge)
        self._rebuild_adjacency()
        if self.has_cycle():
            self.edges.pop()
            self._rebuild_adjacency()
            raise ValueError(
                f"Adding edge {edge.source_id} -> {edge.target_id} would create a cycle."
            )

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all connected edges."""
        self.nodes.pop(node_id, None)
        self.edges = [e for e in self.edges if e.source_id != node_id and e.target_id != node_id]
        self._rebuild_adjacency()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_roots(self) -> List[PlanNode]:
        """Return nodes with no incoming edges (entry points)."""
        targets: Set[str] = {e.target_id for e in self.edges}
        return [n for n in self.nodes.values() if n.node_id not in targets]

    def get_leaves(self) -> List[PlanNode]:
        """Return nodes with no outgoing edges (terminal nodes)."""
        sources: Set[str] = {e.source_id for e in self.edges}
        return [n for n in self.nodes.values() if n.node_id not in sources]

    def get_predecessors(self, node_id: str) -> List[PlanNode]:
        """Return direct predecessor nodes."""
        return [self.nodes[nid] for nid in self._reverse_adjacency.get(node_id, []) if nid in self.nodes]

    def get_successors(self, node_id: str) -> List[PlanNode]:
        """Return direct successor nodes."""
        return [self.nodes[nid] for nid in self._adjacency.get(node_id, []) if nid in self.nodes]

    def node_count(self) -> int:
        """Return the number of nodes."""
        return len(self.nodes)

    def edge_count(self) -> int:
        """Return the number of edges."""
        return len(self.edges)

    # ------------------------------------------------------------------
    # Topological Sort (Kahn's algorithm)
    # ------------------------------------------------------------------

    def topological_sort(self) -> List[PlanNode]:
        """Return nodes in topological order using Kahn's algorithm.

        Raises:
            ValueError: If the graph contains a cycle.
        """
        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        for edge in self.edges:
            in_degree[edge.target_id] = in_degree.get(edge.target_id, 0) + 1

        queue: deque[str] = deque(nid for nid, deg in in_degree.items() if deg == 0)
        sorted_nodes: List[PlanNode] = []

        while queue:
            nid = queue.popleft()
            sorted_nodes.append(self.nodes[nid])
            for successor_id in self._adjacency.get(nid, []):
                in_degree[successor_id] -= 1
                if in_degree[successor_id] == 0:
                    queue.append(successor_id)

        if len(sorted_nodes) != len(self.nodes):
            raise ValueError("Graph contains a cycle; topological sort is impossible.")

        return sorted_nodes

    # ------------------------------------------------------------------
    # Cycle Detection (DFS-based)
    # ------------------------------------------------------------------

    def has_cycle(self) -> bool:
        """Return True if the graph contains a directed cycle."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {nid: WHITE for nid in self.nodes}

        def _dfs(nid: str) -> bool:
            color[nid] = GRAY
            for successor_id in self._adjacency.get(nid, []):
                if color[successor_id] == GRAY:
                    return True
                if color[successor_id] == WHITE and _dfs(successor_id):
                    return True
            color[nid] = BLACK
            return False

        return any(_dfs(nid) for nid, c in color.items() if c == WHITE)

    # ------------------------------------------------------------------
    # Parallel-Level Computation
    # ------------------------------------------------------------------

    def compute_parallel_levels(self) -> List[List[str]]:
        """Assign each node a parallel level (execution wave) and return grouped node IDs.

        Level 0 = root nodes (no dependencies).
        Level N = nodes whose predecessors are all in levels < N.

        Returns:
            List of lists, where each inner list contains node IDs that can run concurrently.
        """
        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        for edge in self.edges:
            in_degree[edge.target_id] = in_degree.get(edge.target_id, 0) + 1

        current_level: List[str] = [nid for nid, deg in in_degree.items() if deg == 0]
        levels: List[List[str]] = []
        level_idx = 0

        while current_level:
            for nid in current_level:
                self.nodes[nid].parallel_level = level_idx
            levels.append(list(current_level))

            next_level: List[str] = []
            for nid in current_level:
                for successor_id in self._adjacency.get(nid, []):
                    in_degree[successor_id] -= 1
                    if in_degree[successor_id] == 0:
                        next_level.append(successor_id)

            current_level = next_level
            level_idx += 1

        return levels

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire graph for persistence or logging."""
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _rebuild_adjacency(self) -> None:
        """Rebuild forward and reverse adjacency lists from the edge list."""
        self._adjacency = {nid: [] for nid in self.nodes}
        self._reverse_adjacency = {nid: [] for nid in self.nodes}
        for edge in self.edges:
            if edge.source_id in self._adjacency:
                self._adjacency[edge.source_id].append(edge.target_id)
            if edge.target_id in self._reverse_adjacency:
                self._reverse_adjacency[edge.target_id].append(edge.source_id)
