"""Relation Edge models — Semantic Relationship representation for Knowledge Graph."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RelationType(Enum):
    """Categorized relationship predicate types in the knowledge graph."""

    USES = "uses"
    IMPLEMENTS = "implements"
    IMPROVES = "improves"
    EVALUATES_ON = "evaluates_on"
    BENCHMARKS = "benchmarks"
    AUTHORED_BY = "authored_by"
    DEPENDS_ON = "depends_on"
    CONTRADICTS = "contradicts"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    PRODUCES = "produces"
    DERIVED_FROM = "derived_from"
    # Sprint 11 — Expanded relationship types
    CITES = "cites"
    DEVELOPED_BY = "developed_by"
    LOCATED_IN = "located_in"
    FUNDED_BY = "funded_by"
    COMPETES_WITH = "competes_with"
    EMPLOYS = "employs"
    INTEGRATES = "integrates"


@dataclass
class RelationEdge:
    """A directed semantic edge connecting source_node_id to target_node_id."""

    source_id: str
    target_id: str
    relation_type: RelationType = RelationType.RELATED_TO
    weight: float = 1.0
    confidence_score: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    is_directional: bool = True
    edge_id: str = field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:10]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    def add_evidence(self, source_id: str, source_type: str, confidence: float,
                     snippet: str = "", timestamp: Optional[str] = None) -> None:
        """Attach an evidence record to this edge."""
        self.evidence.append({
            "evidence_id": f"ev_{uuid.uuid4().hex[:8]}",
            "source_id": source_id,
            "source_type": source_type,
            "confidence": confidence,
            "snippet": snippet[:500],
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "retrieval_count": 0,
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "weight": self.weight,
            "confidence_score": self.confidence_score,
            "properties": self.properties,
            "is_directional": self.is_directional,
            "created_at": self.created_at,
            "evidence": self.evidence,
        }
