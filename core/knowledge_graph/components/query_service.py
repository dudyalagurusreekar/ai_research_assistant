"""Graph Query Service — Cypher-like pattern matching and natural language Graph QA interface."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.knowledge_graph.components.graph_reasoning import GraphReasoningEngine
from core.knowledge_graph.components.semantic_retrieval import SemanticRetrievalEngine
from core.knowledge_graph.models.edge import RelationType
from core.knowledge_graph.models.graph import KnowledgeGraph
from core.knowledge_graph.models.node import EntityType
from core.knowledge_graph.models.query import (
    GraphPath,
    GraphQuery,
    GraphQueryResult,
    SearchMode,
)
from utils.logger import get_logger

logger = get_logger("GraphQueryService")


class GraphQueryService:
    """Service layer exposing structured pattern matching, path finding, and natural language Graph QA."""

    def __init__(
        self,
        graph: Optional[KnowledgeGraph] = None,
        retrieval_engine: Optional[SemanticRetrievalEngine] = None,
        reasoning_engine: Optional[GraphReasoningEngine] = None,
    ) -> None:
        self.graph = graph or KnowledgeGraph()
        self.retrieval_engine = retrieval_engine or SemanticRetrievalEngine(self.graph)
        self.reasoning_engine = reasoning_engine or GraphReasoningEngine(self.graph)

    def execute_query(self, query: GraphQuery) -> GraphQueryResult:
        """Execute structured graph query."""
        if query.search_mode == SearchMode.PATH_FINDING and query.source_entity_id and query.target_entity_id:
            start_t = time.time()
            paths = self.reasoning_engine.find_paths(
                query.source_entity_id, query.target_entity_id, max_depth=query.max_hop_depth, limit=query.limit
            )
            latency_ms = (time.time() - start_t) * 1000.0
            return GraphQueryResult(
                matched_nodes=[self.graph.get_node(query.source_entity_id), self.graph.get_node(query.target_entity_id)],
                paths=paths,
                query_latency_ms=latency_ms,
                reasoning_insights=[f"Found {len(paths)} path(s) connecting source to target."],
            )

        return self.retrieval_engine.search(query)

    def query_natural_language(self, question: str) -> GraphQueryResult:
        """Parse natural language question and execute semantic graph retrieval."""
        logger.info(f"GraphQueryService parsing natural language question: '{question}'")
        gquery = GraphQuery(
            query_text=question,
            max_hop_depth=2,
            min_confidence=0.4,
            limit=10,
            search_mode=SearchMode.HYBRID,
        )
        return self.execute_query(gquery)
