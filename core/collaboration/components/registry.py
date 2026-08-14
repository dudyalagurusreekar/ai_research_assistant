"""Agent Registry — Dynamic registration, discovery, and capability resolution for specialized agents."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional, Type

from core.collaboration.models.agent_info import (
    AgentCapability,
    AgentMetadata,
    AgentRole,
    AgentStatus,
)
from utils.logger import get_logger

logger = get_logger("AgentRegistry")


class AgentRegistry:
    """Thread-safe registry managing agent lifecycle, discovery, and capability matching."""

    _instance: Optional[AgentRegistry] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._agents: Dict[str, Any] = {}  # agent_id -> BaseSpecializedAgent instance
        self._metadata: Dict[str, AgentMetadata] = {}  # agent_id -> AgentMetadata
        self._role_index: Dict[AgentRole, List[str]] = {role: [] for role in AgentRole}
        self._registry_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> AgentRegistry:
        """Singleton instance accessor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register_agent(self, agent_instance: Any, metadata: Optional[AgentMetadata] = None) -> AgentMetadata:
        """Register a specialized agent instance in the registry."""
        with self._registry_lock:
            agent_id = getattr(agent_instance, "agent_id", None)
            if not agent_id and metadata:
                agent_id = metadata.agent_id
            elif not agent_id:
                raise ValueError("Agent instance must have an agent_id or metadata must be provided")

            if metadata is None:
                metadata = getattr(agent_instance, "metadata", None)
                if metadata is None:
                    role = getattr(agent_instance, "role", AgentRole.RESEARCH)
                    name = getattr(agent_instance, "name", f"Agent_{agent_id}")
                    metadata = AgentMetadata(agent_id=agent_id, name=name, role=role)

            self._agents[agent_id] = agent_instance
            self._metadata[agent_id] = metadata

            if agent_id not in self._role_index[metadata.role]:
                self._role_index[metadata.role].append(agent_id)

            logger.info(f"Registered agent '{metadata.name}' ({agent_id}) with role {metadata.role.value}")
            return metadata

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent by ID."""
        with self._registry_lock:
            if agent_id in self._agents:
                metadata = self._metadata[agent_id]
                if agent_id in self._role_index[metadata.role]:
                    self._role_index[metadata.role].remove(agent_id)
                del self._agents[agent_id]
                del self._metadata[agent_id]
                logger.info(f"Unregistered agent {agent_id}")
                return True
            return False

    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Retrieve an agent instance by ID."""
        with self._registry_lock:
            return self._agents.get(agent_id)

    def get_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """Retrieve metadata for an agent by ID."""
        with self._registry_lock:
            return self._metadata.get(agent_id)

    def list_agents(self, role: Optional[AgentRole] = None, status: Optional[AgentStatus] = None) -> List[AgentMetadata]:
        """List registered agents filtered by role or status."""
        with self._registry_lock:
            results = []
            for meta in self._metadata.values():
                if role and meta.role != role:
                    continue
                if status and meta.status != status:
                    continue
                results.append(meta)
            return results

    def find_best_agent(self, role: AgentRole, required_capabilities: Optional[List[str]] = None) -> Optional[Any]:
        """Resolve the optimal available agent matching role and required capabilities."""
        with self._registry_lock:
            candidate_ids = self._role_index.get(role, [])
            if not candidate_ids:
                return None

            best_agent = None
            highest_score = -1

            for agent_id in candidate_ids:
                meta = self._metadata.get(agent_id)
                if not meta or meta.status == AgentStatus.OFFLINE:
                    continue

                score = 0
                if meta.status == AgentStatus.IDLE:
                    score += 10

                if required_capabilities:
                    cap_matches = sum(1 for cap in required_capabilities if meta.has_capability(cap))
                    score += cap_matches * 5
                else:
                    score += 5

                if score > highest_score:
                    highest_score = score
                    best_agent = self._agents.get(agent_id)

            return best_agent

    def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update the operational status of an agent."""
        with self._registry_lock:
            if agent_id in self._metadata:
                self._metadata[agent_id].status = status
                logger.debug(f"Agent {agent_id} status updated to {status.value}")
                return True
            return False

    def clear(self) -> None:
        """Clear all registered agents."""
        with self._registry_lock:
            self._agents.clear()
            self._metadata.clear()
            self._role_index = {role: [] for role in AgentRole}
