"""API Integration tests for Research Sessions & Conversations (/api/v1/research)."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

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
        "email": "researcher@ara-research.org",
        "password": "SecurePassword123!",
        "full_name": "Research User",
    })
    token = client.post("/api/v1/auth/login", json={
        "email": "researcher@ara-research.org",
        "password": "SecurePassword123!",
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = client.post("/api/v1/projects", json={"name": "Research Proj"}, headers=headers).json()
    project_id = proj_res["data"]["id"]
    ws_res = client.get(f"/api/v1/projects/{project_id}/workspaces", headers=headers).json()
    workspace_id = ws_res["data"][0]["id"]

    return headers, workspace_id


def test_research_session_and_messages_stream():
    headers, workspace_id = get_auth_headers_and_workspace()

    # 1. Create Research Session
    session_res = client.post("/api/v1/research/sessions", json={
        "workspace_id": workspace_id,
        "title": "Deep Learning Survey",
        "objective": "Summarize latest Transformer architectures",
    }, headers=headers)
    assert session_res.status_code == 201
    session_id = session_res.json()["data"]["id"]

    # 2. Create Conversation Thread
    conv_res = client.post(f"/api/v1/research/sessions/{session_id}/conversations", json={"title": "Primary Chat"}, headers=headers)
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["data"]["id"]

    # 3. Add Messages
    msg1 = client.post(f"/api/v1/conversations/{conv_id}/messages", json={
        "sender_type": "USER",
        "content": "What are the key advances in attention mechanisms?",
    }, headers=headers)
    assert msg1.status_code == 201

    msg2 = client.post(f"/api/v1/conversations/{conv_id}/messages", json={
        "sender_type": "ASSISTANT",
        "content": "FlashAttention reduces I/O complexity to O(N).",
    }, headers=headers)
    assert msg2.status_code == 201

    # 4. List Messages
    list_msgs = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    assert list_msgs.status_code == 200
    assert len(list_msgs.json()["data"]) == 2
