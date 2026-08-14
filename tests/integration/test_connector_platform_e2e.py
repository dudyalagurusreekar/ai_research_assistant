"""End-to-End research workflow tests for Sprint 12 Universal Connector & Integration Platform."""

import pytest
import asyncio

from tools.integration.engine import UniversalConnectorPlatform
from tools.integration.facade.facade import IntegrationToolFacade
from tools.integration.permissions.permission_manager import PermissionAction
from tools.integration.tool import IntegrationTool


def test_universal_connector_platform_e2e_workflow():
    async def _test():
        platform = UniversalConnectorPlatform()
        await platform.initialize()

        # 1. Assign Role to Principal
        platform.permission_manager.assign_role("lead_analyst", "analyst")

        # 2. Execute Gmail Query via Platform Engine
        res_gmail = await platform.execute(
            principal="lead_analyst",
            connector_name="gmail",
            method="SEARCH",
            params={"q": "Research Update"},
            action_type=PermissionAction.READ,
        )
        assert res_gmail.success is True
        assert res_gmail.status_code == 200
        assert len(res_gmail.data["messages"]) >= 1

        # 3. Execute GitHub Query via Platform Engine
        res_github = await platform.execute(
            principal="lead_analyst",
            connector_name="github",
            method="SEARCH_ISSUES",
            params={"query": "Universal"},
            action_type=PermissionAction.READ,
        )
        assert res_github.success is True
        assert res_github.status_code == 200

        # 4. Verify Knowledge Graph ingestion from connectors
        kg_summary = platform.knowledge_graph_bridge.get_graph_summary()
        assert kg_summary["nodes_count"] >= 2

        # 5. Verify Metrics Engine tracking
        metrics_json = platform.metrics.export_json()
        assert "gmail" in metrics_json
        assert "github" in metrics_json

    asyncio.run(_test())


def test_facade_backward_compatibility_and_sprint12_actions():
    async def _test():
        facade = IntegrationToolFacade()

        # 1. Legacy REST action
        rest_str = await facade.forward(action="rest", endpoint="https://api.example.com/v1/health")
        assert "result_id" in rest_str

        # 2. Legacy GraphQL action
        gql_str = await facade.forward(action="graphql", endpoint="https://api.example.com/graphql", query="{ meta { version } }")
        assert "result_id" in gql_str

        # 3. Sprint 12 Service Connector action
        gmail_str = await facade.forward(action="execute_connector", service="gmail", method="SEARCH", params={"q": "Specs"})
        assert "messages" in gmail_str

        # 4. Sprint 12 Sync action
        sync_str = await facade.forward(action="sync", service="jira")
        assert "sync_started" in sync_str

        # 5. Sprint 12 Metrics action
        metrics_str = await facade.forward(action="metrics")
        assert "gmail" in metrics_str or "requests" in metrics_str

    asyncio.run(_test())


def test_smolagents_integration_tool_wrapper_sprint12():
    tool = IntegrationTool()
    res_str = tool.forward(action="execute_connector", endpoint="github", method="SEARCH_ISSUES")
    assert "issues" in res_str
