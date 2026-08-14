"""API Integration tests for Enterprise RAG Platform (/api/v1/rag)."""

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
        "email": "rag_api@ara-research.org",
        "password": "SecurePassword123!",
        "full_name": "RAG API User",
    })
    token = client.post("/api/v1/auth/login", json={
        "email": "rag_api@ara-research.org",
        "password": "SecurePassword123!",
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = client.post("/api/v1/projects", json={"name": "RAG API Proj"}, headers=headers).json()
    ws_res = client.get(f"/api/v1/projects/{proj_res['data']['id']}/workspaces", headers=headers).json()
    workspace_id = ws_res["data"][0]["id"]

    return headers, workspace_id


def test_rag_api_ingest_search_query_and_reindex_flow():
    headers, workspace_id = get_auth_headers_and_workspace()

    # 1. Ingest Multi-Format Document
    md_content = b"# Deep Learning Frontiers\nConvolutional networks analyze spatial features while Vision Transformers model global dependencies."
    files = {"file": ("dl_frontiers.md", io.BytesIO(md_content), "text/markdown")}

    ingest_res = client.post(f"/api/v1/rag/documents/ingest?workspace_id={workspace_id}", files=files, headers=headers)
    assert ingest_res.status_code == 201
    doc_id = ingest_res.json()["data"]["id"]

    # 2. Hybrid Search
    search_res = client.post("/api/v1/rag/search", json={
        "workspace_id": workspace_id,
        "query": "Vision Transformers global dependencies",
        "top_k": 3,
    }, headers=headers)
    assert search_res.status_code == 200
    results = search_res.json()["data"]
    assert len(results) >= 1
    assert "citation" in results[0]

    # 3. Grounded Q&A Query
    qa_res = client.post("/api/v1/rag/query", json={
        "workspace_id": workspace_id,
        "question": "What model analyzes spatial features?",
        "top_k": 3,
    }, headers=headers)
    assert qa_res.status_code == 200
    qa_data = qa_res.json()["data"]
    assert "answer" in qa_data
    assert len(qa_data["citations"]) >= 1

    # 4. Inspect Chunks
    chunks_res = client.get(f"/api/v1/rag/documents/{doc_id}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    assert len(chunks_res.json()["data"]) >= 1

    # 5. Re-index Document
    reindex_res = client.post(f"/api/v1/rag/documents/{doc_id}/reindex", headers=headers)
    assert reindex_res.status_code == 200
    assert "re-indexed successfully" in reindex_res.json()["data"]["message"]
