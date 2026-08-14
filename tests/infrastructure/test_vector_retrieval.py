import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base, Project, Workspace
from infrastructure.database.repositories import DocumentRepository, ProjectRepository, UserRepository


@pytest.fixture
def db_session():
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)
    with manager.get_session() as session:
        yield session
    manager.drop_all_tables(Base)


def test_document_ingestion_and_vector_chunks(db_session):
    user = UserRepository(db_session).create({"email": "doc@ara.local", "full_name": "Doc User", "password_hash": "h"})
    project = ProjectRepository(db_session).create({"name": "Doc Project", "owner_id": user.id})
    workspace = ProjectRepository(db_session).create_workspace(project.id, name="Doc WS")

    doc_repo = DocumentRepository(db_session)
    doc = doc_repo.create({
        "workspace_id": workspace.id,
        "title": "Quantum Computing Survey.pdf",
        "mime_type": "application/pdf",
        "file_size": 10240,
        "storage_path": "ara-uploads/quantum.pdf",
        "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    })
    assert doc.id is not None

    chunks_data = [
        {"content": "Quantum supremacy was demonstrated using superconducting qubits.", "token_count": 10, "embedding": [0.1] * 1536},
        {"content": "Quantum error correction mitigates decoherence in fault-tolerant quantum algorithms.", "token_count": 12, "embedding": [0.2] * 1536},
    ]
    chunks = doc_repo.add_chunks(doc.id, chunks_data)
    assert len(chunks) == 2
    assert chunks[0].content.startswith("Quantum supremacy")

    # Test vector search fallback
    results = doc_repo.vector_search(query_embedding=[0.1] * 1536, workspace_id=workspace.id, top_k=2)
    assert len(results) == 2
    assert results[0][0].document_id == doc.id
