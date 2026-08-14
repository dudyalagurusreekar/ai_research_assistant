"""UniversalConnectorPlatform master platform engine for Sprint 12."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.manager.connector_manager import ConnectorManager
from tools.integration.auth.oauth2_manager import OAuth2Manager, RateLimitHeaderParser
from tools.integration.auth.credential_vault import CredentialVault
from tools.integration.permissions.permission_manager import PermissionManager, PermissionAction
from tools.integration.sync.sync_engine import SynchronizationEngine, SyncMode
from tools.integration.change_detection.change_detector import ChangeDetectionEngine, ChangeEvent
from tools.integration.scheduler.scheduler import IntegrationScheduler, ScheduledJob
from tools.integration.cache.cache_layer import IntegrationCache
from tools.integration.metrics.metrics_engine import ConnectorMetricsEngine

# Connectors
from tools.integration.connectors.gmail_connector import GmailConnector
from tools.integration.connectors.google_drive_connector import GoogleDriveConnector
from tools.integration.connectors.github_connector import GitHubConnector
from tools.integration.connectors.slack_connector import SlackConnector
from tools.integration.connectors.jira_connector import JiraConnector
from tools.integration.connectors.notion_connector import NotionConnector
from tools.integration.connectors.calendar_connector import CalendarConnector
from tools.integration.connectors.database_connector import DatabaseServiceConnector
from tools.integration.connectors.cloud_storage_connector import CloudStorageServiceConnector
from tools.integration.connectors.rest_connector import RESTConnector
from tools.integration.connectors.graphql_connector import GraphQLConnector
from tools.integration.connectors.mcp_connector import MCPConnector

# Bridges
from tools.integration.bridges.planner_bridge import PlannerConnectorBridge
from tools.integration.bridges.tool_selection_bridge import ToolSelectionConnectorBridge
from tools.integration.bridges.llm_bridge import LLMConnectorBridge
from tools.integration.bridges.reflection_bridge import ReflectionConnectorBridge
from tools.integration.bridges.learning_bridge import LearningConnectorBridge
from tools.integration.bridges.data_intelligence_bridge import DataIntelligenceConnectorBridge
from tools.integration.bridges.agent_bridge import AgentConnectorBridge
from tools.integration.bridges.knowledge_graph_bridge import KnowledgeGraphConnectorBridge
from tools.integration.bridges.browser_bridge import BrowserConnectorBridge
from tools.integration.bridges.workflow_bridge import WorkflowConnectorBridge

from tools.integration.models.integration_models import (
    IntegrationRequest,
    NormalizedIntegrationResult,
)
from infrastructure.logging.logger import StructuredLogger


class UniversalConnectorPlatform:
    """Master orchestrator for Sprint 12 Universal Connector & Integration Platform."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("UniversalConnectorPlatform")

        # Core platform engines
        self.vault = CredentialVault()
        self.auth_manager = OAuth2Manager(vault=self.vault)
        self.permission_manager = PermissionManager()
        self.manager = ConnectorManager()
        self.sync_engine = SynchronizationEngine()
        self.change_engine = ChangeDetectionEngine()
        self.scheduler = IntegrationScheduler()
        self.cache = IntegrationCache()
        self.metrics = ConnectorMetricsEngine()

        # Register default connectors
        self._register_default_connectors()

        # Subsystem bridges
        self.planner_bridge = PlannerConnectorBridge(platform_engine=self)
        self.tool_selection_bridge = ToolSelectionConnectorBridge(platform_engine=self)
        self.llm_bridge = LLMConnectorBridge(platform_engine=self)
        self.reflection_bridge = ReflectionConnectorBridge(platform_engine=self)
        self.learning_bridge = LearningConnectorBridge(platform_engine=self)
        self.data_intelligence_bridge = DataIntelligenceConnectorBridge(platform_engine=self)
        self.agent_bridge = AgentConnectorBridge(platform_engine=self)
        self.knowledge_graph_bridge = KnowledgeGraphConnectorBridge(platform_engine=self)
        self.browser_bridge = BrowserConnectorBridge(platform_engine=self)
        self.workflow_bridge = WorkflowConnectorBridge(platform_engine=self)

    def _register_default_connectors(self) -> None:
        """Register all 12 built-in service & protocol connectors."""
        self.manager.register_connector(GmailConnector())
        self.manager.register_connector(GoogleDriveConnector())
        self.manager.register_connector(GitHubConnector())
        self.manager.register_connector(SlackConnector())
        self.manager.register_connector(JiraConnector())
        self.manager.register_connector(NotionConnector())
        self.manager.register_connector(CalendarConnector())
        self.manager.register_connector(DatabaseServiceConnector())
        self.manager.register_connector(CloudStorageServiceConnector())
        self.manager.register_connector(RESTConnector())
        self.manager.register_connector(GraphQLConnector())
        self.manager.register_connector(MCPConnector())

    async def initialize(self) -> bool:
        """Initialize platform and all registered connectors."""
        await self.manager.initialize_all()
        self._logger.info("UniversalConnectorPlatform fully initialized with all 12 connectors and 10 subsystem bridges.")
        return True

    async def execute(
        self,
        principal: str,
        connector_name: str,
        method: str = "GET",
        endpoint_or_tool: str = "",
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        action_type: PermissionAction = PermissionAction.READ,
        use_cache: bool = True,
    ) -> NormalizedIntegrationResult:
        """Execute request with least-privilege permission check, caching, and metrics tracking."""
        start_time = time.time()
        params = params or {}

        # 1. Permission check
        allowed = self.permission_manager.check_permission(
            principal=principal,
            service_name=connector_name,
            resource=endpoint_or_tool or "*",
            action=action_type,
        )
        if not allowed:
            exec_time = (time.time() - start_time) * 1000.0
            self.metrics.record_request(connector_name, success=False, latency_ms=exec_time, error_message="Permission Denied")
            return NormalizedIntegrationResult(
                connector_name=connector_name,
                success=False,
                status_code=403,
                error=f"Permission denied for principal '{principal}' on service '{connector_name}'.",
                execution_time_ms=exec_time,
            )

        # 2. Check cache
        if use_cache and method.upper() in ["GET", "SEARCH", "READ", "SEARCH_ISSUES", "SEARCH_MESSAGES", "LIST_FILES"]:
            cached = self.cache.get(connector_name, endpoint_or_tool, params)
            if cached is not None:
                exec_time = (time.time() - start_time) * 1000.0
                self.metrics.record_request(connector_name, success=True, latency_ms=exec_time)
                res_cached = NormalizedIntegrationResult(
                    connector_name=connector_name,
                    success=True,
                    status_code=200,
                    data=cached,
                    execution_time_ms=exec_time,
                    metadata={"cached": True},
                )
                self.knowledge_graph_bridge.ingest_entity(connector_name, method.lower(), cached if isinstance(cached, dict) else {"content": cached})
                return res_cached

        # 3. Request execution via ConnectorManager
        req = IntegrationRequest(
            connector_name=connector_name,
            endpoint_or_tool=endpoint_or_tool,
            method=method,
            params=params,
            body=body,
        )
        res = await self.manager.execute_request(req)
        exec_time = (time.time() - start_time) * 1000.0

        # 4. Metrics & Cache update
        self.metrics.record_request(
            connector_name=connector_name,
            success=res.success,
            latency_ms=exec_time,
            error_message=res.error or "",
            rate_limit_hit=res.status_code == 429,
        )
        if res.success and use_cache and method.upper() in ["GET", "SEARCH", "READ", "SEARCH_ISSUES", "SEARCH_MESSAGES", "LIST_FILES"]:
            self.cache.set(connector_name, endpoint_or_tool, res.data, params)

        # 5. Ingest into Knowledge Graph & Learning bridges
        if res.success and res.data:
            try:
                self.knowledge_graph_bridge.ingest_entity(connector_name, method.lower(), res.data if isinstance(res.data, dict) else {"content": res.data})
                self.learning_bridge.record_experience(connector_name, method, exec_time, res.success)
            except Exception as me:
                self._logger.warning(f"Bridge notification failed: {me}")

        return res
