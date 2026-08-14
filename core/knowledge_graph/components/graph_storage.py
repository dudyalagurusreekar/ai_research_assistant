"""Graph Storage — Indexed property graph storage, persistence, and filtering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode, EntityType
from utils.logger import get_logger

logger = get_logger("GraphStorage")


class GraphStorage:
    """Manages graph persistence, inverted index lookups, and JSON/SQLite export."""

    def __init__(self, graph: Optional[KnowledgeGraph] = None, storage_dir: Optional[str] = None) -> None:
        self.graph = graph or KnowledgeGraph()
        self.storage_dir = Path(storage_dir) if storage_dir else Path.cwd() / ".storage" / "knowledge_graph"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_to_file(self, filename: str = "knowledge_graph.json") -> Path:
        """Persist graph nodes and edges to JSON file."""
        filepath = self.storage_dir / filename
        data = {
            "graph_id": self.graph.graph_id,
            "nodes": [n.to_dict() for n in self.graph.list_nodes()],
            "edges": [e.to_dict() for e in self.graph.list_edges()],
        }

        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"GraphStorage saved graph to {filepath} ({self.graph.node_count} nodes, {self.graph.edge_count} edges)")
        return filepath

    def load_from_file(self, filename: str = "knowledge_graph.json") -> bool:
        """Load graph nodes and edges from JSON file."""
        filepath = self.storage_dir / filename
        if not filepath.exists():
            logger.warning(f"Storage file {filepath} does not exist")
            return False

        try:
            content = json.loads(filepath.read_text(encoding="utf-8"))
            self.graph.clear()

            for n_dict in content.get("nodes", []):
                etype = EntityType(n_dict.get("entity_type", "concept"))
                node = EntityNode(
                    node_id=n_dict.get("node_id"),
                    name=n_dict.get("name", ""),
                    canonical_name=n_dict.get("canonical_name", ""),
                    entity_type=etype,
                    aliases=n_dict.get("aliases", []),
                    confidence_score=n_dict.get("confidence_score", 1.0),
                    properties=n_dict.get("properties", {}),
                    tags=n_dict.get("tags", []),
                )
                self.graph.add_node(node)

            for e_dict in content.get("edges", []):
                rtype = RelationType(e_dict.get("relation_type", "related_to"))
                edge = RelationEdge(
                    edge_id=e_dict.get("edge_id"),
                    source_id=e_dict.get("source_id"),
                    target_id=e_dict.get("target_id"),
                    relation_type=rtype,
                    weight=e_dict.get("weight", 1.0),
                    confidence_score=e_dict.get("confidence_score", 1.0),
                    properties=e_dict.get("properties", {}),
                    is_directional=e_dict.get("is_directional", True),
                )
                self.graph.add_edge(edge)

            logger.info(f"GraphStorage loaded {self.graph.node_count} nodes, {self.graph.edge_count} edges from {filepath}")
            return True
        except Exception as exc:
            logger.error(f"Failed to load graph from {filepath}: {exc}")
            return False

    def save_snapshot(self, tag: str = "auto", metadata: Optional[Dict[str, Any]] = None) -> Any:
        """Create and persist a versioned snapshot of the current knowledge graph."""
        from uuid import uuid4
        from core.knowledge_graph.models.versioning import GraphSnapshot

        snapshot_dir = self.storage_dir / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        snapshot_id = f"snap_{uuid4().hex[:10]}"
        current_version = getattr(self.graph, "version", 1)

        snapshot = GraphSnapshot(
            snapshot_id=snapshot_id,
            version=current_version,
            tag=tag,
            node_count=self.graph.node_count,
            edge_count=self.graph.edge_count,
            nodes=[n.to_dict() for n in self.graph.list_nodes()],
            edges=[e.to_dict() for e in self.graph.list_edges()],
            metadata=metadata or {},
        )

        snap_file = snapshot_dir / f"{snapshot_id}.json"
        snap_file.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")
        logger.info(f"GraphStorage saved snapshot '{snapshot_id}' (v{current_version}) to {snap_file}")
        return snapshot

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all saved graph snapshots."""
        snapshot_dir = self.storage_dir / "snapshots"
        if not snapshot_dir.exists():
            return []

        snapshots = []
        for snap_file in sorted(snapshot_dir.glob("snap_*.json")):
            try:
                data = json.loads(snap_file.read_text(encoding="utf-8"))
                snapshots.append({
                    "snapshot_id": data.get("snapshot_id"),
                    "version": data.get("version"),
                    "tag": data.get("tag"),
                    "created_at": data.get("created_at"),
                    "node_count": data.get("node_count"),
                    "edge_count": data.get("edge_count"),
                })
            except Exception as err:
                logger.warning(f"Error reading snapshot file {snap_file}: {err}")
        return snapshots

    def load_snapshot(self, snapshot_id: str) -> bool:
        """Load a specific graph snapshot by ID."""
        snapshot_dir = self.storage_dir / "snapshots"
        snap_file = snapshot_dir / f"{snapshot_id}.json"
        if not snap_file.exists():
            logger.warning(f"Snapshot file {snap_file} does not exist")
            return False

        try:
            data = json.loads(snap_file.read_text(encoding="utf-8"))
            self.graph.clear()
            for n_dict in data.get("nodes", []):
                etype = EntityType(n_dict.get("entity_type", "concept"))
                node = EntityNode(
                    node_id=n_dict.get("node_id"),
                    name=n_dict.get("name", ""),
                    canonical_name=n_dict.get("canonical_name", ""),
                    entity_type=etype,
                    aliases=n_dict.get("aliases", []),
                    confidence_score=n_dict.get("confidence_score", 1.0),
                    properties=n_dict.get("properties", {}),
                    tags=n_dict.get("tags", []),
                )
                self.graph.add_node(node)

            for e_dict in data.get("edges", []):
                rtype = RelationType(e_dict.get("relation_type", "related_to"))
                edge = RelationEdge(
                    edge_id=e_dict.get("edge_id"),
                    source_id=e_dict.get("source_id"),
                    target_id=e_dict.get("target_id"),
                    relation_type=rtype,
                    weight=e_dict.get("weight", 1.0),
                    confidence_score=e_dict.get("confidence_score", 1.0),
                    properties=e_dict.get("properties", {}),
                    is_directional=e_dict.get("is_directional", True),
                )
                self.graph.add_edge(edge)

            self.graph.version = data.get("version", 1)
            logger.info(f"GraphStorage loaded snapshot '{snapshot_id}' (v{self.graph.version})")
            return True
        except Exception as exc:
            logger.error(f"Failed to load snapshot '{snapshot_id}': {exc}")
            return False

    def compare_snapshots(self, from_snapshot_id: str, to_snapshot_id: str) -> Any:
        """Compare two graph snapshots and compute diff."""
        from core.knowledge_graph.models.versioning import GraphDiff

        snapshot_dir = self.storage_dir / "snapshots"
        f_file = snapshot_dir / f"{from_snapshot_id}.json"
        t_file = snapshot_dir / f"{to_snapshot_id}.json"

        if not f_file.exists() or not t_file.exists():
            raise FileNotFoundError(f"One or both snapshot files missing: {from_snapshot_id}, {to_snapshot_id}")

        f_data = json.loads(f_file.read_text(encoding="utf-8"))
        t_data = json.loads(t_file.read_text(encoding="utf-8"))

        f_nodes = {n["node_id"] for n in f_data.get("nodes", [])}
        t_nodes = {n["node_id"] for n in t_data.get("nodes", [])}
        f_edges = {e["edge_id"] for e in f_data.get("edges", [])}
        t_edges = {e["edge_id"] for e in t_data.get("edges", [])}

        return GraphDiff(
            from_version=f_data.get("version", 0),
            to_version=t_data.get("version", 0),
            nodes_added=list(t_nodes - f_nodes),
            nodes_removed=list(f_nodes - t_nodes),
            edges_added=list(t_edges - f_edges),
            edges_removed=list(f_edges - t_edges),
        )

