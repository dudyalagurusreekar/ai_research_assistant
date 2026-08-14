"""API Integration tests for Workflows, Execution runs, System Settings, and User Preferences."""

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
    client.post("/api/v1/auth/register", json={
        "email": "wf_user@ara-research.org",
        "password": "SecurePassword123!",
        "full_name": "Workflow User",
    })
    token = client.post("/api/v1/auth/login", json={
        "email": "wf_user@ara-research.org",
        "password": "SecurePassword123!",
    }).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_workflow_dag_creation_and_execution():
    headers = get_auth_headers()

    # 1. Create Workflow Template
    dag_def = {
        "nodes": [
            {"id": "n1", "tool": "arxiv_search", "params": {"query": "transformers"}},
            {"id": "n2", "tool": "summarizer", "depends_on": ["n1"]},
        ]
    }
    wf_res = client.post("/api/v1/workflows", json={"name": "Literature Pipeline", "dag_definition": dag_def}, headers=headers)
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["data"]["id"]

    # 2. List Workflows
    list_wf = client.get("/api/v1/workflows", headers=headers)
    assert list_wf.status_code == 200
    assert len(list_wf.json()["data"]) == 1

    # 3. Execute Workflow DAG
    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"input_params": {"max_results": 5}}, headers=headers)
    assert exec_res.status_code == 201
    exec_id = exec_res.json()["data"]["execution_id"]

    # 4. Query Execution Run Status
    status_res = client.get(f"/api/v1/workflow-executions/{exec_id}", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"].lower() == "running"


def test_system_settings_and_user_preferences():
    headers = get_auth_headers()

    # 1. System Settings
    sys_res = client.get("/api/v1/settings/system", headers=headers)
    assert sys_res.status_code == 200
    assert isinstance(sys_res.json()["data"], dict)

    # 2. Get User Preferences
    pref_res = client.get("/api/v1/settings/user", headers=headers)
    assert pref_res.status_code == 200
    assert pref_res.json()["data"]["theme"] == "dark"

    # 3. Patch User Preferences
    patch_res = client.patch("/api/v1/settings/user", json={"preferences": {"theme": "light", "language": "en"}}, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["theme"] == "light"
    assert patch_res.json()["data"]["language"] == "en"
