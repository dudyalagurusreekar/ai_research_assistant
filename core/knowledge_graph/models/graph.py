"""Knowledge Graph container — Property Graph structure and Subgraph representations."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.node import EntityNode, EntityType
from utils.logger import get_logger

logger = get_logger("KnowledgeGraph")


class KnowledgeGraph:
    """In-memory property graph with fast indexing, adjacency lists, and thread safety."""

    def __init__(self, graph_id: str = "global_knowledge_graph") -> None:
        self.graph_id = graph_id
        self._nodes: Dict[str, EntityNode] = {}  # node_id -> EntityNode
        self._edges: Dict[str, RelationEdge] = {}  # edge_id -> RelationEdge
        self._canonical_map: Dict[str, str] = {}  # canonical_name -> node_id
        self._type_index: Dict[EntityType, Set[str]] = {t: set() for t in EntityType}
        self._outgoing_edges: Dict[str, Set[str]] = {}  # node_id -> set of edge_ids
        self._incoming_edges: Dict[str, Set[str]] = {}  # node_id -> set of edge_ids
        self.version: int = 1
        self._lock = threading.RLock()


    def add_node(self, node: EntityNode) -> EntityNode:
        """Add or update an EntityNode in the graph."""
        with self._lock:
            existing_id = self._canonical_map.get(node.canonical_name)
            if existing_id and existing_id in self._nodes:
                # Merge into existing node
                existing = self._nodes[existing_id]
                existing.access_count += 1
                for alias in node.aliases:
                    if alias.lower() not in [a.lower() for a in existing.aliases]:
                        existing.aliases.append(alias)
                existing.properties.update(node.properties)
                for tag in node.tags:
                    if tag not in existing.tags:
                        existing.tags.append(tag)
                existing.confidence_score = max(existing.confidence_score, node.confidence_score)
                return existing

            self._nodes[node.node_id] = node
            self._canonical_map[node.canonical_name] = node.node_id
            for alias in node.aliases:
                self._canonical_map[alias.lower().strip()] = node.node_id

            if node.entity_type not in self._type_index:
                self._type_index[node.entity_type] = set()
            self._type_index[node.entity_type].add(node.node_id)

            if node.node_id not in self._outgoing_edges:
                self._outgoing_edges[node.node_id] = set()
            if node.node_id not in self._incoming_edges:
                self._incoming_edges[node.node_id] = set()

            logger.debug(f"KnowledgeGraph [{self.graph_id}] Added node '{node.name}' ({node.node_id})")
            return node

    def add_edge(self, edge: RelationEdge) -> RelationEdge:
        """Add a RelationEdge connecting source and target nodes."""
        with self._lock:
            if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
                raise ValueError(f"Cannot add edge: source ({edge.source_id}) or target ({edge.target_id}) node missing")

            # Deduplicate existing edge between same source and target with same relation_type
            for existing_edge_id in self._outgoing_edges.get(edge.source_id, set()):
                existing_edge = self._edges.get(existing_edge_id)
                if existing_edge and existing_edge.target_id == edge.target_id and existing_edge.relation_type == edge.relation_type:
                    existing_edge.weight = max(existing_edge.weight, edge.weight)
                    existing_edge.confidence_score = max(existing_edge.confidence_score, edge.confidence_score)
                    existing_edge.properties.update(edge.properties)
                    return existing_edge

            self._edges[edge.edge_id] = edge
            self._outgoing_edges[edge.source_id].add(edge.edge_id)
            self._incoming_edges[edge.target_id].add(edge.edge_id)

            if not edge.is_directional:
                # Add reciprocal edge tracking in adjacency lists
                self._outgoing_edges[edge.target_id].add(edge.edge_id)
                self._incoming_edges[edge.source_id].add(edge.edge_id)

            logger.debug(f"KnowledgeGraph [{self.graph_id}] Added edge {edge.source_id} -[{edge.relation_type.value}]-> {edge.target_id}")
            return edge

    def get_node(self, node_id: str) -> Optional[EntityNode]:
        """Get node by node_id."""
        with self._lock:
            return self._nodes.get(node_id)

    def find_node_by_name(self, name: str) -> Optional[EntityNode]:
        """Find node by exact or alias name match."""
        with self._lock:
            clean_name = name.lower().strip()
            node_id = self._canonical_map.get(clean_name)
            if node_id:
                return self._nodes.get(node_id)
            for node in self._nodes.values():
                if node.matches_name(name):
                    return node
            return None

    def get_edge(self, edge_id: str) -> Optional[RelationEdge]:
        """Get edge by edge_id."""
        with self._lock:
            return self._edges.get(edge_id)

    def get_out_edges(self, node_id: str) -> List[RelationEdge]:
        """Get outgoing edges from node_id."""
        with self._lock:
            edge_ids = self._outgoing_edges.get(node_id, set())
            return [self._edges[e_id] for e_id in edge_ids if e_id in self._edges]

    def get_in_edges(self, node_id: str) -> List[RelationEdge]:
        """Get incoming edges to node_id."""
        with self._lock:
            edge_ids = self._incoming_edges.get(node_id, set())
            return [self._edges[e_id] for e_id in edge_ids if e_id in self._edges]

    def get_neighbors(self, node_id: str, relation_type: Optional[RelationType] = None) -> List[EntityNode]:
        """Get neighboring nodes connected to node_id."""
        with self._lock:
            neighbors = []
            out_edges = self.get_out_edges(node_id)
            for edge in out_edges:
                if relation_type and edge.relation_type != relation_type:
                    continue
                other_id = edge.target_id if edge.source_id == node_id else edge.source_id
                target_node = self.get_node(other_id)
                if target_node and target_node not in neighbors:
                    neighbors.append(target_node)
            return neighbors

    def list_nodes(self, entity_type: Optional[EntityType] = None) -> List[EntityNode]:
        """List graph nodes, optionally filtered by EntityType."""
        with self._lock:
            if entity_type:
                node_ids = self._type_index.get(entity_type, set())
                return [self._nodes[n_id] for n_id in node_ids if n_id in self._nodes]
            return list(self._nodes.values())

    def list_edges(self, relation_type: Optional[RelationType] = None) -> List[RelationEdge]:
        """List graph edges, optionally filtered by RelationType."""
        with self._lock:
            if relation_type:
                return [e for e in self._edges.values() if e.relation_type == relation_type]
            return list(self._edges.values())

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all connected edges from the graph."""
        with self._lock:
            if node_id not in self._nodes:
                return False
            node = self._nodes[node_id]

            # Remove associated edges
            connected_edges = self.get_out_edges(node_id) + self.get_in_edges(node_id)
            for edge in connected_edges:
                self.remove_edge(edge.edge_id)

            del self._nodes[node_id]
            if node.canonical_name in self._canonical_map:
                del self._canonical_map[node.canonical_name]
            if node.entity_type in self._type_index:
                self._type_index[node.entity_type].discard(node_id)

            return True

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge by edge_id."""
        with self._lock:
            if edge_id in self._edges:
                edge = self._edges[edge_id]
                if edge.source_id in self._outgoing_edges:
                    self._outgoing_edges[edge.source_id].discard(edge_id)
                if edge.target_id in self._incoming_edges:
                    self._incoming_edges[edge.target_id].discard(edge_id)
                del self._edges[edge_id]
                return True
            return False

    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._canonical_map.clear()
            self._type_index = {t: set() for t in EntityType}
            self._outgoing_edges.clear()
            self._incoming_edges.clear()
            logger.debug(f"KnowledgeGraph [{self.graph_id}] cleared.")

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    def to_networkx(self) -> Any:
        """Export internal KnowledgeGraph to a NetworkX DiGraph."""
        try:
            import networkx as nx
        except ImportError:
            logger.warning("networkx module is not installed; returning None")
            return None

        with self._lock:
            nx_graph = nx.DiGraph(graph_id=self.graph_id, version=self.version)
            for node_id, node in self._nodes.items():
                nx_graph.add_node(
                    node_id,
                    name=node.name,
                    canonical_name=node.canonical_name,
                    entity_type=node.entity_type.value if hasattr(node.entity_type, "value") else str(node.entity_type),
                    confidence=node.confidence_score,
                    importance=getattr(node, "importance_score", getattr(node, "decay_score", 1.0)),
                )
            for edge_id, edge in self._edges.items():
                nx_graph.add_edge(
                    edge.source_id,
                    edge.target_id,
                    edge_id=edge_id,
                    relation_type=edge.relation_type.value if hasattr(edge.relation_type, "value") else str(edge.relation_type),
                    weight=edge.weight,
                    confidence=edge.confidence_score,
                )
            return nx_graph


    def compute_centrality(self, metric: str = "degree") -> Dict[str, float]:
        """Compute node centrality scores using NetworkX algorithms (or degree fallback)."""
        nx_g = self.to_networkx()
        if nx_g is None:
            # Simple in-memory degree centrality fallback
            with self._lock:
                total = max(1, len(self._nodes) - 1)
                return {
                    n_id: (len(self._outgoing_edges.get(n_id, set())) + len(self._incoming_edges.get(n_id, set()))) / total
                    for n_id in self._nodes
                }

        import networkx as nx
        try:
            if metric == "pagerank":
                return nx.pagerank(nx_g, weight="weight")
            elif metric == "betweenness":
                return nx.betweenness_centrality(nx_g)
            else:
                return nx.degree_centrality(nx_g)
        except Exception as err:
            logger.warning(f"Error computing NetworkX centrality '{metric}': {err}")
            return {n: 0.0 for n in nx_g.nodes()}

    def extract_subgraph(self, node_ids: List[str]) -> Dict[str, Any]:
        """Extract a subgraph containing specified node IDs and connecting edges."""
        with self._lock:
            target_set = set(node_ids)
            sub_nodes = [self._nodes[n_id].to_dict() for n_id in target_set if n_id in self._nodes]
            sub_edges = [
                e.to_dict()
                for e in self._edges.values()
                if e.source_id in target_set and e.target_id in target_set
            ]
            return {
                "nodes": sub_nodes,
                "edges": sub_edges,
                "node_count": len(sub_nodes),
                "edge_count": len(sub_edges),
            }

