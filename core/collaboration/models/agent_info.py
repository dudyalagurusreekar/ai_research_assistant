"""Agent Information models — Roles, Capabilities, Status, and Metadata."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentRole(Enum):
    """Specialized agent roles supported in the collaboration framework."""

    RESEARCH = "research"
    DATA = "data"
    CODE = "code"
    WRITER = "writer"
    REVIEWER = "reviewer"


class AgentStatus(Enum):
    """Lifecycle availability status of a registered agent."""

    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    OFFLINE = "offline"


@dataclass
class AgentCapability:
    """Represents a specific skill or tool capability possessed by an agent."""

    name: str
    description: str = ""
    tools_required: List[str] = field(default_factory=list)
    domain_expertise: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "tools_required": self.tools_required,
            "domain_expertise": self.domain_expertise,
        }


@dataclass
class AgentMetadata:
    """Registration and state metadata for a specialized agent."""

    agent_id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: str = ""
    role: AgentRole = AgentRole.RESEARCH
    capabilities: List[AgentCapability] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    max_concurrent_tasks: int = 1
    current_task_ids: List[str] = field(default_factory=list)
    created_at: str = ""
    version: str = "2.5.0"

    def has_capability(self, capability_name: str) -> bool:
        """Check if agent possesses a capability by name."""
        return any(c.name.lower() == capability_name.lower() for c in self.capabilities)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role.value,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "status": self.status.value,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "current_task_ids": self.current_task_ids,
            "version": self.version,
        }
