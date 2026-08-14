"""Unit tests for Sprint 12 Universal Connector SDK (BaseConnector, OAuthConnector, DatabaseConnector, StorageConnector, Validator, Decorators)."""

import pytest
import asyncio

from tools.integration.sdk.base_connector import BaseConnector
from tools.integration.sdk.oauth_connector import OAuthConnector
from tools.integration.sdk.database_connector_base import DatabaseConnector
from tools.integration.sdk.storage_connector_base import StorageConnector
from tools.integration.sdk.validator import ConnectorValidator, ConnectorValidationError
from tools.integration.sdk.decorators import connector, rate_limited, audit_logged, cacheable
from tools.integration.models.integration_models import IntegrationRequest, IntegrationResponse, ProtocolType


class DummyConnector(BaseConnector):
    def __init__(self):
        super().__init__(name="dummy", protocol=ProtocolType.REST)

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        return IntegrationResponse(status_code=200, data={"echo": request.endpoint_or_tool})


def test_base_connector_lifecycle():
    async def _test():
        conn = DummyConnector()
        assert conn.connector_name == "dummy"
        assert conn.protocol == ProtocolType.REST

        initialized = await conn.initialize()
        assert initialized is True

        health = await conn.check_health()
        assert health.is_active is True
        assert health.health_status == "healthy"

        req = IntegrationRequest(endpoint_or_tool="ping")
        res = await conn.execute_normalized(req)
        assert res.success is True
        assert res.data["echo"] == "ping"

        await conn.shutdown()

    asyncio.run(_test())


def test_oauth_connector_pkce_and_tokens():
    oauth = OAuthConnector(name="test_oauth", auth_url="https://auth.example.com", token_url="https://token.example.com")
    pkce = oauth.generate_pkce_pair()
    assert "code_verifier" in pkce
    assert "code_challenge" in pkce
    assert pkce["code_challenge_method"] == "S256"

    auth_url = oauth.get_authorization_url(client_id="client_123", redirect_uri="http://localhost/callback")
    assert "client_id=client_123" in auth_url
    assert "code_challenge=" in auth_url


def test_connector_validator():
    cfg = {"client_id": "123", "secret": "abc"}
    assert ConnectorValidator.validate_config(cfg, ["client_id", "secret"]) is True

    with pytest.raises(ConnectorValidationError):
        ConnectorValidator.validate_config(cfg, ["client_id", "missing_key"])

    assert ConnectorValidator.validate_endpoint_url("https://api.github.com/user") is True

    with pytest.raises(ConnectorValidationError):
        ConnectorValidator.validate_endpoint_url("ftp://unsupported.com")


def test_decorators():
    async def _test():
        call_count = 0

        class DecoratedService:
            @cacheable(ttl_seconds=60)
            async def cached_method(self, val: str):
                nonlocal call_count
                call_count += 1
                return f"processed_{val}"

        srv = DecoratedService()
        r1 = await srv.cached_method("hello")
        r2 = await srv.cached_method("hello")

        assert r1 == "processed_hello"
        assert r2 == "processed_hello"
        assert call_count == 1

    asyncio.run(_test())
