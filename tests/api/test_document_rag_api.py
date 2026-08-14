"""API Integration tests for Document Upload, MinIO Storage Sync, and RAG Hybrid Search."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import io
import pytest
from fastapi.testclient import TestClient
from services.api.app import app
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base
from infrastructure.database.seed import seed_database

from core.auth.dependencies import get_db_session

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)
    session = manager.SessionLocal()
    seed_database(session=session)

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db
    yield
    app.dependency_overrides.clear()
    session.close()
    manager.drop_all_tables(Base)


def get_auth_headers_and_workspace():
    client.post("/api/v1/auth/register", json={
        "email": "rag_user@ara-research.org",
        "password": "SecurePassword123!",
        "full_name": "RAG User",
    })
    token = client.post("/api/v1/auth/login", json={
        "email": "rag_user@ara-research.org",
        "password": "SecurePassword123!",
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = client.post("/api/v1/projects", json={"name": "RAG Proj"}, headers=headers).json()
    project_id = proj_res["data"]["id"]
    ws_res = client.get(f"/api/v1/projects/{project_id}/workspaces", headers=headers).json()
    workspace_id = ws_res["data"][0]["id"]

    return headers, workspace_id


def test_document_upload_and_hybrid_vector_search():
    headers, workspace_id = get_auth_headers_and_workspace()

    # 1. Upload Document File
    file_content = b"Quantum computing uses qubits and superposition to process information exponentially faster."
    files = {"file": ("quantum_intro.pdf", io.BytesIO(file_content), "application/pdf")}
    
    upload_res = client.post(f"/api/v1/workspaces/{workspace_id}/documents/upload", files=files, headers=headers)
    assert upload_res.status_code == 201
    doc_data = upload_res.json()["data"]
    assert doc_data["title"] == "quantum_intro.pdf"
    assert "sha256_hash" in doc_data

    # 2. List Workspace Documents
    docs_list = client.get(f"/api/v1/workspaces/{workspace_id}/documents", headers=headers)
    assert docs_list.status_code == 200
    assert len(docs_list.json()["data"]) == 1

    # 3. Hybrid Vector RAG Search (using gemini-embedding-2)
    search_res = client.post(f"/api/v1/workspaces/{workspace_id}/documents/search", json={
        "query": "What is quantum superposition?",
        "top_k": 3,
    }, headers=headers)
    assert search_res.status_code == 200
    results = search_res.json()["data"]
    assert len(results) >= 1
    assert "qubits" in results[0]["content"]
