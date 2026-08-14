"""Components package for multi-agent collaboration framework."""

from core.collaboration.components.conflict_resolution import ConflictResolutionEngine
from core.collaboration.components.memory import CollaborationMemory
from core.collaboration.components.orchestrator import MultiAgentOrchestrator
from core.collaboration.components.registry import AgentRegistry
from core.collaboration.components.workspace import SharedWorkspace

__all__ = [
    "AgentRegistry",
    "SharedWorkspace",
    "CollaborationMemory",
    "ConflictResolutionEngine",
    "MultiAgentOrchestrator",
]
