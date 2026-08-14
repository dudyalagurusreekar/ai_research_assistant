"""Graph Versioning and Snapshot Models — Pydantic models for Knowledge Graph history, snapshots, and diffs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GraphSnapshot(BaseModel):
    """Snapshot representation of a knowledge graph state at a specific point in time."""

    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    version: int = Field(..., description="Monotonically increasing version number")
    tag: str = Field(default="auto", description="Snapshot tag or label")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of snapshot creation",
    )
    parent_snapshot_id: Optional[str] = Field(None, description="Parent snapshot ID if incremental")
    node_count: int = Field(default=0, description="Total node count in graph")
    edge_count: int = Field(default=0, description="Total edge count in graph")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Serialized nodes")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="Serialized edges")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary snapshot metadata")

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary representation."""
        return self.model_dump()


class GraphDiff(BaseModel):
    """Difference analysis between two graph versions or snapshots."""

    from_version: int = Field(..., description="Base version number")
    to_version: int = Field(..., description="Target version number")
    nodes_added: List[str] = Field(default_factory=list, description="Node IDs added in target version")
    nodes_removed: List[str] = Field(default_factory=list, description="Node IDs removed in target version")
    edges_added: List[str] = Field(default_factory=list, description="Edge IDs added in target version")
    edges_removed: List[str] = Field(default_factory=list, description="Edge IDs removed in target version")
    nodes_modified: List[str] = Field(default_factory=list, description="Node IDs modified in target version")
    edges_modified: List[str] = Field(default_factory=list, description="Edge IDs modified in target version")

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph diff to dictionary representation."""
        return self.model_dump()


class VersionInfo(BaseModel):
    """Metadata regarding current graph version and history."""

    current_version: int = Field(default=1, description="Current graph version number")
    total_snapshots: int = Field(default=0, description="Number of saved snapshots")
    latest_snapshot_id: Optional[str] = Field(None, description="Latest snapshot ID")
    latest_snapshot_at: Optional[str] = Field(None, description="Latest snapshot timestamp")
