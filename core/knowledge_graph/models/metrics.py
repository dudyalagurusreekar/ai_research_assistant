"""Metrics models — Knowledge Graph operational performance counters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class KnowledgeGraphMetrics:
    """Performance metrics container for Knowledge Graph Engine."""

    node_count: int = 0
    edge_count: int = 0
    queries_executed: int = 0
    extractions_performed: int = 0
    nodes_pruned: int = 0
    edges_pruned: int = 0
    total_query_latency_ms: float = 0.0
    sync_events: int = 0
    # Sprint 11 — Expanded observability metrics
    memory_hit_rate: float = 0.0
    memory_hits: int = 0
    memory_misses: int = 0
    knowledge_reuse_count: int = 0
    episodic_memories_stored: int = 0
    evidence_records_count: int = 0
    graph_growth_rate: float = 0.0
    user_memories_count: int = 0
    project_memories_count: int = 0
    episodes_recalled: int = 0

    @property
    def avg_query_latency_ms(self) -> float:
        if self.queries_executed == 0:
            return 0.0
        return self.total_query_latency_ms / self.queries_executed

    def update_hit_rate(self) -> None:
        """Recalculate memory hit rate from hits and misses."""
        total = self.memory_hits + self.memory_misses
        self.memory_hit_rate = (self.memory_hits / total) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "queries_executed": self.queries_executed,
            "extractions_performed": self.extractions_performed,
            "nodes_pruned": self.nodes_pruned,
            "edges_pruned": self.edges_pruned,
            "avg_query_latency_ms": self.avg_query_latency_ms,
            "sync_events": self.sync_events,
            "memory_hit_rate": round(self.memory_hit_rate, 4),
            "memory_hits": self.memory_hits,
            "memory_misses": self.memory_misses,
            "knowledge_reuse_count": self.knowledge_reuse_count,
            "episodic_memories_stored": self.episodic_memories_stored,
            "evidence_records_count": self.evidence_records_count,
            "graph_growth_rate": self.graph_growth_rate,
            "user_memories_count": self.user_memories_count,
            "project_memories_count": self.project_memories_count,
            "episodes_recalled": self.episodes_recalled,
        }
