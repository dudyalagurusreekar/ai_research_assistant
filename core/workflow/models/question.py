"""Research Question models — Hypothesis-driven sub-questions targeting specialized roles."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.collaboration.models.agent_info import AgentRole


class QuestionPriority(Enum):
    """Priority level of sub-question in execution DAG."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class QuestionStatus(Enum):
    """Status of research sub-question processing."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FAILED = "failed"


@dataclass
class ResearchQuestion:
    """Hypothesis-driven sub-question targeting specific research dimensions."""

    question_text: str
    hypothesis: str = ""
    target_role: AgentRole = AgentRole.RESEARCH
    required_capabilities: List[str] = field(default_factory=list)
    priority: QuestionPriority = QuestionPriority.NORMAL
    status: QuestionStatus = QuestionStatus.PENDING
    dependencies: List[str] = field(default_factory=list)  # question_ids
    question_id: str = field(default_factory=lambda: f"rq_{uuid.uuid4().hex[:8]}")
    execution_wave: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "hypothesis": self.hypothesis,
            "target_role": self.target_role.value,
            "status": self.status.value,
            "execution_wave": self.execution_wave,
            "dependencies": self.dependencies,
        }
