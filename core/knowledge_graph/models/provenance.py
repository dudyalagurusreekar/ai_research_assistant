"""Provenance models — Tracks origin, source metadata, and creation evidence."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class SourceType(Enum):
    """Categorized source types for knowledge provenance."""

    DOCUMENT = "document"
    RESEARCH_OUTPUT = "research_output"
    CODE = "code"
    DATASET = "dataset"
    CONVERSATION = "conversation"
    MULTI_AGENT_WORKSPACE = "multi_agent_workspace"


@dataclass
class ExtractionProvenance:
    """Audit object tracing how and where an entity/edge was extracted."""

    source_type: SourceType = SourceType.DOCUMENT
    source_id: str = ""
    extractor_name: str = "entity_extractor"
    raw_snippet: str = ""
    author_id: str = "system"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provenance_id: str = field(default_factory=lambda: f"prov_{uuid.uuid4().hex[:8]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provenance_id": self.provenance_id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "extractor_name": self.extractor_name,
            "raw_snippet": self.raw_snippet,
            "author_id": self.author_id,
            "timestamp": self.timestamp,
        }
