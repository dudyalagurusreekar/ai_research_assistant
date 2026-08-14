"""Entity Node models — Types, Metadata, and Representation for Knowledge Graph."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class EntityType(Enum):
    """Categorized entity types supported in the knowledge graph."""

    CONCEPT = "concept"
    METHOD = "method"
    DATASET = "dataset"
    MODEL = "model"
    CODE_SYMBOL = "code_symbol"
    AUTHOR = "author"
    ORGANIZATION = "organization"
    METRIC = "metric"
    TOOL = "tool"
    DOCUMENT = "document"
    EVENT = "event"
    TASK = "task"
    # Sprint 11 — Expanded entity types
    PERSON = "person"
    LOCATION = "location"
    RESEARCH_PAPER = "research_paper"
    TECHNOLOGY = "technology"
    API = "api"
    PROGRAMMING_LANGUAGE = "programming_language"
    LIBRARY = "library"
    PRODUCT = "product"



@dataclass
class EntityNode:
    """A single vertex/entity in the Knowledge Graph."""

    name: str
    entity_type: EntityType = EntityType.CONCEPT
    canonical_name: str = ""
    aliases: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    node_id: str = field(default_factory=lambda: f"node_{uuid.uuid4().hex[:10]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    access_count: int = 0
    decay_score: float = 1.0

    def __post_init__(self):
        if not self.canonical_name:
            self.canonical_name = self.name.lower().strip()
        if self.canonical_name not in [a.lower() for a in self.aliases]:
            self.aliases.append(self.canonical_name)

    def matches_name(self, query_name: str) -> bool:
        """Check if query matches name, canonical name, or any alias."""
        clean_q = query_name.lower().strip()
        if clean_q == self.canonical_name or clean_q == self.name.lower():
            return True
        return any(clean_q == alias.lower() for alias in self.aliases)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type.value,
            "aliases": self.aliases,
            "confidence_score": self.confidence_score,
            "properties": self.properties,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "decay_score": self.decay_score,
        }
