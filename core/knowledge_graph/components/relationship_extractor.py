"""Relationship Extractor — Extracts semantic relations between extracted entity nodes."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from core.knowledge_graph.models.edge import RelationEdge, RelationType
from core.knowledge_graph.models.node import EntityNode, EntityType
from utils.logger import get_logger

logger = get_logger("RelationshipExtractor")


class RelationshipExtractor:
    """Extracts typed semantic relation edges between entity nodes using dependency parsing + pattern fallback."""

    def __init__(self) -> None:
        self._nlp = None
        self._spacy_available = False
        try:
            import spacy
            try:
                self._nlp = spacy.load("en_core_web_sm")
                self._spacy_available = True
                logger.info("RelationshipExtractor initialized with spaCy 'en_core_web_sm'")
            except Exception as e:
                self._nlp = spacy.blank("en")
                self._spacy_available = True
                logger.info(f"RelationshipExtractor initialized blank spaCy pipeline: {e}")
        except ImportError:
            logger.info("spaCy module not available for relationship parsing")

        self._predicate_patterns = [
            (r"\b(uses|using|leveraging|utilizes|utilizing)\b", RelationType.USES),
            (r"\b(implements|implementing|builds on|built on)\b", RelationType.IMPLEMENTS),
            (r"\b(improves|outperforms|boosts|enhances|surpasses)\b", RelationType.IMPROVES),
            (r"\b(evaluates on|evaluated on|tested on)\b", RelationType.EVALUATES_ON),
            (r"\b(benchmarks|benchmarked on)\b", RelationType.BENCHMARKS),
            (r"\b(authored by|written by|created by)\b", RelationType.AUTHORED_BY),
            (r"\b(depends on|requires|relying on)\b", RelationType.DEPENDS_ON),
            (r"\b(contradicts|disproves|conflicts with)\b", RelationType.CONTRADICTS),
            (r"\b(part of|belongs to|component of)\b", RelationType.PART_OF),
            (r"\b(produces|generates|yields)\b", RelationType.PRODUCES),
            (r"\b(derived from|based on)\b", RelationType.DERIVED_FROM),
        ]


    def extract_relationships(
        self, text: str, entities: List[EntityNode], source_id: str = "text_source"
    ) -> List[RelationEdge]:
        """Extract relations between entity pairs co-occurring in text."""
        edges: List[RelationEdge] = []
        if len(entities) < 2:
            return edges

        text_lower = text.lower()

        # Compare entity pairs
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                n1 = entities[i]
                n2 = entities[j]

                # Check for direct co-occurrence in text
                pos1 = text_lower.find(n1.name.lower())
                pos2 = text_lower.find(n2.name.lower())

                if pos1 != -1 and pos2 != -1 and abs(pos1 - pos2) < 200:
                    snippet = text_lower[min(pos1, pos2) : max(pos1, pos2) + len(n2.name)]
                    rel_type = self._infer_relation_type(snippet, n1.entity_type, n2.entity_type)

                    source_id_node = n1.node_id if pos1 <= pos2 else n2.node_id
                    target_id_node = n2.node_id if pos1 <= pos2 else n1.node_id

                    edge = RelationEdge(
                        source_id=source_id_node,
                        target_id=target_id_node,
                        relation_type=rel_type,
                        confidence_score=0.85,
                        properties={"source_id": source_id, "snippet": snippet[:100]},
                    )
                    edges.append(edge)

        logger.debug(f"RelationshipExtractor extracted {len(edges)} relation edges")
        return edges

    def _infer_relation_type(self, snippet: str, t1: EntityType, t2: EntityType) -> RelationType:
        """Infer RelationType from text snippet or entity type pair heuristics."""
        for pattern, rel_type in self._predicate_patterns:
            if re.search(pattern, snippet):
                return rel_type

        # Fallback domain type matching heuristics
        if t1 == EntityType.MODEL and t2 == EntityType.DATASET:
            return RelationType.EVALUATES_ON
        elif t1 == EntityType.METHOD and t2 == EntityType.MODEL:
            return RelationType.IMPLEMENTS
        elif t1 == EntityType.AUTHOR and t2 in (EntityType.MODEL, EntityType.DOCUMENT, EntityType.METHOD):
            return RelationType.AUTHORED_BY
        elif t1 == EntityType.CODE_SYMBOL and t2 == EntityType.TOOL:
            return RelationType.USES

        return RelationType.RELATED_TO
