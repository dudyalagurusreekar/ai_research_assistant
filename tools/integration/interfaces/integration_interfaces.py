"""Abstract interface contracts for the External Integration Platform."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tools.integration.models.integration_models import (
    NormalizedIntegrationResult,
    IntegrationRequest,
    IntegrationResponse,
    AuthenticationConfig,
    ConnectorMetadata,
    ProtocolType,
)


class IConnector(ABC):
    """Abstract strategy interface for protocol-specific connectors."""

    @property
    @abstractmethod
    def connector_name(self) -> str:
        """Connector identifier (e.g., 'rest', 'graphql', 'mcp')."""
        pass

    @property
    @abstractmethod
    def protocol(self) -> ProtocolType:
        """Supported protocol type."""
        pass

    @abstractmethod
    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Execute request against external target service."""
        pass


class IIntegrationRegistry(ABC):
    """Abstract registry interface for connector strategies."""

    @abstractmethod
    def register(self, connector: IConnector) -> None:
        """Register a connector strategy."""
        pass

    @abstractmethod
    def get_connector(self, name: str) -> Optional[IConnector]:
        """Get connector strategy by name."""
        pass

    @abstractmethod
    def list_connectors(self) -> List[ConnectorMetadata]:
        """List metadata for all registered connectors."""
        pass


class IAuthenticationManager(ABC):
    """Abstract authentication header injection interface."""

    @abstractmethod
    def apply_authentication(self, request: IntegrationRequest, auth_config: AuthenticationConfig) -> IntegrationRequest:
        """Inject authentication headers into IntegrationRequest."""
        pass


class IConnectorLifecycleManager(ABC):
    """Abstract lifecycle and health check manager interface."""

    @abstractmethod
    async def check_health(self, connector_name: str) -> ConnectorMetadata:
        """Check health status of target connector."""
        pass


class IRequestPipeline(ABC):
    """Abstract request pipeline manager interface."""

    @abstractmethod
    async def process_request(self, request: IntegrationRequest, connector: IConnector) -> NormalizedIntegrationResult:
        """Process request through middleware, retries, timeout bounds, and response normalization."""
        pass
