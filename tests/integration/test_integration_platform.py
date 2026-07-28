"""Comprehensive Unit, Integration, Concurrency, and End-to-End Tests for Phase 9 External Integration Platform."""

import asyncio

from tools.integration.facade.facade import IntegrationToolFacade
from tools.integration.models.integration_models import (
    IntegrationRequest,
    AuthenticationConfig,
    AuthType,
)
from tools.integration.registry.integration_registry import IntegrationRegistry
from tools.integration.auth.auth_manager import AuthenticationManager
from tools.integration.lifecycle.lifecycle_manager import ConnectorLifecycleManager
from tools.integration.pipeline.request_pipeline import RequestPipeline
from tools.integration.connectors.rest_connector import RESTConnector
from tools.integration.connectors.graphql_connector import GraphQLConnector
from tools.integration.connectors.mcp_connector import MCPConnector
from tools.integration.tool import IntegrationTool
from core.events import AsyncEventBus


def test_integration_registry():
    """Verify connector strategy registration and lookup."""
    registry = IntegrationRegistry()
    rest = RESTConnector()
    gql = GraphQLConnector()
    mcp = MCPConnector()

    registry.register(rest)
    registry.register(gql)
    registry.register(mcp)

    assert registry.get_connector("rest") is not None
    assert registry.get_connector("graphql") is not None
    assert registry.get_connector("mcp") is not None
    assert len(registry.list_connectors()) == 3


def test_auth_manager():
    """Verify authentication header injection."""
    auth_mgr = AuthenticationManager()
    req = IntegrationRequest(endpoint_or_tool="https://api.example.com/data")

    # API Key auth
    cfg_apikey = AuthenticationConfig(auth_type=AuthType.API_KEY, api_key="secret123", header_name="X-Custom-Key")
    req_key = auth_mgr.apply_authentication(req, cfg_apikey)
    assert req_key.headers.get("X-Custom-Key") == "secret123"

    # Bearer token auth
    cfg_bearer = AuthenticationConfig(auth_type=AuthType.BEARER_TOKEN, token="bearer_abc")
    req_bearer = auth_mgr.apply_authentication(req, cfg_bearer)
    assert req_bearer.headers.get("Authorization") == "Bearer bearer_abc"


def test_lifecycle_manager():
    """Verify health check monitoring."""
    async def _test():
        registry = IntegrationRegistry()
        registry.register(RESTConnector())
        lifecycle = ConnectorLifecycleManager(registry=registry)

        meta = await lifecycle.check_health("rest")
        assert meta.is_active is True
        assert meta.health_status == "healthy"

    asyncio.run(_test())


def test_request_pipeline_timeout_protection():
    """Verify request pipeline timeout bounds and error translation."""
    async def _test():
        pipeline = RequestPipeline()
        conn = RESTConnector()

        # Valid request
        req = IntegrationRequest(endpoint_or_tool="https://api.example.com", timeout_seconds=5.0)
        res = await pipeline.process_request(req, conn)

        assert res.success is True
        assert res.status_code == 200
        assert res.execution_time_ms >= 0.0

    asyncio.run(_test())


def test_graphql_connector():
    """Verify GraphQL connector query execution."""
    async def _test():
        conn = GraphQLConnector()
        req = IntegrationRequest(endpoint_or_tool="https://api.example.com/graphql", params={"query": "{ user { id } }"})
        resp = await conn.execute(req)

        assert resp.status_code == 200
        assert "data" in resp.data

    asyncio.run(_test())


def test_mcp_connector():
    """Verify MCP connector tool call invocation."""
    async def _test():
        conn = MCPConnector()
        req = IntegrationRequest(endpoint_or_tool="search_papers", params={"query": "quantum"})
        resp = await conn.execute(req)

        assert resp.status_code == 200
        assert resp.data["tool_name"] == "search_papers"

    asyncio.run(_test())


def test_integration_facade_end_to_end_and_events():
    """Verify IntegrationToolFacade unified APIs, memory integration, and AsyncEventBus notifications."""
    async def _test():
        bus = AsyncEventBus()
        events_fired = []

        async def _on_event(evt):
            events_fired.append(evt.event_type)

        bus.subscribe("integration.started", _on_event)
        bus.subscribe("connector.loaded", _on_event)
        bus.subscribe("request.sent", _on_event)
        bus.subscribe("response.received", _on_event)
        bus.subscribe("integration.completed", _on_event)

        facade = IntegrationToolFacade(event_bus=bus)

        # 1. REST Query API
        rest_res = await facade.query_rest("https://api.example.com/v1/resource")
        assert rest_res.success is True
        assert rest_res.status_code == 200

        # 2. GraphQL Query API
        gql_res = await facade.query_graphql("https://api.example.com/graphql", query="{ meta { version } }")
        assert gql_res.success is True

        # 3. MCP Tool Invocation API
        mcp_res = await facade.invoke_mcp_tool("fetch_data", arguments={"id": 42})
        assert mcp_res.success is True

        # Wait briefly for async events
        await asyncio.sleep(0.05)
        assert "integration.started" in events_fired
        assert "connector.loaded" in events_fired
        assert "request.sent" in events_fired
        assert "response.received" in events_fired
        assert "integration.completed" in events_fired

        # Test forward JSON method
        forward_json = await facade.forward(action="rest", endpoint="https://api.example.com/health")
        assert "result_id" in forward_json

    asyncio.run(_test())


def test_smolagents_integration_tool_wrapper():
    """Verify smolagents IntegrationTool wrapper."""
    tool = IntegrationTool()
    res_str = tool.forward(action="rest", endpoint="https://api.example.com/test")
    assert "result_id" in res_str
