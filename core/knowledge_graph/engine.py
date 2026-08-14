"""Knowledge Graph Engine Facade — Main entry point for knowledge extraction, reasoning, semantic memory, and long-term memory."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

from core.knowledge_graph.components.entity_extractor import EntityExtractor
from core.knowledge_graph.components.episodic_memory import EpisodicMemoryEngine, Episode
from core.knowledge_graph.components.graph_builder import GraphBuilder
from core.knowledge_graph.components.graph_memory import GraphMemoryManager
from core.knowledge_graph.components.graph_reasoning import GraphReasoningEngine
from core.knowledge_graph.components.graph_storage import GraphStorage
from core.knowledge_graph.components.knowledge_synchronizer import KnowledgeSynchronizer
from core.knowledge_graph.components.long_term_memory import LongTermMemoryStore, MemoryEntry, MemoryScope
from core.knowledge_graph.components.memory_policies import MemoryPolicyEngine
from core.knowledge_graph.components.query_service import GraphQueryService
from core.knowledge_graph.components.relationship_extractor import RelationshipExtractor
from core.knowledge_graph.components.semantic_retrieval import SemanticRetrievalEngine
from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.metrics import KnowledgeGraphMetrics
from core.knowledge_graph.models.node import EntityNode, EntityType
from core.knowledge_graph.models.query import (
    GraphPath,
    GraphQuery,
    GraphQueryResult,
    SearchMode,
)
from utils.logger import get_logger

logger = get_logger("KnowledgeGraphEngine")


class KnowledgeGraphEngine:
    """Main facade orchestrating Knowledge Graph extraction, storage, semantic retrieval, reasoning, memory, and policies."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.graph = KnowledgeGraph()
        self.entity_extractor = EntityExtractor()
        self.relationship_extractor = RelationshipExtractor()
        self.builder = GraphBuilder(self.graph)
        self.storage = GraphStorage(self.graph, storage_dir=storage_dir)
        self.retrieval_engine = SemanticRetrievalEngine(self.graph)
        self.reasoning_engine = GraphReasoningEngine(self.graph)
        self.memory_manager = GraphMemoryManager(self.graph)
        self.synchronizer = KnowledgeSynchronizer(self.graph)
        self.query_service = GraphQueryService(self.graph, self.retrieval_engine, self.reasoning_engine)
        self.metrics = KnowledgeGraphMetrics()
        # Sprint 11 — New memory components
        self.episodic_memory = EpisodicMemoryEngine()
        self.long_term_memory = LongTermMemoryStore()
        self.memory_policy = MemoryPolicyEngine()

    def ingest_text(self, text: str, source_id: str = "text_source") -> Tuple[List[EntityNode], List[RelationEdge]]:
        """Extract entities and relationships from text and build into graph."""
        nodes = self.entity_extractor.extract_from_text(text, source_id=source_id)
        edges = self.relationship_extractor.extract_relationships(text, nodes, source_id=source_id)

        added_nodes, added_edges = self.builder.build_from_extraction(nodes, edges)

        # Attach evidence to edges
        for edge in added_edges:
            edge.add_evidence(
                source_id=source_id,
                source_type="document",
                confidence=edge.confidence_score,
                snippet=text[:200],
            )

        self.metrics.extractions_performed += 1
        self.metrics.node_count = self.graph.node_count
        self.metrics.edge_count = self.graph.edge_count
        self.metrics.evidence_records_count += len(added_edges)

        logger.info(f"Ingested text from '{source_id}': +{len(added_nodes)} nodes, +{len(added_edges)} edges")
        return added_nodes, added_edges

    def ingest_structured_data(self, data: Dict[str, Any], source_id: str = "data_source") -> List[EntityNode]:
        """Extract entity nodes from structured dictionary and add to graph."""
        nodes = self.entity_extractor.extract_from_structured_data(data, source_id=source_id)
        added_nodes, _ = self.builder.build_from_extraction(nodes, [])

        self.metrics.node_count = self.graph.node_count
        return added_nodes

    def query(self, query: Union[str, GraphQuery]) -> GraphQueryResult:
        """Execute semantic graph query."""
        if isinstance(query, str):
            res = self.query_service.query_natural_language(query)
        else:
            res = self.query_service.execute_query(query)

        self.metrics.queries_executed += 1
        self.metrics.total_query_latency_ms += res.query_latency_ms

        # Track memory hits/misses
        if res.matched_nodes:
            self.metrics.memory_hits += 1
            self.metrics.knowledge_reuse_count += len(res.matched_nodes)
        else:
            self.metrics.memory_misses += 1
        self.metrics.update_hit_rate()

        return res

    def find_path(self, source_name: str, target_name: str, max_depth: int = 4) -> List[GraphPath]:
        """Find multi-hop semantic paths between source and target node names."""
        n1 = self.graph.find_node_by_name(source_name)
        n2 = self.graph.find_node_by_name(target_name)

        if not n1 or not n2:
            return []

        return self.reasoning_engine.find_paths(n1.node_id, n2.node_id, max_depth=max_depth)

    def prune_and_compact(self, min_confidence: float = 0.25) -> Tuple[int, int]:
        """Prune low-confidence nodes and compact memory graph."""
        pn, pe = self.memory_manager.prune_low_confidence_nodes(threshold=min_confidence)
        self.metrics.nodes_pruned += pn
        self.metrics.edges_pruned += pe
        self.metrics.node_count = self.graph.node_count
        self.metrics.edge_count = self.graph.edge_count
        return pn, pe

    # --- Sprint 11: Episodic Memory ---

    def record_episode(self, query: str, plan_steps: Optional[List[str]] = None,
                       tools_used: Optional[List[str]] = None, sources: Optional[List[str]] = None,
                       outcome: str = "", success: bool = True, confidence: float = 1.0,
                       user_id: str = "", project_id: str = "", duration_ms: float = 0.0) -> Episode:
        """Record an execution episode into episodic memory."""
        episode = self.episodic_memory.record_episode(
            query=query, plan_steps=plan_steps, tools_used=tools_used,
            sources_consulted=sources, outcome=outcome, success=success,
            confidence_score=confidence, user_id=user_id, project_id=project_id,
            duration_ms=duration_ms,
        )
        self.metrics.episodic_memories_stored = self.episodic_memory.episode_count
        return episode

    def recall_episodes(self, query: str, limit: int = 5) -> List[Episode]:
        """Recall similar past episodes."""
        results = self.episodic_memory.recall_similar_episodes(query, limit=limit)
        self.metrics.episodes_recalled += len(results)
        return results

    # --- Sprint 11: Long-Term Memory ---

    def store_memory(self, scope: str, owner_id: str, key: str, value: str,
                     importance: float = 0.5, ttl_days: Optional[int] = None) -> MemoryEntry:
        """Store a memory entry (user or project scoped)."""
        if scope == "project":
            entry = self.long_term_memory.store_project_memory(owner_id, key, value, importance, ttl_days=ttl_days)
        else:
            entry = self.long_term_memory.store_user_memory(owner_id, key, value, importance, ttl_days=ttl_days)

        self.metrics.user_memories_count = self.long_term_memory.user_memory_count()
        self.metrics.project_memories_count = self.long_term_memory.project_memory_count()
        return entry

    def recall_memory(self, scope: str, owner_id: str, key_or_query: Optional[str] = None) -> List[MemoryEntry]:
        """Recall memories from long-term store."""
        if scope == "project":
            return self.long_term_memory.recall_project_memory(owner_id, key_or_query)
        return self.long_term_memory.recall_user_memory(owner_id, key_or_query)

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory entry."""
        return self.long_term_memory.delete_memory(memory_id)

    # --- Sprint 11: Policy Enforcement ---

    def enforce_policies(self) -> Dict[str, int]:
        """Run all memory policy enforcement."""
        expired = self.memory_policy.enforce_expiration(self.long_term_memory)
        scored = self.memory_policy.compute_importance_scores(self.long_term_memory)
        pruned = self.memory_policy.prune_low_importance(self.long_term_memory)

        self.metrics.user_memories_count = self.long_term_memory.user_memory_count()
        self.metrics.project_memories_count = self.long_term_memory.project_memory_count()

        return {"expired": expired, "scored": scored, "pruned": pruned}

    # --- Sprint 11: Graph Summary ---

    def get_graph_summary(self) -> Dict[str, Any]:
        """Return enriched graph summary with all metrics."""
        self.metrics.node_count = self.graph.node_count
        self.metrics.edge_count = self.graph.edge_count
        self.metrics.episodic_memories_stored = self.episodic_memory.episode_count
        self.metrics.user_memories_count = self.long_term_memory.user_memory_count()
        self.metrics.project_memories_count = self.long_term_memory.project_memory_count()
        self.metrics.update_hit_rate()

        return {
            "graph_id": self.graph.graph_id,
            "metrics": self.metrics.to_dict(),
            "entity_type_distribution": {
                t.value: len(self.graph._type_index.get(t, set())) for t in EntityType
            },
            "policy_summary": self.memory_policy.get_policy_summary(),
        }

    # --- Sprint 11: Graph Snapshots & Versioning ---

    def create_snapshot(self, tag: str = "auto", metadata: Optional[Dict[str, Any]] = None) -> Any:
        """Create and save a versioned graph snapshot."""
        return self.storage.save_snapshot(tag=tag, metadata=metadata)

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all saved graph snapshots."""
        return self.storage.list_snapshots()

    def load_snapshot(self, snapshot_id: str) -> bool:
        """Load a graph snapshot by ID."""
        success = self.storage.load_snapshot(snapshot_id)
        if success:
            self.metrics.node_count = self.graph.node_count
            self.metrics.edge_count = self.graph.edge_count
        return success

    def compare_snapshots(self, from_snapshot_id: str, to_snapshot_id: str) -> Any:
        """Compare two graph snapshots and compute diff."""
        return self.storage.compare_snapshots(from_snapshot_id, to_snapshot_id)

    # --- Sprint 11: Privacy & Hard Purge ---

    def purge_user_privacy_data(self, user_id: str) -> Dict[str, int]:
        """Hard purge all memory records and episodic history for a user."""
        mem_count = self.long_term_memory.purge_user_data(user_id)
        ep_count = self.episodic_memory.purge_user_episodes(user_id)
        self.metrics.user_memories_count = self.long_term_memory.user_memory_count()
        return {"memories_purged": mem_count, "episodes_purged": ep_count}

    def purge_project_privacy_data(self, project_id: str) -> Dict[str, int]:
        """Hard purge all memory records and episodic history for a project."""
        mem_count = self.long_term_memory.purge_project_data(project_id)
        ep_count = self.episodic_memory.purge_project_episodes(project_id)
        self.metrics.project_memories_count = self.long_term_memory.project_memory_count()
        return {"memories_purged": mem_count, "episodes_purged": ep_count}

    def redact_memory_pii(self, memory_id: str) -> bool:
        """Redact PII patterns from a stored memory entry."""
        return self.long_term_memory.redact_memory(memory_id)

    # --- Sprint 11: NetworkX Topology & Subgraph ---

    def compute_centrality(self, metric: str = "degree") -> Dict[str, float]:
        """Compute node centrality using NetworkX or degree fallback."""
        return self.graph.compute_centrality(metric=metric)

    def extract_subgraph(self, node_ids: List[str]) -> Dict[str, Any]:
        """Extract a subgraph containing specified node IDs and connecting edges."""
        return self.graph.extract_subgraph(node_ids)

    def save(self, filename: str = "knowledge_graph.json") -> str:
        """Persist graph data to file."""
        path = self.storage.save_to_file(filename)
        return str(path)

    def load(self, filename: str = "knowledge_graph.json") -> bool:
        """Load graph data from file."""
        success = self.storage.load_from_file(filename)
        if success:
            self.metrics.node_count = self.graph.node_count
            self.metrics.edge_count = self.graph.edge_count
        return success

