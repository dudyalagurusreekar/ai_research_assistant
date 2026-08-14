"""Knowledge Synchronizer — Bi-directional sync between Knowledge Graph and ARA subsystems."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.knowledge_graph.components.graph_builder import GraphBuilder
from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityNode, EntityType
from utils.logger import get_logger

logger = get_logger("KnowledgeSynchronizer")


class KnowledgeSynchronizer:
    """Synchronizes KnowledgeGraph bi-directionally across MemorySystem, SharedWorkspace, DataMemory, and ExperienceStore."""

    def __init__(self, graph: Optional[KnowledgeGraph] = None) -> None:
        self.graph = graph or KnowledgeGraph()
        self.builder = GraphBuilder(self.graph)

    def sync_workspace_artifacts(self, workspace: Any) -> int:
        """Sync intermediate artifacts and data from SharedWorkspace into Knowledge Graph."""
        if not workspace or not hasattr(workspace, "list_keys"):
            return 0

        synced_count = 0
        keys = workspace.list_keys()

        for key in keys:
            val = workspace.get(key)
            node = EntityNode(
                name=f"Artifact:{key}",
                canonical_name=f"artifact:{key}".lower(),
                entity_type=EntityType.DOCUMENT if "report" in key or "text" in key else EntityType.DATASET,
                confidence_score=0.95,
                properties={"workspace_key": key, "artifact_val": str(val)[:200]},
                tags=["workspace_sync"],
            )
            self.graph.add_node(node)
            synced_count += 1

        logger.info(f"KnowledgeSynchronizer synced {synced_count} artifacts from SharedWorkspace")
        return synced_count

    def sync_learning_experiences(self, experience_store: Any) -> int:
        """Sync pattern insights and strategy records from ExperienceStore into Knowledge Graph."""
        if not experience_store:
            return 0

        synced_count = 0
        try:
            if hasattr(experience_store, "list_records"):
                records = experience_store.list_records()
            elif hasattr(experience_store, "list_experiences"):
                records = experience_store.list_experiences()
            elif hasattr(experience_store, "_records"):
                records = list(experience_store._records.values())
            else:
                records = []

            for rec in records:
                query_str = getattr(rec, "query", "experience_query")
                node = EntityNode(
                    name=f"Strategy:{query_str[:30]}",
                    canonical_name=f"strategy:{query_str[:30]}".lower(),
                    entity_type=EntityType.METHOD,
                    confidence_score=0.90,
                    properties={"intent": getattr(rec, "intent", ""), "tools": getattr(rec, "selected_tools", [])},
                    tags=["learning_sync"],
                )
                self.graph.add_node(node)
                synced_count += 1
        except Exception as exc:
            logger.warning(f"Error syncing experiences: {exc}")

        logger.info(f"KnowledgeSynchronizer synced {synced_count} experience records into Knowledge Graph")
        return synced_count
