"""Evidence Record model — Traceable provenance for every knowledge graph relationship."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class EvidenceSourceType(Enum):
    """Source types for evidence provenance."""

    DOCUMENT = "document"
    BROWSER = "browser"
    CONNECTOR = "connector"
    CONVERSATION = "conversation"
    USER_INPUT = "user_input"
    RAG_RETRIEVAL = "rag_retrieval"
    API_RESPONSE = "api_response"
    RESEARCH_SESSION = "research_session"


@dataclass
class EvidenceRecord:
    """Traceable evidence record attached to knowledge graph relationships."""

    source_id: str = ""
    source_type: EvidenceSourceType = EvidenceSourceType.DOCUMENT
    confidence: float = 1.0
    snippet: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retrieval_count: int = 0
    evidence_id: str = field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "confidence": self.confidence,
            "snippet": self.snippet[:500],
            "timestamp": self.timestamp,
            "retrieval_count": self.retrieval_count,
            "metadata": self.metadata,
        }
