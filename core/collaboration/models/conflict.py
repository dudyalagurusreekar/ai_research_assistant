"""Conflict models — Types, Resolution Strategies, and Audit Records."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ConflictType(Enum):
    """Categories of detected conflicts between agent outputs."""

    CONTRADICTORY_DATA = "contradictory_data"
    QUALITY_GATE_FAILURE = "quality_gate_failure"
    FACTUAL_DISCREPANCY = "factual_discrepancy"
    SCHEMA_MISMATCH = "schema_mismatch"
    TIMEOUT = "timeout"


class ResolutionStrategy(Enum):
    """Strategies for reconciling conflicting agent outputs."""

    CONFIDENCE_WEIGHTED = "confidence_weighted"
    REVIEWER_OVERRIDE = "reviewer_override"
    RE_EXECUTION = "re_execution"
    HYBRID_MERGE = "hybrid_merge"
    CONSENSUS = "consensus"


@dataclass
class ConflictRecord:
    """Audit record capturing a conflict event and its resolution."""

    conflict_id: str = field(default_factory=lambda: f"cnf_{uuid.uuid4().hex[:8]}")
    conflict_type: ConflictType = ConflictType.FACTUAL_DISCREPANCY
    description: str = ""
    involved_agent_ids: List[str] = field(default_factory=list)
    conflicting_outputs: Dict[str, Any] = field(default_factory=dict)
    applied_strategy: Optional[ResolutionStrategy] = None
    resolved_output: Optional[Any] = None
    confidence_score: float = 0.0
    is_resolved: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type.value,
            "description": self.description,
            "involved_agent_ids": self.involved_agent_ids,
            "applied_strategy": self.applied_strategy.value if self.applied_strategy else None,
            "confidence_score": self.confidence_score,
            "is_resolved": self.is_resolved,
            "timestamp": self.timestamp,
        }
