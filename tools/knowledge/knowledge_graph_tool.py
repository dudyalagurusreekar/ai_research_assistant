"""KnowledgeGraphTool — ToolRegistry integration exposing Knowledge Graph actions to AI agents."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from smolagents import Tool

from core.knowledge_graph.engine import KnowledgeGraphEngine
from core.knowledge_graph.models.edge import RelationType
from core.knowledge_graph.models.node import EntityType
from core.knowledge_graph.models.query import GraphQuery, SearchMode
from utils.logger import get_logger

logger = get_logger("KnowledgeGraphTool")


class KnowledgeGraphTool(Tool):
    """Tool exposing Knowledge Graph operations (query, search, add_fact, find_path) to CodeAgents."""

    name = "knowledge_graph_tool"
    description = (
        "Queries and updates the Knowledge Graph and Semantic Memory Engine. "
        "Actions: 'query' (natural language search), 'search' (entity search), "
        "'add_fact' (insert node/fact), 'find_path' (multi-hop pathfinding), "
        "'get_neighbors' (k-hop expansion), 'infer_relationships' (transitive inference)."
    )
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'query', 'search', 'add_fact', 'find_path', 'get_neighbors', 'infer_relationships'",
        },
        "query": {
            "type": "string",
            "description": "Search text, entity name, or natural language query",
            "nullable": True,
        },
        "source": {
            "type": "string",
            "description": "Source entity name or ID for pathfinding or facts",
            "nullable": True,
        },
        "target": {
            "type": "string",
            "description": "Target entity name or ID for pathfinding or facts",
            "nullable": True,
        },
        "relation": {
            "type": "string",
            "description": "Relation predicate type (e.g. 'uses', 'implements', 'improves')",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, engine: Optional[KnowledgeGraphEngine] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.engine = engine or KnowledgeGraphEngine()

    def forward(
        self,
        action: str,
        query: Optional[str] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        relation: Optional[str] = None,
    ) -> str:
        """Execute knowledge graph tool action."""
        action_clean = action.lower().strip()
        logger.info(f"KnowledgeGraphTool forward action='{action_clean}'")

        if action_clean in ["query", "search"]:
            q_text = query or source or "knowledge concept"
            res = self.engine.query(q_text)
            node_names = [n.name for n in res.matched_nodes[:5]]
            return f"Found {len(res.matched_nodes)} matched node(s): {', '.join(node_names)}"

        elif action_clean == "add_fact":
            fact_text = query or f"{source or 'Subject'} {relation or 'related_to'} {target or 'Object'}"
            added_nodes, added_edges = self.engine.ingest_text(fact_text)
            return f"Successfully added fact: +{len(added_nodes)} node(s), +{len(added_edges)} edge(s)."

        elif action_clean == "find_path":
            if not source or not target:
                return "Error: Both 'source' and 'target' must be provided for path finding."
            paths = self.engine.find_path(source, target)
            return f"Found {len(paths)} path(s) connecting '{source}' to '{target}'."

        elif action_clean == "get_neighbors":
            entity_name = query or source or ""
            node = self.engine.graph.find_node_by_name(entity_name)
            if not node:
                return f"Entity '{entity_name}' not found in Knowledge Graph."
            neighbors = self.engine.graph.get_neighbors(node.node_id)
            neighbor_names = [n.name for n in neighbors[:10]]
            return f"Entity '{node.name}' has {len(neighbors)} neighbor(s): {', '.join(neighbor_names)}"

        elif action_clean == "infer_relationships":
            inferred = self.engine.reasoning_engine.infer_transitive_relations()
            return f"Inferred {len(inferred)} transitive relationship edge(s)."

        else:
            return f"Unknown KnowledgeGraphTool action: '{action}'. Available: 'query', 'search', 'add_fact', 'find_path', 'get_neighbors', 'infer_relationships'."
