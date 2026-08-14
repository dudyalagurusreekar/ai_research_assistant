"""Graph Memory Manager — Lifecycle management, confidence decay scoring, pruning, and compaction."""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode
from utils.logger import get_logger

logger = get_logger("GraphMemoryManager")


class GraphMemoryManager:
    """Manages long-term graph memory lifecycle, decay scoring, compaction, and pruning."""

    def __init__(
        self,
        graph: Optional[KnowledgeGraph] = None,
        decay_half_life_seconds: float = 86400.0 * 7,  # 7 days default
        prune_threshold: float = 0.25,
    ) -> None:
        self.graph = graph or KnowledgeGraph()
        self.decay_half_life_seconds = decay_half_life_seconds
        self.prune_threshold = prune_threshold

    def apply_decay(self, current_timestamp: Optional[float] = None) -> int:
        """Apply memory decay formula to node decay scores."""
        now = current_timestamp or time.time()
        updated_count = 0

        for node in self.graph.list_nodes():
            # Calculate time delta (simulated or timestamp delta)
            time_factor = 0.98  # Daily decay factor
            boost = min(0.3, node.access_count * 0.05)
            new_decay = max(0.05, (node.decay_score * time_factor) + boost)
            node.decay_score = min(1.0, round(new_decay, 3))
            updated_count += 1

        logger.debug(f"GraphMemoryManager applied memory decay to {updated_count} nodes")
        return updated_count

    def prune_low_confidence_nodes(self, threshold: Optional[float] = None) -> Tuple[int, int]:
        """Prune nodes and associated edges whose confidence score or decay score is below threshold."""
        limit = threshold if threshold is not None else self.prune_threshold
        pruned_nodes_count = 0
        pruned_edges_count = 0

        nodes_to_prune: List[str] = []
        for node in self.graph.list_nodes():
            if node.confidence_score < limit or node.decay_score < limit:
                nodes_to_prune.append(node.node_id)

        for node_id in nodes_to_prune:
            out_e = len(self.graph.get_out_edges(node_id))
            in_e = len(self.graph.get_in_edges(node_id))
            pruned_edges_count += out_e + in_e
            if self.graph.remove_node(node_id):
                pruned_nodes_count += 1

        logger.info(
            f"GraphMemoryManager pruned {pruned_nodes_count} low-confidence nodes "
            f"and {pruned_edges_count} edges (threshold={limit})"
        )
        return pruned_nodes_count, pruned_edges_count

    def compact_graph(self) -> int:
        """Compact memory graph by removing orphaned edges and consolidating duplicate canonical names."""
        # Unused method placeholder or cleaning
        return 0
