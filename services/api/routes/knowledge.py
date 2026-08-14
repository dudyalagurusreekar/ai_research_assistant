"""REST API Router for Knowledge Graph & Long-Term Memory Platform (/api/v1/knowledge)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session
from core.knowledge_graph.engine import KnowledgeGraphEngine
from core.knowledge_graph.models.node import EntityType
from core.knowledge_graph.models.edge import RelationType
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import ResponseEnvelope

router = APIRouter(prefix="/knowledge", tags=["Knowledge Graph & Long-Term Memory"])

# Singleton engine instance
_kg_engine: Optional[KnowledgeGraphEngine] = None


def get_kg_engine() -> KnowledgeGraphEngine:
    """Get or create the singleton KnowledgeGraphEngine instance."""
    global _kg_engine
    if _kg_engine is None:
        _kg_engine = KnowledgeGraphEngine()
    return _kg_engine


# --- Request/Response Schemas ---

class AddEntityRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    entity_type: str = Field(default="concept")
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0)
    aliases: List[str] = Field(default_factory=list)
    properties: dict = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class AddRelationshipRequest(BaseModel):
    source_name: str = Field(..., min_length=1)
    target_name: str = Field(..., min_length=1)
    relation_type: str = Field(default="related_to")
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0)
    evidence_snippet: str = Field(default="")
    evidence_source_id: str = Field(default="user_input")
    evidence_source_type: str = Field(default="user_input")


class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source_id: str = Field(default="api_ingest")


class StoreMemoryRequest(BaseModel):
    key: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    ttl_days: Optional[int] = Field(default=None, ge=1)


class RecordEpisodeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    plan_steps: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    sources_consulted: List[str] = Field(default_factory=list)
    outcome: str = Field(default="")
    success: bool = Field(default=True)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    duration_ms: float = Field(default=0.0)


# --- Entity Endpoints ---

@router.post("/entities", status_code=status.HTTP_201_CREATED)
async def add_entity(
    body: AddEntityRequest,
    current_user: User = Depends(get_current_user),
):
    """Add an entity node to the knowledge graph."""
    engine = get_kg_engine()
    try:
        etype = EntityType(body.entity_type)
    except ValueError:
        etype = EntityType.CONCEPT

    from core.knowledge_graph.models.node import EntityNode
    node = EntityNode(
        name=body.name,
        entity_type=etype,
        confidence_score=body.confidence_score,
        aliases=body.aliases,
        properties=body.properties,
        tags=body.tags,
    )
    added = engine.graph.add_node(node)
    engine.metrics.node_count = engine.graph.node_count
    return ResponseEnvelope(data=added.to_dict(), message="Entity added to knowledge graph")


@router.post("/relationships", status_code=status.HTTP_201_CREATED)
async def add_relationship(
    body: AddRelationshipRequest,
    current_user: User = Depends(get_current_user),
):
    """Add a relationship edge with evidence to the knowledge graph."""
    engine = get_kg_engine()

    source = engine.graph.find_node_by_name(body.source_name)
    target = engine.graph.find_node_by_name(body.target_name)

    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source entity '{body.source_name}' not found")
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target entity '{body.target_name}' not found")

    try:
        rtype = RelationType(body.relation_type)
    except ValueError:
        rtype = RelationType.RELATED_TO

    from core.knowledge_graph.models.edge import RelationEdge
    edge = RelationEdge(
        source_id=source.node_id,
        target_id=target.node_id,
        relation_type=rtype,
        confidence_score=body.confidence_score,
    )
    edge.add_evidence(
        source_id=body.evidence_source_id,
        source_type=body.evidence_source_type,
        confidence=body.confidence_score,
        snippet=body.evidence_snippet,
    )

    added = engine.graph.add_edge(edge)
    engine.metrics.edge_count = engine.graph.edge_count
    engine.metrics.evidence_records_count += 1
    return ResponseEnvelope(data=added.to_dict(), message="Relationship added to knowledge graph")


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_text(
    body: IngestTextRequest,
    current_user: User = Depends(get_current_user),
):
    """Ingest text, extract entities and relationships, and add to knowledge graph."""
    engine = get_kg_engine()
    nodes, edges = engine.ingest_text(body.text, source_id=body.source_id)
    return ResponseEnvelope(
        data={"nodes_added": len(nodes), "edges_added": len(edges)},
        message=f"Ingested text: {len(nodes)} entities, {len(edges)} relationships extracted",
    )


# --- Search & Graph Endpoints ---

@router.get("/search")
async def search_graph(
    q: str = Query(..., min_length=1, description="Search query"),
    entity_type: Optional[str] = Query(default=None),
    min_confidence: float = Query(default=0.3, ge=0.0, le=1.0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Semantic search across the knowledge graph."""
    engine = get_kg_engine()

    from core.knowledge_graph.models.query import GraphQuery, SearchMode
    entity_types = None
    if entity_type:
        try:
            entity_types = [EntityType(entity_type)]
        except ValueError:
            pass

    query = GraphQuery(
        query_text=q,
        entity_types=entity_types,
        min_confidence=min_confidence,
        limit=limit,
        search_mode=SearchMode.HYBRID,
    )
    result = engine.query(query)
    return ResponseEnvelope(data=result.to_dict(), message=f"Found {result.total_nodes_found} matching nodes")


@router.get("/graph")
async def export_graph(
    entity_type: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
):
    """Export graph as JSON (nodes + edges)."""
    engine = get_kg_engine()
    etype = None
    if entity_type:
        try:
            etype = EntityType(entity_type)
        except ValueError:
            pass

    nodes = engine.graph.list_nodes(entity_type=etype)[:limit]
    edges = engine.graph.list_edges()
    node_ids = {n.node_id for n in nodes}
    filtered_edges = [e for e in edges if e.source_id in node_ids and e.target_id in node_ids]

    return ResponseEnvelope(
        data={
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in filtered_edges[:limit * 3]],
            "total_nodes": len(nodes),
            "total_edges": len(filtered_edges),
        },
        message="Graph exported successfully",
    )


@router.get("/graph/{node_id}/neighbors")
async def get_neighbors(
    node_id: str,
    max_hops: int = Query(default=1, ge=1, le=4),
    current_user: User = Depends(get_current_user),
):
    """Get k-hop neighborhood of a node."""
    engine = get_kg_engine()
    node = engine.graph.get_node(node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Node '{node_id}' not found")

    neighbors = engine.graph.get_neighbors(node_id)
    out_edges = engine.graph.get_out_edges(node_id)
    in_edges = engine.graph.get_in_edges(node_id)

    return ResponseEnvelope(
        data={
            "center_node": node.to_dict(),
            "neighbors": [n.to_dict() for n in neighbors],
            "outgoing_edges": [e.to_dict() for e in out_edges],
            "incoming_edges": [e.to_dict() for e in in_edges],
        },
        message=f"Found {len(neighbors)} neighbors",
    )


# --- Memory Endpoints ---

@router.post("/memory/user")
async def store_user_memory(
    body: StoreMemoryRequest,
    current_user: User = Depends(get_current_user),
):
    """Store a user-scoped memory entry."""
    engine = get_kg_engine()
    entry = engine.store_memory("user", str(current_user.id), body.key, body.value,
                                 importance=body.importance, ttl_days=body.ttl_days)
    return ResponseEnvelope(data=entry.to_dict(), message="User memory stored")


@router.post("/memory/project")
async def store_project_memory(
    project_id: str = Query(...),
    body: StoreMemoryRequest = ...,
    current_user: User = Depends(get_current_user),
):
    """Store a project-scoped memory entry."""
    engine = get_kg_engine()
    entry = engine.store_memory("project", project_id, body.key, body.value,
                                 importance=body.importance, ttl_days=body.ttl_days)
    return ResponseEnvelope(data=entry.to_dict(), message="Project memory stored")


@router.get("/memory/user/{user_id}")
async def get_user_memories(
    user_id: str,
    key: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """Retrieve user-scoped memories."""
    engine = get_kg_engine()
    memories = engine.recall_memory("user", user_id, key)
    return ResponseEnvelope(
        data=[m.to_dict() for m in memories[:limit]],
        message=f"Retrieved {min(len(memories), limit)} user memories",
    )


@router.get("/memory/project/{project_id}")
async def get_project_memories(
    project_id: str,
    key: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """Retrieve project-scoped memories."""
    engine = get_kg_engine()
    memories = engine.recall_memory("project", project_id, key)
    return ResponseEnvelope(
        data=[m.to_dict() for m in memories[:limit]],
        message=f"Retrieved {min(len(memories), limit)} project memories",
    )


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a specific memory entry."""
    engine = get_kg_engine()
    success = engine.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory '{memory_id}' not found")
    return ResponseEnvelope(data={"deleted": memory_id}, message="Memory deleted successfully")


# --- Episode Endpoints ---

@router.post("/episodes", status_code=status.HTTP_201_CREATED)
async def record_episode(
    body: RecordEpisodeRequest,
    current_user: User = Depends(get_current_user),
):
    """Record an execution episode."""
    engine = get_kg_engine()
    episode = engine.record_episode(
        query=body.query,
        plan_steps=body.plan_steps,
        tools_used=body.tools_used,
        sources=body.sources_consulted,
        outcome=body.outcome,
        success=body.success,
        confidence=body.confidence_score,
        user_id=str(current_user.id),
        duration_ms=body.duration_ms,
    )
    return ResponseEnvelope(data=episode.to_dict(), message="Episode recorded")


@router.get("/episodes")
async def list_episodes(
    project_id: Optional[str] = Query(default=None),
    success_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """List episodic memories."""
    engine = get_kg_engine()
    episodes = engine.episodic_memory.list_episodes(
        user_id=str(current_user.id),
        project_id=project_id,
        success_only=success_only,
        limit=limit,
    )
    return ResponseEnvelope(
        data=[e.to_dict() for e in episodes],
        message=f"Retrieved {len(episodes)} episodes",
    )


# --- Metrics Endpoint ---

@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(get_current_user),
):
    """Get knowledge graph observability metrics."""
    engine = get_kg_engine()
    summary = engine.get_graph_summary()
    return ResponseEnvelope(data=summary, message="Knowledge graph metrics retrieved")


# --- Policy Endpoint ---

@router.post("/policies/enforce")
async def enforce_policies(
    current_user: User = Depends(get_current_user),
):
    """Run memory policy enforcement (expiration, importance scoring, pruning)."""
    engine = get_kg_engine()
    result = engine.enforce_policies()
    return ResponseEnvelope(data=result, message="Memory policies enforced")


# --- Sprint 11: Snapshot & Versioning Endpoints ---

class CreateSnapshotRequest(BaseModel):
    tag: str = Field(default="auto", max_length=50)
    metadata: dict = Field(default_factory=dict)


class ExtractSubgraphRequest(BaseModel):
    node_ids: List[str] = Field(..., min_items=1)


@router.post("/snapshots", status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    body: CreateSnapshotRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a versioned snapshot of the knowledge graph."""
    engine = get_kg_engine()
    snapshot = engine.create_snapshot(tag=body.tag, metadata=body.metadata)
    return ResponseEnvelope(data=snapshot.to_dict(), message=f"Graph snapshot '{snapshot.snapshot_id}' created")


@router.get("/snapshots")
async def list_snapshots(
    current_user: User = Depends(get_current_user),
):
    """List all saved graph snapshots."""
    engine = get_kg_engine()
    snapshots = engine.list_snapshots()
    return ResponseEnvelope(data=snapshots, message=f"Retrieved {len(snapshots)} snapshots")


@router.post("/snapshots/{snapshot_id}/load")
async def load_snapshot(
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
):
    """Load a specific graph snapshot by ID."""
    engine = get_kg_engine()
    success = engine.load_snapshot(snapshot_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Snapshot '{snapshot_id}' not found")
    return ResponseEnvelope(data={"loaded": snapshot_id}, message=f"Snapshot '{snapshot_id}' loaded successfully")


@router.get("/snapshots/diff")
async def compare_snapshots(
    from_snapshot_id: str = Query(...),
    to_snapshot_id: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    """Compare two graph snapshots and compute diff."""
    engine = get_kg_engine()
    try:
        diff = engine.compare_snapshots(from_snapshot_id, to_snapshot_id)
        return ResponseEnvelope(data=diff.to_dict(), message="Snapshot diff computed successfully")
    except FileNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


# --- Sprint 11: Privacy Controls & Hard Purge Endpoints ---

@router.post("/privacy/redact/{memory_id}")
async def redact_memory_pii(
    memory_id: str,
    current_user: User = Depends(get_current_user),
):
    """Redact PII (email, phone, API keys) from a stored memory entry."""
    engine = get_kg_engine()
    success = engine.redact_memory_pii(memory_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory record '{memory_id}' not found")
    return ResponseEnvelope(data={"redacted": memory_id}, message="Memory content redacted successfully")


@router.delete("/privacy/user/{user_id}")
async def purge_user_privacy(
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    """Hard purge all memory records and episodic history for a user."""
    engine = get_kg_engine()
    res = engine.purge_user_privacy_data(user_id)
    return ResponseEnvelope(data=res, message=f"Purged user privacy data for user '{user_id}'")


@router.delete("/privacy/project/{project_id}")
async def purge_project_privacy(
    project_id: str,
    current_user: User = Depends(get_current_user),
):
    """Hard purge all memory records and episodic history for a project."""
    engine = get_kg_engine()
    res = engine.purge_project_privacy_data(project_id)
    return ResponseEnvelope(data=res, message=f"Purged project privacy data for project '{project_id}'")


# --- Sprint 11: Topology & Graph Analysis Endpoints ---

@router.get("/graph/centrality")
async def get_node_centrality(
    metric: str = Query(default="degree", regex="^(degree|pagerank|betweenness)$"),
    current_user: User = Depends(get_current_user),
):
    """Compute node centrality scores using NetworkX algorithms."""
    engine = get_kg_engine()
    scores = engine.compute_centrality(metric=metric)
    return ResponseEnvelope(data=scores, message=f"Computed '{metric}' centrality scores")


@router.post("/graph/subgraph")
async def extract_subgraph(
    body: ExtractSubgraphRequest,
    current_user: User = Depends(get_current_user),
):
    """Extract a subgraph for specified node IDs."""
    engine = get_kg_engine()
    subgraph = engine.extract_subgraph(body.node_ids)
    return ResponseEnvelope(data=subgraph, message="Subgraph extracted successfully")


@router.get("/graph/paths")
async def find_paths(
    source_name: str = Query(..., min_length=1),
    target_name: str = Query(..., min_length=1),
    max_depth: int = Query(default=4, ge=1, le=8),
    current_user: User = Depends(get_current_user),
):
    """Find multi-hop semantic paths between source and target node names."""
    engine = get_kg_engine()
    paths = engine.find_path(source_name, target_name, max_depth=max_depth)
    return ResponseEnvelope(data=[p.to_dict() for p in paths], message=f"Found {len(paths)} path(s)")


@router.get("/memory")
async def get_all_memories(
    current_user: User = Depends(get_current_user),
):
    """Retrieve combined long term memory entries."""
    engine = get_kg_engine()
    memories = engine.recall_memory("user", str(current_user.id))
    return ResponseEnvelope(
        data={"memories": [m.to_dict() for m in memories]},
        message="Long term memories retrieved successfully",
    )

