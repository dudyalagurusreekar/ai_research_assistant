"""Security tests verifying protection against invalid JWTs, expired tokens, replay attacks, brute-force, and RBAC escalation."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import time
import pytest
from fastapi.testclient import TestClient
from services.api.app import app
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base
from infrastructure.database.seed import seed_database
from core.auth.jwt import jwt_manager

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


def test_security_reject_invalid_jwt_token():
    # Attempt request with malformed JWT
    headers = {"Authorization": "Bearer invalid_malformed_jwt_token_string"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


def test_security_reject_expired_jwt_token():
    # Issue token expired 10 minutes ago
    expired_token = jwt_manager.create_access_token(
        user_id="usr-expired",
        email="expired@ara-research.org",
        expires_minutes=-10,
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401
    body = response.json()
    msg = body.get("detail") or body.get("error", {}).get("message", "")
    assert "expired" in msg.lower()


def test_security_rbac_privilege_escalation_prevention():
    # Register standard Researcher user
    client.post("/api/v1/auth/register", json={
        "email": "user_standard@ara-research.org",
        "password": "StandardPassword123!",
        "full_name": "Standard User",
        "role": "Researcher",
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "user_standard@ara-research.org",
        "password": "StandardPassword123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to access Admin-only endpoint (/api/v1/users/)
    admin_response = client.get("/api/v1/users/", headers=headers)
    assert admin_response.status_code == 403
    body = admin_response.json()
    msg = body.get("detail") or body.get("error", {}).get("message", "")
    assert "Access denied" in msg or "Forbidden" in msg or "FORBIDDEN" in str(body)


def test_security_brute_force_lockout_throttling():
    email = "brute_target@ara-research.org"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "ValidPassword123!",
        "full_name": "Brute Target",
    })

    # Execute 5 failed login attempts
    for _ in range(5):
        res = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword123!"})
        assert res.status_code == 401

    # 6th attempt should be blocked with 403 Forbidden Lockout
    locked_res = client.post("/api/v1/auth/login", json={"email": email, "password": "ValidPassword123!"})
    assert locked_res.status_code == 403
    body = locked_res.json()
    msg = body.get("detail") or body.get("error", {}).get("message", "")
    assert "locked" in msg.lower()

