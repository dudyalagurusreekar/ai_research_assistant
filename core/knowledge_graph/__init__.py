"""ARA v1.0 — Knowledge Graph, Semantic Memory, and Long-Term Memory Platform (Sprint 11)."""

from core.knowledge_graph.components import (
    EntityExtractor,
    GraphBuilder,
    GraphMemoryManager,
    GraphQueryService,
    GraphReasoningEngine,
    GraphStorage,
    KnowledgeSynchronizer,
    RelationshipExtractor,
    SemanticRetrievalEngine,
)
from core.knowledge_graph.components.episodic_memory import EpisodicMemoryEngine, Episode
from core.knowledge_graph.components.long_term_memory import LongTermMemoryStore, MemoryEntry, MemoryScope, DataSensitivity
from core.knowledge_graph.components.memory_policies import MemoryPolicyEngine
from core.knowledge_graph.engine import KnowledgeGraphEngine
from core.knowledge_graph.integration import (
    BrowserKnowledgeIntegration,
    CollaborationKnowledgeIntegration,
    ConnectorKnowledgeIntegration,
    DataKnowledgeIntegration,
    LearningKnowledgeIntegration,
    MemorySystemKnowledgeIntegration,
    OrchestratorKnowledgeIntegration,
    PlannerKnowledgeIntegration,
    RAGKnowledgeIntegration,
    ReflectionKnowledgeIntegration,
    ResearchWorkspaceKnowledgeIntegration,
)
from core.knowledge_graph.models import (
    EntityNode,
    EntityType,
    ExtractionProvenance,
    GraphDiff,
    GraphPath,
    GraphQuery,
    GraphQueryResult,
    GraphSnapshot,
    KnowledgeGraph,
    KnowledgeGraphMetrics,
    RelationEdge,
    RelationType,
    SearchMode,
    SourceType,
    VersionInfo,
)
from core.knowledge_graph.models.evidence import EvidenceRecord, EvidenceSourceType

__all__ = [
    # Facade Engine
    "KnowledgeGraphEngine",
    # Components
    "EntityExtractor",
    "RelationshipExtractor",
    "GraphBuilder",
    "GraphStorage",
    "SemanticRetrievalEngine",
    "GraphReasoningEngine",
    "GraphMemoryManager",
    "KnowledgeSynchronizer",
    "GraphQueryService",
    # Sprint 11 Components
    "EpisodicMemoryEngine",
    "Episode",
    "LongTermMemoryStore",
    "MemoryEntry",
    "MemoryScope",
    "DataSensitivity",
    "MemoryPolicyEngine",
    "EvidenceRecord",
    "EvidenceSourceType",
    "GraphSnapshot",
    "GraphDiff",
    "VersionInfo",
    # Models
    "EntityNode",
    "EntityType",
    "RelationEdge",
    "RelationType",
    "KnowledgeGraph",
    "KnowledgeGraphMetrics",
    "ExtractionProvenance",
    "SourceType",
    "GraphQuery",
    "GraphQueryResult",
    "GraphPath",
    "SearchMode",
    # Integrations
    "PlannerKnowledgeIntegration",
    "ReflectionKnowledgeIntegration",
    "LearningKnowledgeIntegration",
    "DataKnowledgeIntegration",
    "CollaborationKnowledgeIntegration",
    "MemorySystemKnowledgeIntegration",
    "BrowserKnowledgeIntegration",
    "ConnectorKnowledgeIntegration",
    "RAGKnowledgeIntegration",
    "OrchestratorKnowledgeIntegration",
    "ResearchWorkspaceKnowledgeIntegration",
]

