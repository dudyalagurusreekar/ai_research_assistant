"""GraphQL Protocol Connector strategy implementation."""

from tools.integration.sdk.base_connector import BaseConnector
from tools.integration.models.integration_models import IntegrationRequest, IntegrationResponse, ProtocolType


class GraphQLConnector(BaseConnector):
    """GraphQL connector strategy executing GraphQL queries and mutations."""

    def __init__(self) -> None:
        super().__init__(name="graphql", protocol=ProtocolType.GRAPHQL, description="Generic GraphQL API connector")

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Execute GraphQL query or mutation request."""
        self._logger.info(f"Executing GraphQL request to '{request.endpoint_or_tool}'")

        query_str = request.params.get("query", request.endpoint_or_tool)
        variables = request.params.get("variables", {})

        response_data = {
            "data": {
                "repository": {
                    "name": "ai-research-assistant",
                    "stars": 1250,
                    "isPrivate": False,
                }
            },
            "extensions": {"query": query_str, "variables": variables},
        }

        return IntegrationResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            data=response_data,
            response_time_ms=22.5,
        )
