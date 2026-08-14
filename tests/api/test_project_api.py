"""API Integration tests for Projects & Workspaces (/api/v1/projects)."""

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


def get_auth_headers():
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "project_owner@ara-research.org",
        "password": "SecurePassword123!",
        "full_name": "Project Owner",
    })
    token = client.post("/api/v1/auth/login", json={
        "email": "project_owner@ara-research.org",
        "password": "SecurePassword123!",
    }).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_project_crud_and_workspace_creation():
    headers = get_auth_headers()

    # 1. Create Project
    res = client.post("/api/v1/projects", json={"name": "Quantum AI Project", "description": "Survey of QML"}, headers=headers)
    assert res.status_code == 201
    env = res.json()
    assert env["success"] is True
    project_id = env["data"]["id"]

    # 2. List Projects
    list_res = client.get("/api/v1/projects", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 3. Create Workspace
    ws_res = client.post(f"/api/v1/projects/{project_id}/workspaces", json={"name": "Experiments WS"}, headers=headers)
    assert ws_res.status_code == 201
    assert ws_res.json()["data"]["name"] == "Experiments WS"

    # 4. List Workspaces
    ws_list = client.get(f"/api/v1/projects/{project_id}/workspaces", headers=headers)
    assert ws_list.status_code == 200
    assert len(ws_list.json()["data"]) >= 2  # Default + Experiments WS
