"""API Integration tests for Reports & Browser Automation endpoints."""

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


def get_auth_headers_and_session():
    client.post("/api/v1/auth/register", json={
        "email": "report_user@ara-research.org",
        "password": "SecurePassword123!",
        "full_name": "Report User",
    })
    token = client.post("/api/v1/auth/login", json={
        "email": "report_user@ara-research.org",
        "password": "SecurePassword123!",
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = client.post("/api/v1/projects", json={"name": "Report Proj"}, headers=headers).json()
    ws_res = client.get(f"/api/v1/projects/{proj_res['data']['id']}/workspaces", headers=headers).json()
    ws_id = ws_res["data"][0]["id"]

    sess_res = client.post("/api/v1/research/sessions", json={
        "workspace_id": ws_id,
        "title": "Quantum Report Session",
        "objective": "Objective",
    }, headers=headers).json()

    return headers, sess_res["data"]["id"]


def test_report_generation_and_presigned_download():
    headers, session_id = get_auth_headers_and_session()

    # 1. Generate Report
    report_res = client.post(f"/api/v1/research/sessions/{session_id}/reports", json={
        "title": "Quantum Computing Frontiers",
        "summary": "This report details quantum supremacy and error correction.",
        "sections": [
            {"title": "Hardware Architectures", "content": "Superconducting qubits and ion traps."},
            {"title": "Algorithms", "content": "Shor's and Grover's algorithms."},
        ],
        "format": "markdown",
    }, headers=headers)
    assert report_res.status_code == 201
    report_id = report_res.json()["data"]["id"]

    # 2. Get Report Details
    det_res = client.get(f"/api/v1/reports/{report_id}", headers=headers)
    assert det_res.status_code == 200
    assert len(det_res.json()["data"]["sections"]) == 2

    # 3. Download Link
    dl_res = client.get(f"/api/v1/reports/{report_id}/download", headers=headers)
    assert dl_res.status_code == 200
    assert "download_url" in dl_res.json()["data"]


def test_browser_automation_session_and_screenshot():
    headers, _ = get_auth_headers_and_session()

    # 1. Create Browser Session
    bs_res = client.post("/api/v1/browser/sessions", json={"initial_url": "https://arxiv.org"}, headers=headers)
    assert bs_res.status_code == 201
    session_id = bs_res.json()["data"]["id"]

    # 2. Log Action
    nav_res = client.post(f"/api/v1/browser/sessions/{session_id}/navigate", json={
        "action_type": "NAVIGATE",
        "value": "https://arxiv.org/abs/2301.00001",
    }, headers=headers)
    assert nav_res.status_code == 200

    # 3. Screenshot Capture
    ss_res = client.post(f"/api/v1/browser/sessions/{session_id}/screenshot", json={
        "url": "https://arxiv.org/abs/2301.00001",
    }, headers=headers)
    assert ss_res.status_code == 200
    assert "storage_path" in ss_res.json()["data"]
