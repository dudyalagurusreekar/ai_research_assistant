"""REST API tests for Data Intelligence & Analytics Router (/api/v1/analytics)."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from fastapi.testclient import TestClient
from services.api.app import app
from core.auth.jwt import jwt_manager
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base
from infrastructure.database.models.auth import User
from infrastructure.database.seed import seed_database
from core.auth.dependencies import get_db_session

client = TestClient(app)
_test_user_id = None


@pytest.fixture(autouse=True)
def setup_test_database():
    global _test_user_id
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)
    session = manager.SessionLocal()
    seed_database(session=session)

    user = session.query(User).filter(User.email == "admin@ara-research.org").first()
    _test_user_id = user.id if user else "usr_admin_001"

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
    token = jwt_manager.create_access_token(user_id=_test_user_id, email="admin@ara-research.org", role="Admin", tenant_id="tenant-default-001")
    return {"Authorization": f"Bearer {token}"}


def test_api_analytics_profile():
    headers = get_auth_headers()
    response = client.post("/api/v1/analytics/profile?dataset_name=test_analytics_ds", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["dataset_name"] == "test_analytics_ds"


def test_api_analytics_statistics():
    headers = get_auth_headers()
    response = client.post("/api/v1/analytics/statistics?dataset_name=test_analytics_ds", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True


def test_api_analytics_visualize():
    headers = get_auth_headers()
    response = client.post("/api/v1/analytics/visualize?dataset_name=test_analytics_ds", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert isinstance(json_data["data"], list)


def test_api_analytics_query_sql():
    headers = get_auth_headers()
    response = client.post(
        "/api/v1/analytics/query-sql",
        json={"natural_query": "What is the average off target rate?", "table_name": "test_analytics_ds"},
        headers=headers,
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "records" in json_data["data"]
