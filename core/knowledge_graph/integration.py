"""Integration adapters connecting Knowledge Graph Engine with Planner, Reflection, Learning, Data Intelligence, Multi-Agent Framework, and Memory System."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.knowledge_graph.engine import KnowledgeGraphEngine
from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.node import EntityNode, EntityType
from utils.logger import get_logger

logger = get_logger("KnowledgeGraphIntegration")


class PlannerKnowledgeIntegration:
    """Adapter bridging supervisory Planner with KnowledgeGraph for concept and past DAG retrieval."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def enhance_planner_context(self, planner_ctx: Any) -> Any:
        """Query KnowledgeGraph for domain concepts related to planner_ctx query and enrich constraints."""
        query = getattr(planner_ctx, "user_query", None) or getattr(planner_ctx, "query", "")
        if query:
            res = self.kg_engine.query(query)
            if res.matched_nodes:
                concept_names = [n.name for n in res.matched_nodes[:5]]
                if hasattr(planner_ctx, "reasoning_trace") and isinstance(planner_ctx.reasoning_trace, list):
                    planner_ctx.reasoning_trace.append(f"Knowledge Graph Context Concepts: {', '.join(concept_names)}")
                if hasattr(planner_ctx, "constraints") and hasattr(planner_ctx.constraints, "stopping_criteria"):
                    planner_ctx.constraints.stopping_criteria.append(f"Knowledge Graph Context Concepts: {', '.join(concept_names)}")
                logger.info(f"Enhanced PlannerContext with {len(concept_names)} KnowledgeGraph concept(s)")
        return planner_ctx


class ReflectionKnowledgeIntegration:
    """Adapter auditing facts and logging Reflection Engine decisions as nodes/edges in KnowledgeGraph."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def record_reflection_decision(self, decision: Any, query: str = "") -> None:
        """Record ReflectionDecision object as a graph node in KnowledgeGraph."""
        action = getattr(decision, "action", "proceed")
        if hasattr(action, "value"):
            action = action.value

        conf_score = getattr(decision, "confidence_score", None)
        if conf_score is None:
            reasoning_assessment = getattr(decision, "reasoning_assessment", None)
            conf_score = getattr(reasoning_assessment, "confidence_score", 0.9)

        node = EntityNode(
            name=f"ReflectionDecision:{action}",
            canonical_name=f"reflection:{action}:{query[:20]}".lower(),
            entity_type=EntityType.TASK,
            confidence_score=float(conf_score),
            properties={"action": str(action), "query": query},
            tags=["reflection_sync"],
        )
        self.kg_engine.graph.add_node(node)
        logger.info(f"Logged ReflectionDecision ({action}) in Knowledge Graph")


class LearningKnowledgeIntegration:
    """Adapter syncing Continuous Learning strategy recommendations into KnowledgeGraph."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def sync_experience_store(self, experience_store: Any) -> int:
        """Sync experience records into KnowledgeGraph."""
        return self.kg_engine.synchronizer.sync_learning_experiences(experience_store)


class DataKnowledgeIntegration:
    """Adapter ingesting dataset schemas, profiles, and statistical analysis into KnowledgeGraph."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def ingest_data_report(self, data_report: Any) -> int:
        """Ingest DataReport or DataProfile into KnowledgeGraph."""
        dataset_name = getattr(data_report, "dataset_name", "dataset")
        ds_node = EntityNode(
            name=dataset_name,
            canonical_name=dataset_name.lower().strip(),
            entity_type=EntityType.DATASET,
            confidence_score=0.98,
            tags=["data_intelligence"],
        )
        self.kg_engine.graph.add_node(ds_node)

        profile = getattr(data_report, "profile", None)
        stat_res = getattr(data_report, "statistical_result", None)
        summary = None

        if stat_res and hasattr(stat_res, "summary_metrics"):
            summary = stat_res.summary_metrics
        elif profile and hasattr(profile, "summary_statistics"):
            summary = profile.summary_statistics
        elif hasattr(data_report, "summary_statistics"):
            summary = getattr(data_report, "summary_statistics")

        if isinstance(summary, dict):
            for stat_name, stat_val in summary.items():
                m_node = EntityNode(
                    name=f"Metric:{stat_name}",
                    canonical_name=f"metric:{stat_name}".lower(),
                    entity_type=EntityType.METRIC,
                    confidence_score=0.95,
                    properties={"value": str(stat_val)},
                )
                self.kg_engine.graph.add_node(m_node)
                edge = RelationEdge(
                    source_id=ds_node.node_id,
                    target_id=m_node.node_id,
                    relation_type=RelationType.PRODUCES,
                )
                self.kg_engine.graph.add_edge(edge)

        return self.kg_engine.graph.node_count


class CollaborationKnowledgeIntegration:
    """Adapter syncing Multi-Agent Framework artifacts and outputs into KnowledgeGraph."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def sync_shared_workspace(self, workspace: Any) -> int:
        """Sync SharedWorkspace artifacts into KnowledgeGraph."""
        return self.kg_engine.synchronizer.sync_workspace_artifacts(workspace)


class MemorySystemKnowledgeIntegration:
    """Adapter bridging MemorySystem (tools/browser/memory) with KnowledgeGraph."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def sync_memory_item(self, memory_item: Any) -> EntityNode:
        """Convert a MemoryItem into an EntityNode in KnowledgeGraph."""
        content = getattr(memory_item, "content", "memory_content")
        mtype = getattr(memory_item, "memory_type", "semantic")
        if hasattr(mtype, "value"):
            mtype = mtype.value

        node = EntityNode(
            name=content[:40],
            canonical_name=content[:40].lower().strip(),
            entity_type=EntityType.CONCEPT,
            confidence_score=getattr(memory_item, "importance", 0.8),
            properties={"full_content": content, "memory_type": str(mtype)},
            tags=["memory_system_sync"],
        )
        return self.kg_engine.graph.add_node(node)


class BrowserKnowledgeIntegration:
    """Adapter ingesting browser navigation history, extracted content, and downloads into KnowledgeGraph."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def ingest_browser_session(self, session_data: Dict[str, Any]) -> int:
        """Ingest browser session navigation history and extracted data into KnowledgeGraph."""
        added = 0
        session_id = session_data.get("session_id", "browser_session")
        urls = session_data.get("visited_urls", [])

        for url in urls:
            node = EntityNode(
                name=url[:60],
                canonical_name=url.lower().strip()[:60],
                entity_type=EntityType.DOCUMENT,
                confidence_score=0.90,
                properties={"url": url, "source": "browser", "session_id": session_id},
                tags=["browser_sync"],
            )
            self.kg_engine.graph.add_node(node)
            added += 1

        extracted_text = session_data.get("extracted_text", "")
        if extracted_text:
            nodes, edges = self.kg_engine.ingest_text(extracted_text, source_id=f"browser:{session_id}")
            added += len(nodes)

        logger.info(f"BrowserKnowledgeIntegration ingested {added} items from session '{session_id}'")
        return added

    def ingest_download(self, download_data: Dict[str, Any]) -> EntityNode:
        """Ingest a browser download as a document node."""
        filename = download_data.get("filename", "download")
        node = EntityNode(
            name=filename,
            canonical_name=filename.lower().strip(),
            entity_type=EntityType.DOCUMENT,
            confidence_score=0.95,
            properties={
                "source": "browser_download",
                "url": download_data.get("url", ""),
                "file_size": download_data.get("file_size", 0),
            },
            tags=["browser_download"],
        )
        return self.kg_engine.graph.add_node(node)


class ConnectorKnowledgeIntegration:
    """Adapter ingesting external connector data (GitHub, Notion, Jira, Gmail, Drive) into KnowledgeGraph."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def ingest_connector_items(self, connector_type: str, items: List[Dict[str, Any]]) -> int:
        """Ingest items from an external connector into the KnowledgeGraph."""
        added = 0

        type_map = {
            "github": EntityType.TECHNOLOGY,
            "notion": EntityType.DOCUMENT,
            "jira": EntityType.TASK,
            "gmail": EntityType.DOCUMENT,
            "google_drive": EntityType.DOCUMENT,
        }
        entity_type = type_map.get(connector_type.lower(), EntityType.DOCUMENT)

        for item in items:
            title = item.get("title") or item.get("name") or item.get("subject", "connector_item")
            node = EntityNode(
                name=title[:60],
                canonical_name=title[:60].lower().strip(),
                entity_type=entity_type,
                confidence_score=0.90,
                properties={
                    "connector_type": connector_type,
                    "external_id": item.get("id", ""),
                    "url": item.get("url", ""),
                },
                tags=[f"connector_{connector_type.lower()}"],
            )
            self.kg_engine.graph.add_node(node)
            added += 1

        logger.info(f"ConnectorKnowledgeIntegration ingested {added} items from '{connector_type}'")
        return added


class RAGKnowledgeIntegration:
    """Adapter enhancing RAG retrieval using knowledge graph context, aliases, and neighbor expansion."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def expand_query_with_graph(self, query: str) -> str:
        """Expand a RAG query with aliases and related concepts from the knowledge graph."""
        result = self.kg_engine.query(query)
        if not result.matched_nodes:
            return query

        expansions = []
        for node in result.matched_nodes[:3]:
            for alias in node.aliases[:2]:
                if alias.lower() != query.lower() and alias not in expansions:
                    expansions.append(alias)

        if expansions:
            expanded = f"{query} {' '.join(expansions)}"
            logger.info(f"RAGKnowledgeIntegration expanded query: '{query}' → '{expanded[:100]}'")
            return expanded

        return query

    def supply_missing_context(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Supply additional context from graph neighbors for RAG retrieval."""
        result = self.kg_engine.query(query)
        context_items = []

        for node in result.matched_nodes[:limit]:
            context_items.append({
                "entity": node.name,
                "entity_type": node.entity_type.value,
                "properties": node.properties,
                "confidence": node.confidence_score,
            })

        return context_items


class OrchestratorKnowledgeIntegration:
    """Adapter connecting AI Orchestrator with Episodic Memory & Long-Term Memory."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def record_agent_execution(
        self, query: str, plan_steps: List[str], tools_used: List[str],
        outcome: str, success: bool = True, duration_ms: float = 0.0,
        user_id: str = "", project_id: str = "",
    ) -> Any:
        """Record agent execution run as an episode in episodic memory."""
        return self.kg_engine.record_episode(
            query=query,
            plan_steps=plan_steps,
            tools_used=tools_used,
            outcome=outcome,
            success=success,
            duration_ms=duration_ms,
            user_id=user_id,
            project_id=project_id,
        )

    def retrieve_execution_patterns(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve past successful execution patterns for a query."""
        episodes = self.kg_engine.recall_episodes(query, limit=limit)
        patterns = []
        for ep in episodes:
            if ep.success:
                patterns.append({
                    "episode_id": ep.episode_id,
                    "query": ep.query,
                    "plan_steps": ep.plan_steps,
                    "tools_used": ep.tools_used,
                    "confidence_score": ep.confidence_score,
                })
        return patterns


class ResearchWorkspaceKnowledgeIntegration:
    """Adapter bridging Research Workspace research notes and synthesis artifacts with KnowledgeGraph."""

    def __init__(self, kg_engine: Optional[KnowledgeGraphEngine] = None) -> None:
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

    def ingest_research_note(
        self, note_id: str, note_title: str, content: str, project_id: str = "default_project"
    ) -> int:
        """Ingest a research workspace note into KnowledgeGraph entities and long-term project memory."""
        node = EntityNode(
            name=note_title,
            canonical_name=note_title.lower().strip(),
            entity_type=EntityType.DOCUMENT,
            confidence_score=0.95,
            properties={"note_id": note_id, "project_id": project_id},
            tags=["research_workspace"],
        )
        self.kg_engine.graph.add_node(node)

        # Ingest text content into graph
        nodes, edges = self.kg_engine.ingest_text(content, source_id=f"workspace:{note_id}")

        # Store in project memory
        self.kg_engine.store_memory(
            scope="project",
            owner_id=project_id,
            key=f"note_{note_id}",
            value=f"Title: {note_title}\nContent: {content[:300]}",
            importance=0.8,
        )

        logger.info(f"Ingested research note '{note_title}' into KnowledgeGraph and project memory")
        return len(nodes) + 1


