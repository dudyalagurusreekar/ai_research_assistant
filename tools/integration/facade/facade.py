"""Unified IntegrationToolFacade for the External Integration Platform."""

import json
from typing import Dict, Any, Optional

from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult
from core.models.event import Event
from core.events import AsyncEventBus
from tools.integration.models.integration_models import (
    NormalizedIntegrationResult,
    IntegrationRequest,
    AuthenticationConfig,
    ConnectorMetadata,
)
from tools.integration.registry.integration_registry import IntegrationRegistry
from tools.integration.auth.auth_manager import AuthenticationManager
from tools.integration.lifecycle.lifecycle_manager import ConnectorLifecycleManager
from tools.integration.pipeline.request_pipeline import RequestPipeline
from tools.integration.connectors.rest_connector import RESTConnector
from tools.integration.connectors.graphql_connector import GraphQLConnector
from tools.integration.connectors.mcp_connector import MCPConnector
from tools.integration.engine import UniversalConnectorPlatform
from tools.integration.permissions.permission_manager import PermissionAction
from infrastructure.logging.logger import StructuredLogger


class IntegrationToolFacade(ITool):
    """Public unified API facade for the External Integration Platform."""

    name = "integration_tool"
    description = "Unified connectivity tool for external REST APIs, GraphQL, MCP servers, authentication, and third-party integrations."

    def __init__(
        self,
        registry: Optional[IntegrationRegistry] = None,
        auth_manager: Optional[AuthenticationManager] = None,
        lifecycle_manager: Optional[ConnectorLifecycleManager] = None,
        pipeline: Optional[RequestPipeline] = None,
        event_bus: Optional[AsyncEventBus] = None,
        memory_facade: Optional[Any] = None,
        platform_engine: Optional[UniversalConnectorPlatform] = None,
    ) -> None:
        self.name = "integration_tool"
        self._logger = StructuredLogger("IntegrationToolFacade")
        self._event_bus = event_bus or AsyncEventBus()
        self._memory_facade = memory_facade
        self.platform_engine = platform_engine or UniversalConnectorPlatform()

        self._registry = registry or IntegrationRegistry()
        if not self._registry.list_connectors():
            self._registry.register(RESTConnector())
            self._registry.register(GraphQLConnector())
            self._registry.register(MCPConnector())

        self._auth_manager = auth_manager or AuthenticationManager()
        self._lifecycle_manager = lifecycle_manager or ConnectorLifecycleManager(registry=self._registry)
        self._pipeline = pipeline or RequestPipeline(auth_manager=self._auth_manager)

        self._metadata = ToolMetadata(
            name="integration_tool",
            version="2.0.0",
            description="Unified connectivity platform for Gmail, Drive, GitHub, Slack, Jira, Notion, Calendar, Database, Storage, REST, GraphQL, and MCP.",
            capabilities=[
                "rest_api", "graphql_api", "mcp_tool_invocation", "gmail", "google_drive",
                "github", "slack", "jira", "notion", "calendar", "database", "cloud_storage",
                "authentication", "least_privilege_permissions", "incremental_sync", "metrics",
            ],
            parameters_schema={
                "action": "Action to perform ('rest', 'graphql', 'mcp', 'execute_connector', 'sync', 'health', 'list_connectors', 'metrics')",
                "endpoint": "Target endpoint URL, connector name, or tool identifier",
                "method": "HTTP/Protocol method",
            },
            tags=["integration", "universal_connector", "rest", "graphql", "mcp", "saas", "api"],
            is_async=True,
            enabled=True,
        )

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata descriptor."""
        return self._metadata

    async def forward(self, action: str = "rest", **kwargs) -> str:
        """Standard tool execution wrapper returning JSON string."""
        try:
            endpoint = kwargs.get("endpoint", kwargs.get("url", kwargs.get("tool", kwargs.get("service", ""))))
            if action in ["rest", "api", "request"]:
                method = kwargs.get("method", "GET")
                params = kwargs.get("params", {})
                body = kwargs.get("body")
                res = await self.query_rest(endpoint, method=method, params=params, body=body)
                return json.dumps(res.to_dict(), indent=2)
            elif action in ["graphql", "gql"]:
                query_str = kwargs.get("query", endpoint)
                variables = kwargs.get("variables", {})
                res_gql = await self.query_graphql(endpoint, query=query_str, variables=variables)
                return json.dumps(res_gql.to_dict(), indent=2)
            elif action in ["mcp", "mcp_tool"]:
                tool_name = kwargs.get("tool_name", endpoint or "mcp_tool")
                args = kwargs.get("arguments", kwargs.get("args", {}))
                res_mcp = await self.invoke_mcp_tool(tool_name, arguments=args)
                return json.dumps(res_mcp.to_dict(), indent=2)
            elif action in ["execute_connector", "connector", "service"]:
                conn_name = kwargs.get("connector", kwargs.get("service", endpoint or "gmail"))
                method = kwargs.get("method", "GET")
                params = kwargs.get("params", {})
                body = kwargs.get("body")
                principal = kwargs.get("principal", "ara_user")
                res_conn = await self.platform_engine.execute(
                    principal=principal,
                    connector_name=conn_name,
                    method=method,
                    endpoint_or_tool=endpoint,
                    params=params,
                    body=body,
                )
                return json.dumps(res_conn.to_dict(), indent=2)
            elif action in ["sync", "sync_service"]:
                service_name = kwargs.get("service", kwargs.get("connector", endpoint or "gmail"))
                entity_type = kwargs.get("entity_type", "messages")
                chk = self.platform_engine.sync_engine.start_sync(service_name, entity_type)
                return json.dumps({"status": "sync_started", "checkpoint_id": chk.checkpoint_id}, indent=2)
            elif action in ["health", "check"]:
                c_name = kwargs.get("connector", "rest")
                meta = await self.check_health(c_name)
                return json.dumps(meta.to_dict(), indent=2)
            elif action in ["list_connectors", "list"]:
                connectors = self.platform_engine.manager.list_connectors()
                return json.dumps([c.to_dict() for c in connectors], indent=2)
            elif action in ["metrics", "get_metrics"]:
                return self.platform_engine.metrics.export_json()
            else:
                return json.dumps({"error": f"Unknown integration action '{action}'"}, indent=2)
        except Exception as e:
            self._logger.error(f"Error in IntegrationToolFacade.forward action '{action}': {e}")
            return json.dumps({"error": str(e)}, indent=2)

    async def execute(self, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Execute method returning ToolResult object conforming to ITool interface."""
        params = dict(parameters or {})
        params.update(kwargs)
        action = params.get("action", "rest")
        try:
            output_json = await self.forward(action=action, **params)
            data = json.loads(output_json)
            if isinstance(data, dict) and "error" in data:
                return ToolResult.error(error_message=data["error"])
            return ToolResult.success(data=data)
        except Exception as e:
            return ToolResult.error(error_message=str(e))

    async def execute_request(self, request: IntegrationRequest) -> NormalizedIntegrationResult:
        """Execute request using registered connector strategy."""
        try:
            await self._publish_event("integration.started", {"request_id": request.request_id, "connector": request.connector_name})
            await self._publish_event("connector.loaded", {"connector": request.connector_name, "protocol": "rest"})
            await self._publish_event("request.sent", {"request_id": request.request_id, "endpoint": request.endpoint_or_tool})

            conn_sdk = self.platform_engine.manager.get_connector(request.connector_name)
            if conn_sdk:
                result = await self.platform_engine.execute(
                    principal="ara_user",
                    connector_name=request.connector_name,
                    method=request.method,
                    endpoint_or_tool=request.endpoint_or_tool,
                    params=request.params,
                    body=request.body,
                )
                await self._publish_event("response.received", {"status_code": result.status_code, "success": result.success})
                await self._publish_event("integration.completed", {"result_id": result.result_id})
                return result

            connector = self._registry.get_connector(request.connector_name)
            if not connector:
                raise ValueError(f"Connector '{request.connector_name}' is not registered.")

            result = await self._pipeline.process_request(request, connector)
            await self._publish_event("response.received", {"status_code": result.status_code, "success": result.success})

            if self._memory_facade:
                try:
                    await self._memory_facade.remember(
                        content=f"External Request ({request.connector_name}): {request.endpoint_or_tool} -> {result.status_code}",
                        memory_type="knowledge",
                        tags=["integration", request.connector_name],
                        metadata={"request_id": request.request_id},
                    )
                except Exception as me:
                    self._logger.warning(f"Error persisting integration memory: {me}")

            await self._publish_event("integration.completed", {"result_id": result.result_id})
            return result

        except Exception as e:
            await self._publish_event("integration.failed", {"action": "execute_request", "error": str(e)})
            raise

    async def query_rest(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        auth_config: Optional[AuthenticationConfig] = None,
    ) -> NormalizedIntegrationResult:
        """Execute REST HTTP query."""
        req = IntegrationRequest(
            connector_name="rest",
            endpoint_or_tool=endpoint,
            method=method,
            params=params or {},
            body=body,
            auth_config=auth_config,
        )
        return await self.execute_request(req)

    async def query_graphql(
        self,
        endpoint: str,
        query: str = "",
        variables: Optional[Dict[str, Any]] = None,
        auth_config: Optional[AuthenticationConfig] = None,
    ) -> NormalizedIntegrationResult:
        """Execute GraphQL query or mutation."""
        req = IntegrationRequest(
            connector_name="graphql",
            endpoint_or_tool=endpoint,
            method="QUERY",
            params={"query": query, "variables": variables or {}},
            auth_config=auth_config,
        )
        return await self.execute_request(req)

    async def invoke_mcp_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        auth_config: Optional[AuthenticationConfig] = None,
    ) -> NormalizedIntegrationResult:
        """Invoke Model Context Protocol (MCP) tool."""
        req = IntegrationRequest(
            connector_name="mcp",
            endpoint_or_tool=tool_name,
            method="TOOL_CALL",
            params=arguments or {},
            auth_config=auth_config,
        )
        return await self.execute_request(req)

    async def check_health(self, connector_name: str) -> ConnectorMetadata:
        """Check health status of target connector."""
        sdk_conn = self.platform_engine.manager.get_connector(connector_name)
        if sdk_conn:
            return await sdk_conn.check_health()
        return await self._lifecycle_manager.check_health(connector_name)

    async def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish domain event over AsyncEventBus."""
        if self._event_bus:
            try:
                event_obj = Event(
                    event_type=event_type,
                    source="IntegrationToolFacade",
                    payload=payload,
                )
                await self._event_bus.publish(event_obj)
            except Exception as e:
                self._logger.warning(f"Error publishing integration event '{event_type}': {e}")
