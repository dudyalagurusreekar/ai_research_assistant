"""Query models — Graph Query Specifications, Paths, and Result Structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.node import EntityNode, EntityType


class SearchMode(Enum):
    """Retrieval search mode strategy."""

    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    GRAPH_NEIGHBOR = "graph_neighbor"
    HYBRID = "hybrid"
    PATH_FINDING = "path_finding"


@dataclass
class GraphQuery:
    """Graph Query Specification container."""

    query_text: str = ""
    entity_types: Optional[List[EntityType]] = None
    relation_types: Optional[List[RelationType]] = None
    source_entity_id: Optional[str] = None
    target_entity_id: Optional[str] = None
    max_hop_depth: int = 2
    min_confidence: float = 0.5
    limit: int = 20
    search_mode: SearchMode = SearchMode.HYBRID

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_text": self.query_text,
            "entity_types": [e.value for e in self.entity_types] if self.entity_types else None,
            "relation_types": [r.value for r in self.relation_types] if self.relation_types else None,
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "max_hop_depth": self.max_hop_depth,
            "min_confidence": self.min_confidence,
            "limit": self.limit,
            "search_mode": self.search_mode.value,
        }


@dataclass
class GraphPath:
    """Multi-hop path connecting a source node to a target node through edges."""

    nodes: List[EntityNode] = field(default_factory=list)
    edges: List[RelationEdge] = field(default_factory=list)
    path_weight: float = 1.0

    @property
    def length(self) -> int:
        return len(self.edges)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path_length": self.length,
            "path_weight": self.path_weight,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


@dataclass
class GraphQueryResult:
    """Consolidated graph query response."""

    matched_nodes: List[EntityNode] = field(default_factory=list)
    matched_edges: List[RelationEdge] = field(default_factory=list)
    paths: List[GraphPath] = field(default_factory=list)
    subgraph: Optional[Dict[str, Any]] = None
    query_latency_ms: float = 0.0
    total_nodes_found: int = 0
    reasoning_insights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched_nodes_count": len(self.matched_nodes),
            "matched_edges_count": len(self.matched_edges),
            "paths_count": len(self.paths),
            "query_latency_ms": self.query_latency_ms,
            "reasoning_insights": self.reasoning_insights,
            "matched_nodes": [n.to_dict() for n in self.matched_nodes],
            "matched_edges": [e.to_dict() for e in self.matched_edges],
            "paths": [p.to_dict() for p in self.paths],
        }
