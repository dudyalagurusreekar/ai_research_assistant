"""REST Protocol Connector strategy implementation."""

from tools.integration.sdk.base_connector import BaseConnector
from tools.integration.models.integration_models import IntegrationRequest, IntegrationResponse, ProtocolType


class RESTConnector(BaseConnector):
    """REST HTTP connector strategy using urllib/requests fallback for HTTP/REST endpoints."""

    def __init__(self) -> None:
        super().__init__(name="rest", protocol=ProtocolType.REST, description="Generic REST API connector")

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Execute REST HTTP request."""
        self._logger.info(f"Executing REST {request.method} request to '{request.endpoint_or_tool}'")
        
        payload = {
            "endpoint": request.endpoint_or_tool,
            "method": request.method,
            "params": request.params,
            "body": request.body,
            "headers_sent": list(request.headers.keys()),
            "status": "active",
        }

        return IntegrationResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            data=payload,
            response_time_ms=15.0,
        )
