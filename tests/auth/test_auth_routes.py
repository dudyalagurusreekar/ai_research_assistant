"""Integration tests for FastAPI Authentication & Users REST API endpoints using TestClient."""

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
def setup_test_database():
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


def test_api_health_check():
    response = client.get("/health/liveness")
    assert response.status_code == 200
    res_json = response.json()
    status_val = res_json.get("status") or (res_json.get("data", {}) if isinstance(res_json.get("data"), dict) else {}).get("status")
    assert status_val == "healthy"



def test_api_register_and_login_flow():
    # 1. Register User
    reg_payload = {
        "email": "route_user@ara-research.org",
        "password": "RoutePassword123!",
        "full_name": "Route User",
        "role": "Researcher",
    }
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert "user_id" in data

    # 2. Login User
    login_payload = {
        "email": "route_user@ara-research.org",
        "password": "RoutePassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # 3. Get Current User Profile
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    profile = response.json()
    assert profile["email"] == "route_user@ara-research.org"

    # 4. Refresh Token Endpoint
    refresh_response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens

    # 5. Logout User Endpoint
    logout_response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
    assert logout_response.status_code == 200


def test_api_oauth_authorize_endpoint():
    response = client.get("/api/v1/auth/oauth/google/authorize?redirect_uri=http://localhost:3000/callback")
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "accounts.google.com" in data["authorization_url"]
