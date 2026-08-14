"""Graph Reasoning Engine — Multi-hop path finding, transitive relation inference, centrality, and contradiction detection."""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode
from core.knowledge_graph.models.query import GraphPath
from utils.logger import get_logger

logger = get_logger("GraphReasoningEngine")


class GraphReasoningEngine:
    """Production Graph Reasoning Engine executing pathfinding, transitive inference, PageRank, and contradiction detection."""

    def __init__(self, graph: Optional[KnowledgeGraph] = None) -> None:
        self.graph = graph or KnowledgeGraph()

    def find_paths(
        self, source_node_id: str, target_node_id: str, max_depth: int = 4, limit: int = 5
    ) -> List[GraphPath]:
        """Find multi-hop paths between source_node_id and target_node_id via BFS pathfinding."""
        paths: List[GraphPath] = []
        source_node = self.graph.get_node(source_node_id)
        target_node = self.graph.get_node(target_node_id)

        if not source_node or not target_node:
            return paths

        queue = deque([([source_node], [], 0.0)])
        visited: Set[str] = {source_node_id}

        while queue and len(paths) < limit:
            node_path, edge_path, weight_accum = queue.popleft()
            curr_node = node_path[-1]

            if curr_node.node_id == target_node_id and len(edge_path) > 0:
                paths.append(GraphPath(nodes=node_path, edges=edge_path, path_weight=round(weight_accum, 2)))
                continue

            if len(edge_path) >= max_depth:
                continue

            out_edges = self.graph.get_out_edges(curr_node.node_id)
            for edge in out_edges:
                next_node_id = edge.target_id
                next_node = self.graph.get_node(next_node_id)

                if next_node and (next_node_id not in visited or next_node_id == target_node_id):
                    if next_node_id != target_node_id:
                        visited.add(next_node_id)
                    queue.append((node_path + [next_node], edge_path + [edge], weight_accum + edge.weight))

        logger.debug(f"GraphReasoningEngine found {len(paths)} path(s) between {source_node_id} and {target_node_id}")
        return paths

    def infer_transitive_relations(self) -> List[RelationEdge]:
        """Infer transitive relationships (e.g. A IMPLEMENTS B and B USES C => A USES C)."""
        inferred_edges: List[RelationEdge] = []
        nodes = self.graph.list_nodes()

        for node_a in nodes:
            out_a = self.graph.get_out_edges(node_a.node_id)
            for edge_ab in out_a:
                node_b_id = edge_ab.target_id
                out_b = self.graph.get_out_edges(node_b_id)

                for edge_bc in out_b:
                    node_c_id = edge_bc.target_id
                    if node_c_id == node_a.node_id:
                        continue

                    # Transitive rule: IMPLEMENTS + USES => USES
                    if edge_ab.relation_type == RelationType.IMPLEMENTS and edge_bc.relation_type == RelationType.USES:
                        inferred_edge = RelationEdge(
                            source_id=node_a.node_id,
                            target_id=node_c_id,
                            relation_type=RelationType.USES,
                            confidence_score=edge_ab.confidence_score * edge_bc.confidence_score * 0.9,
                            properties={"inferred": True, "via_node": node_b_id},
                        )
                        inferred_edges.append(inferred_edge)

        logger.info(f"GraphReasoningEngine inferred {len(inferred_edges)} transitive relationships")
        return inferred_edges

    def compute_node_centrality(self, damping_factor: float = 0.85, max_iterations: int = 20) -> Dict[str, float]:
        """Compute PageRank centrality scores for all nodes in graph using NetworkX (or fallback)."""
        return self.graph.compute_centrality(metric="pagerank")


    def detect_contradictions(self) -> List[Tuple[EntityNode, EntityNode, RelationEdge]]:
        """Find contradictory relation edges in the graph."""
        contradictions: List[Tuple[EntityNode, EntityNode, RelationEdge]] = []
        contradict_edges = self.graph.list_edges(relation_type=RelationType.CONTRADICTS)

        for edge in contradict_edges:
            n1 = self.graph.get_node(edge.source_id)
            n2 = self.graph.get_node(edge.target_id)
            if n1 and n2:
                contradictions.append((n1, n2, edge))

        return contradictions
