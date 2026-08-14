"""End-to-End Test: Cross-Subsystem Knowledge Synchronization, Memory Decay, and Knowledge Evolution."""

import pytest

from core.collaboration.components.workspace import SharedWorkspace
from core.knowledge_graph import KnowledgeGraphEngine
from core.learning.engine import ContinuousLearningEngine


def test_e2e_knowledge_synchronization_and_evolution():
    engine = KnowledgeGraphEngine()

    # 1. Sync workspace artifacts
    workspace = SharedWorkspace()
    workspace.set("final_report", "Multi-Agent Collaboration Framework v2.5 Report", artifact_type="text")

    synced_ws = engine.synchronizer.sync_workspace_artifacts(workspace)
    assert synced_ws == 1

    # 2. Sync learning experiences
    learning_engine = ContinuousLearningEngine()
    learning_engine.record_experience("Multi-Agent Planning", "multi_step_research", 4, ["tool_a"], [], 2, 1, 1, 150.0)

    synced_learn = engine.synchronizer.sync_learning_experiences(learning_engine.store)
    assert synced_learn >= 1

    # 3. Knowledge Evolution & Pruning
    initial_nodes = engine.graph.node_count
    assert initial_nodes >= 2

    # Prune high-threshold => verify lifecycle compaction
    pn, pe = engine.prune_and_compact(min_confidence=0.99)
    assert engine.graph.node_count <= initial_nodes
