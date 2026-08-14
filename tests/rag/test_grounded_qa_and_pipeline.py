"""Integration tests for RAGPipeline, Incremental Re-indexing, and GroundedQAEngine."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base
from core.rag.pipeline import RAGPipeline, GroundedQAEngine
from infrastructure.database.repositories.project_repository import ProjectRepository
from infrastructure.database.repositories.user_repository import UserRepository


@pytest.fixture
def db_session():
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)
    session = manager.SessionLocal()
    
    # Create test user and workspace
    user_repo = UserRepository(session)
    user = user_repo.create({"email": "rag_pipeline@ara-research.org", "full_name": "RAG Pipeline User", "password_hash": "hash"})
    proj_repo = ProjectRepository(session)
    proj = proj_repo.create({"name": "Pipeline Proj", "owner_id": user.id})
    ws = proj_repo.create_workspace(proj.id, name="Pipeline WS")
    
    yield session, ws.id
    session.close()
    manager.drop_all_tables(Base)


def test_rag_pipeline_ingest_and_grounded_qa(db_session):
    session, workspace_id = db_session
    pipeline = RAGPipeline(session)

    md_content = b"# Quantum Supremacy\nSuperconducting qubits demonstrated quantum supremacy by executing random circuit sampling 10,000x faster than supercomputers."
    doc = pipeline.ingest_document(workspace_id=workspace_id, filename="quantum_supremacy.md", file_bytes=md_content, mime_type="text/markdown")

    assert doc.id is not None
    assert doc.title == "quantum_supremacy.md"

    # Test Grounded Q&A engine
    qa = GroundedQAEngine(session)
    result = qa.answer_question(workspace_id=workspace_id, question="How much faster was quantum supremacy demonstrated?", top_k=3)

    assert result["question"] == "How much faster was quantum supremacy demonstrated?"
    assert "retrieved research evidence" in result["answer"]
    assert len(result["citations"]) >= 1
    assert "quantum_supremacy.md" in result["evidence_sources"]


def test_rag_pipeline_reindex_document(db_session):
    session, workspace_id = db_session
    pipeline = RAGPipeline(session)

    md_content = b"# Machine Learning\nTransformers utilize self-attention mechanisms."
    doc = pipeline.ingest_document(workspace_id=workspace_id, filename="ml.md", file_bytes=md_content)

    reindexed_doc = pipeline.reindex_document(doc.id)
    assert reindexed_doc.id == doc.id
