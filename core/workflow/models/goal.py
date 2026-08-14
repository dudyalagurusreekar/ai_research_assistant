"""Research Goal models — Deconstructed research objective and target constraints."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class GoalDomain(Enum):
    """Categorized domain disciplines for research goals."""

    COMPUTER_SCIENCE = "computer_science"
    BIOMEDICAL = "biomedical"
    FINANCE = "finance"
    GENERAL_SCIENCE = "general_science"
    ENGINEERING = "engineering"
    DATA_ANALYTICS = "data_analytics"


class GoalPriority(Enum):
    """Priority classifications for research goals."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ConstraintSpec:
    """Target operational and evidence constraints for a research goal."""

    max_execution_time_seconds: float = 300.0
    require_peer_reviewed: bool = False
    min_citation_count: int = 3
    max_budget_tokens: int = 16384
    preferred_format: str = "markdown"


@dataclass
class ResearchGoal:
    """Deconstructed research goal object."""

    raw_query: str
    title: str = ""
    domain: GoalDomain = GoalDomain.COMPUTER_SCIENCE
    priority: GoalPriority = GoalPriority.NORMAL
    primary_objectives: List[str] = field(default_factory=list)
    key_entities: List[str] = field(default_factory=list)
    constraints: ConstraintSpec = field(default_factory=ConstraintSpec)
    goal_id: str = field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.title:
            self.title = self.raw_query[:50].strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "raw_query": self.raw_query,
            "title": self.title,
            "domain": self.domain.value,
            "priority": self.priority.value,
            "primary_objectives": self.primary_objectives,
            "key_entities": self.key_entities,
            "created_at": self.created_at,
        }
