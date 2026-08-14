"""Graph Builder — Incremental graph construction, entity resolution, and edge linking."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.knowledge_graph.models.edge import RelationEdge
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode
from utils.logger import get_logger

logger = get_logger("GraphBuilder")


class GraphBuilder:
    """Builds and merges extracted entities and relationships into KnowledgeGraph."""

    def __init__(self, graph: Optional[KnowledgeGraph] = None) -> None:
        self.graph = graph or KnowledgeGraph()

    def build_from_extraction(
        self, entities: List[EntityNode], relationships: List[RelationEdge]
    ) -> Tuple[List[EntityNode], List[RelationEdge]]:
        """Add extracted entities and edges to graph with entity resolution and deduplication."""
        added_nodes: List[EntityNode] = []
        node_id_map: Dict[str, str] = {}  # original node_id -> graph resolved node_id

        # 1. Resolve and add nodes
        for node in entities:
            resolved_node = self.graph.add_node(node)
            node_id_map[node.node_id] = resolved_node.node_id
            if resolved_node not in added_nodes:
                added_nodes.append(resolved_node)

        # 2. Update edge endpoint IDs and add edges
        added_edges: List[RelationEdge] = []
        for edge in relationships:
            resolved_source = node_id_map.get(edge.source_id, edge.source_id)
            resolved_target = node_id_map.get(edge.target_id, edge.target_id)

            if resolved_source == resolved_target:
                continue  # Skip self loops

            if self.graph.get_node(resolved_source) and self.graph.get_node(resolved_target):
                edge.source_id = resolved_source
                edge.target_id = resolved_target
                resolved_edge = self.graph.add_edge(edge)
                if resolved_edge not in added_edges:
                    added_edges.append(resolved_edge)

        logger.info(
            f"GraphBuilder built graph [{self.graph.graph_id}]: "
            f"+{len(added_nodes)} nodes, +{len(added_edges)} edges. "
            f"Total Nodes: {self.graph.node_count}, Total Edges: {self.graph.edge_count}"
        )
        return added_nodes, added_edges

    def merge_subgraph(self, other_graph: KnowledgeGraph) -> Tuple[int, int]:
        """Merge another KnowledgeGraph instance into this graph."""
        nodes = other_graph.list_nodes()
        edges = other_graph.list_edges()
        added_nodes, added_edges = self.build_from_extraction(nodes, edges)
        return len(added_nodes), len(added_edges)
