"""Evidence and Traceability Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceType(str, Enum):
    EMPIRICAL = "empirical"
    BENCHMARK = "benchmark"
    EXPERT_OPINION = "expert_opinion"
    DOCUMENTATION = "documentation"
    METRIC = "metric"
    HISTORICAL_DATA = "historical_data"
    LIVE_VERIFICATION = "live_verification"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"


@dataclass
class EvidenceItem:
    """Represents a specific piece of evidence linked to an option and criterion."""

    evidence_id: str = field(default_factory=lambda: f"evi_{uuid.uuid4().hex[:8]}")
    option_id: str = ""
    criterion_id: str = ""
    evidence_type: EvidenceType = EvidenceType.BENCHMARK
    source_subsystem: str = "general"  # knowledge_graph, data_intelligence, connector, browser, etc.
    source_reference: str = ""  # URL, document ID, entity URI, or search snippet
    title: str = ""
    snippet: str = ""
    confidence_score: float = 1.0  # 0.0 to 1.0
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "option_id": self.option_id,
            "criterion_id": self.criterion_id,
            "evidence_type": self.evidence_type.value,
            "source_subsystem": self.source_subsystem,
            "source_reference": self.source_reference,
            "title": self.title,
            "snippet": self.snippet,
            "confidence_score": self.confidence_score,
            "verification_status": self.verification_status.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
