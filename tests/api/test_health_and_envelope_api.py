"""API Integration tests for Correlation ID propagation, JSON Response Envelope consistency, and Health Probes."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from fastapi.testclient import TestClient
from services.api.app import app
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base

from core.auth.dependencies import get_db_session

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)
    session = manager.SessionLocal()

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


def test_health_liveness_and_readiness_probes():
    # Liveness
    live_res = client.get("/health/liveness")
    assert live_res.status_code == 200
    env = live_res.json()
    assert env["success"] is True
    assert env["data"]["status"] == "healthy"

    # Readiness
    ready_res = client.get("/health/readiness")
    assert ready_res.status_code == 200
    r_env = ready_res.json()
    assert r_env["data"]["status"] in ["ready", "degraded"]


def test_correlation_id_header_injection_and_propagation():
    custom_cid = "req-custom-trace-999"
    res = client.get("/health/liveness", headers={"X-Correlation-ID": custom_cid})
    assert res.status_code == 200
    assert res.headers.get("X-Correlation-ID") == custom_cid
    assert res.json()["correlation_id"] == custom_cid


def test_standardized_error_envelope_formatting():
    # Trigger 404 endpoint
    res = client.get("/api/v1/non_existent_route")
    assert res.status_code == 404
    env = res.json()
    assert env["success"] is False
    assert env["data"] is None
    assert env["error"]["code"] == "HTTP_404"
