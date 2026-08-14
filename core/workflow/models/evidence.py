"""Evidence models — Multi-source evidence representation and provenance tagging."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceSourceType(Enum):
    """Categorized source types for gathered evidence."""

    LITERATURE = "literature"
    WEB_SEARCH = "web_search"
    DATA_ANALYSIS = "data_analysis"
    CODE_EXECUTION = "code_execution"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class EvidenceConfidence(Enum):
    """Confidence classification for evidence validity."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EvidenceRecord:
    """Ingested evidence item supporting or refuting a research question."""

    question_id: str
    content: str
    source_type: EvidenceSourceType = EvidenceSourceType.LITERATURE
    source_name: str = ""
    source_url: Optional[str] = None
    doi: Optional[str] = None
    confidence: EvidenceConfidence = EvidenceConfidence.HIGH
    confidence_score: float = 0.90
    provenance_tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_id: str = field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "question_id": self.question_id,
            "source_type": self.source_type.value,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "doi": self.doi,
            "confidence_score": self.confidence_score,
            "provenance_tags": self.provenance_tags,
            "content_snippet": self.content[:150],
        }
