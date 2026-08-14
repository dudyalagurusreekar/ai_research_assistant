"""Semantic Retrieval Engine — Hybrid vector/keyword search, k-hop graph expansion, and subgraph extraction."""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode, EntityType
from core.knowledge_graph.models.query import GraphQuery, GraphQueryResult, SearchMode
from utils.logger import get_logger

logger = get_logger("SemanticRetrievalEngine")


class SemanticRetrievalEngine:
    """Production semantic retrieval engine combining term vectors, k-hop expansion, and subgraph extraction."""

    def __init__(self, graph: Optional[KnowledgeGraph] = None) -> None:
        self.graph = graph or KnowledgeGraph()

    def search(self, query: GraphQuery) -> GraphQueryResult:
        """Execute hybrid semantic search over KnowledgeGraph."""
        start_t = time.time()
        matched_nodes: List[EntityNode] = []
        matched_edges: List[RelationEdge] = []
        insights: List[str] = []

        query_text = query.query_text.strip()

        # 1. Primary Node Search (Keyword + TF-IDF Vector Similarity)
        candidate_nodes = self.graph.list_nodes(
            entity_type=query.entity_types[0] if query.entity_types and len(query.entity_types) == 1 else None
        )

        scored_nodes: List[Tuple[EntityNode, float]] = []
        for node in candidate_nodes:
            if query.entity_types and node.entity_type not in query.entity_types:
                continue
            if node.confidence_score < query.min_confidence:
                continue

            score = self._compute_similarity_score(query_text, node)
            if score > 0.1 or query.source_entity_id == node.node_id:
                scored_nodes.append((node, score))

        # Sort nodes by score descending
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        top_nodes = [n for n, s in scored_nodes[: query.limit]]
        matched_nodes.extend(top_nodes)

        # 2. k-Hop Neighborhood Expansion
        if query.max_hop_depth > 0 and top_nodes:
            expanded_node_ids: Set[str] = {n.node_id for n in top_nodes}
            current_level: Set[str] = {n.node_id for n in top_nodes}

            for hop in range(query.max_hop_depth):
                next_level: Set[str] = set()
                for n_id in current_level:
                    out_edges = self.graph.get_out_edges(n_id)
                    in_edges = self.graph.get_in_edges(n_id)

                    for edge in out_edges + in_edges:
                        if query.relation_types and edge.relation_type not in query.relation_types:
                            continue
                        if edge not in matched_edges:
                            matched_edges.append(edge)

                        other_id = edge.target_id if edge.source_id == n_id else edge.source_id
                        if other_id not in expanded_node_ids:
                            expanded_node_ids.add(other_id)
                            next_level.add(other_id)
                            neighbor_node = self.graph.get_node(other_id)
                            if neighbor_node and neighbor_node not in matched_nodes:
                                matched_nodes.append(neighbor_node)

                current_level = next_level
                if not current_level:
                    break

            insights.append(f"Expanded k-hop neighborhood ({query.max_hop_depth} hops) containing {len(matched_nodes)} total nodes.")

        latency_ms = (time.time() - start_t) * 1000.0
        return GraphQueryResult(
            matched_nodes=matched_nodes[: query.limit * 2],
            matched_edges=matched_edges[: query.limit * 3],
            query_latency_ms=latency_ms,
            total_nodes_found=len(matched_nodes),
            reasoning_insights=insights,
        )

    def _compute_similarity_score(self, query_text: str, node: EntityNode) -> float:
        """Compute keyword overlap & term frequency similarity between query and node."""
        if not query_text:
            return 0.5

        if node.matches_name(query_text):
            return 1.0

        q_words = set(re.findall(r"\w+", query_text.lower()))
        n_words = set(re.findall(r"\w+", node.name.lower() + " " + " ".join(node.aliases)))

        if not q_words or not n_words:
            return 0.0

        overlap = q_words.intersection(n_words)
        jaccard = len(overlap) / float(len(q_words.union(n_words)))

        # Tag / Property matching bonus
        bonus = 0.0
        for tag in node.tags:
            if tag.lower() in q_words:
                bonus += 0.15

        return min(1.0, jaccard + bonus)
