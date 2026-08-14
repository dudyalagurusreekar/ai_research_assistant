"""ARA Version 2.5 — Multi-Agent Collaboration Framework (Sprint 7)."""

from core.collaboration.agents import (
    BaseSpecializedAgent,
    SpecializedCodeAgent,
    SpecializedDataAgent,
    SpecializedResearchAgent,
    SpecializedReviewerAgent,
    SpecializedWriterAgent,
)
from core.collaboration.components import (
    AgentRegistry,
    CollaborationMemory,
    ConflictResolutionEngine,
    MultiAgentOrchestrator,
    SharedWorkspace,
)
from core.collaboration.engine import MultiAgentCollaborationEngine
from core.collaboration.integration import (
    LearningCollaborationIntegration,
    PlannerCollaborationIntegration,
    ReflectionCollaborationIntegration,
)
from core.collaboration.models import (
    AgentCapability,
    AgentMessage,
    AgentMetadata,
    AgentMetrics,
    AgentOutput,
    AgentRole,
    AgentStatus,
    CollaborationContext,
    CollaborationStatus,
    ConflictRecord,
    ConflictType,
    ExecutionMode,
    MessagePriority,
    MessageType,
    OrchestratorMetrics,
    ResolutionStrategy,
    TaskAssignment,
)

__all__ = [
    # Engine & Facade
    "MultiAgentCollaborationEngine",
    # Agents
    "BaseSpecializedAgent",
    "SpecializedResearchAgent",
    "SpecializedDataAgent",
    "SpecializedCodeAgent",
    "SpecializedWriterAgent",
    "SpecializedReviewerAgent",
    # Components
    "AgentRegistry",
    "SharedWorkspace",
    "CollaborationMemory",
    "ConflictResolutionEngine",
    "MultiAgentOrchestrator",
    # Models
    "AgentCapability",
    "AgentMetadata",
    "AgentRole",
    "AgentStatus",
    "AgentMessage",
    "MessageType",
    "MessagePriority",
    "ConflictRecord",
    "ConflictType",
    "ResolutionStrategy",
    "AgentOutput",
    "CollaborationContext",
    "CollaborationStatus",
    "ExecutionMode",
    "TaskAssignment",
    "AgentMetrics",
    "OrchestratorMetrics",
    # Integrations
    "PlannerCollaborationIntegration",
    "ReflectionCollaborationIntegration",
    "LearningCollaborationIntegration",
]
