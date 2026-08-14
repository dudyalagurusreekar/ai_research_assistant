"""Integration tests for Sprint 11: Knowledge Graph and Long-Term Memory Platform."""

import pytest
import tempfile
from pathlib import Path

from core.knowledge_graph.engine import KnowledgeGraphEngine
from core.knowledge_graph.models.node import EntityType, EntityNode
from core.knowledge_graph.models.edge import RelationType, RelationEdge
from core.knowledge_graph.integration import (
    PlannerKnowledgeIntegration,
    OrchestratorKnowledgeIntegration,
    RAGKnowledgeIntegration,
    BrowserKnowledgeIntegration,
    ConnectorKnowledgeIntegration,
    ResearchWorkspaceKnowledgeIntegration,
)


@pytest.fixture
def temp_kg_engine():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = KnowledgeGraphEngine(storage_dir=tmpdir)
        yield engine


def test_e2e_text_ingestion_and_networkx(temp_kg_engine):
    engine = temp_kg_engine
    text = "PyTorch is an open source machine learning framework. BERT uses PyTorch for transformer model evaluation on SQuAD."
    nodes, edges = engine.ingest_text(text, source_id="paper_1")

    assert len(nodes) >= 2
    assert engine.graph.node_count >= 2

    # NetworkX export & Centrality
    nx_g = engine.graph.to_networkx()
    assert nx_g is not None
    assert nx_g.number_of_nodes() >= 2

    centrality = engine.compute_centrality(metric="degree")
    assert isinstance(centrality, dict)
    assert len(centrality) == engine.graph.node_count


def test_graph_snapshot_versioning_and_diff(temp_kg_engine):
    engine = temp_kg_engine
    engine.ingest_text("Transformer architecture built on PyTorch framework.", source_id="doc_v1")

    snap1 = engine.create_snapshot(tag="v1.0")
    assert snap1.version == 1
    assert snap1.node_count >= 1

    engine.ingest_text("GPT-4 model evaluated on HumanEval benchmark.", source_id="doc_v2")
    snap2 = engine.create_snapshot(tag="v2.0")
    assert snap2.node_count > snap1.node_count

    snapshots = engine.list_snapshots()
    assert len(snapshots) == 2

    diff = engine.compare_snapshots(snap1.snapshot_id, snap2.snapshot_id)
    assert len(diff.nodes_added) > 0


def test_long_term_and_episodic_memory_lifecycle(temp_kg_engine):
    engine = temp_kg_engine

    # Store user and project memory
    mem_u = engine.store_memory(
        scope="user",
        owner_id="usr_100",
        key="preferred_llm",
        value="User prefers Claude 3.5 Sonnet and Gemini 1.5 Pro. Contact email: test@example.com",
        importance=0.9,
    )
    assert mem_u.owner_id == "usr_100"

    mem_p = engine.store_memory(
        scope="project",
        owner_id="prj_500",
        key="target_accuracy",
        value="Target accuracy is 95% on benchmark dataset.",
        importance=0.85,
    )
    assert mem_p.owner_id == "prj_500"

    # Record episode
    ep = engine.record_episode(
        query="Benchmark model accuracy",
        plan_steps=["Extract data", "Run benchmark"],
        tools_used=["python_exec", "eval_tool"],
        outcome="Achieved 96.2% accuracy",
        success=True,
        user_id="usr_100",
        project_id="prj_500",
    )
    assert ep.success is True

    # PII Redaction
    redacted = engine.redact_memory_pii(mem_u.memory_id)
    assert redacted is True
    recalled = engine.recall_memory("user", "usr_100", "preferred_llm")
    assert "[REDACTED_EMAIL]" in recalled[0].value

    # User Privacy Hard Purge
    purge_res = engine.purge_user_privacy_data("usr_100")
    assert purge_res["memories_purged"] == 1
    assert purge_res["episodes_purged"] == 1
    assert len(engine.recall_memory("user", "usr_100")) == 0


def test_system_integrations(temp_kg_engine):
    engine = temp_kg_engine

    # Orchestrator Integration
    orch_adapter = OrchestratorKnowledgeIntegration(engine)
    ep = orch_adapter.record_agent_execution(
        query="Optimize graph database query",
        plan_steps=["Analyze index", "Add composite key"],
        tools_used=["db_analyzer"],
        outcome="Latency reduced by 40%",
        user_id="u123",
    )
    assert ep.episode_id is not None

    patterns = orch_adapter.retrieve_execution_patterns("Optimize graph query")
    assert len(patterns) >= 1

    # Research Workspace Integration
    ws_adapter = ResearchWorkspaceKnowledgeIntegration(engine)
    nodes_added = ws_adapter.ingest_research_note(
        note_id="note_001",
        note_title="Graph Neural Networks Research",
        content="GNN architecture improves link prediction on knowledge graphs.",
        project_id="prj_999",
    )
    assert nodes_added >= 1
    proj_mems = engine.recall_memory("project", "prj_999")
    assert len(proj_mems) == 1
