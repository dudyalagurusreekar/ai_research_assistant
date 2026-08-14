"""Conflict models — Discrepancy analysis and evidence resolution audit records."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ConflictSeverity(Enum):
    """Severity classification of evidence conflicts."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionAction(Enum):
    """Strategy action used to resolve evidence conflicts."""

    WEIGHTED_MERGE = "weighted_merge"
    SOURCE_OVERRIDE = "source_override"
    RE_EXECUTE_VERIFICATION = "re_execute_verification"
    DISCARD_LOW_CONFIDENCE = "discard_low_confidence"


@dataclass
class ConflictReport:
    """Audit report capturing contradictory evidence across research sources."""

    description: str
    conflicting_evidence_ids: List[str] = field(default_factory=list)
    severity: ConflictSeverity = ConflictSeverity.MODERATE
    applied_resolution: Optional[ResolutionAction] = None
    resolved_finding: str = ""
    is_resolved: bool = False
    conflict_id: str = field(default_factory=lambda: f"cnf_{uuid.uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "description": self.description,
            "conflicting_evidence_ids": self.conflicting_evidence_ids,
            "severity": self.severity.value,
            "applied_resolution": self.applied_resolution.value if self.applied_resolution else None,
            "is_resolved": self.is_resolved,
            "resolved_finding": self.resolved_finding,
        }
