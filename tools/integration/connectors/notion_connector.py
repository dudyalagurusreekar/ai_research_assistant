"""Notion Service Connector for databases, pages, block contents, and edit tracking."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.sdk.oauth_connector import OAuthConnector
from tools.integration.models.integration_models import (
    IntegrationRequest,
    IntegrationResponse,
)


class NotionConnector(OAuthConnector):
    """Universal Connector for Notion (Query Database, Search Pages, Fetch Blocks, Append Content, Edit Tracking)."""

    def __init__(self) -> None:
        super().__init__(
            name="notion",
            base_url="https://api.notion.com/v1",
            auth_url="https://api.notion.com/v1/oauth/authorize",
            token_url="https://api.notion.com/v1/oauth/token",
            default_scopes=["read", "write"],
            description="Notion API connector for structured databases, documentation pages, and knowledge bases",
        )
        self._mock_pages: List[Dict[str, Any]] = [
            {
                "id": "page_001",
                "title": "ARA Project Roadmap",
                "object": "page",
                "created_time": "2026-07-25T09:00:00Z",
                "last_edited_time": "2026-08-01T11:00:00Z",
                "url": "https://notion.so/ARA-Project-Roadmap-001",
                "blocks": [
                    {"type": "heading_1", "text": "Sprint 12 Universal Connectors"},
                    {"type": "paragraph", "text": "Enables seamless integration with external SaaS services."},
                ],
            },
            {
                "id": "page_002",
                "title": "Data Intelligence & ML Benchmarks",
                "object": "page",
                "created_time": "2026-07-29T14:00:00Z",
                "last_edited_time": "2026-07-29T14:00:00Z",
                "url": "https://notion.so/Data-Intelligence-002",
                "blocks": [
                    {"type": "paragraph", "text": "Evaluation reports for multivariate ANOVA and K-Means clustering."}
                ],
            },
        ]

    def get_supported_actions(self) -> List[str]:
        return ["query_database", "search_pages", "get_page", "append_block", "track_page_edits"]

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Route Notion API request."""
        action = request.method.upper()
        endpoint = request.endpoint_or_tool.lower()

        if action in ["GET", "SEARCH", "SEARCH_PAGES"] or "search" in endpoint:
            query = request.params.get("query", request.params.get("q", ""))
            filtered = [
                p for p in self._mock_pages
                if not query or query.lower() in p["title"].lower()
            ]
            return IntegrationResponse(status_code=200, data={"object": "list", "results": filtered, "has_more": False})

        elif action in ["GET_PAGE", "READ"]:
            page_id = request.params.get("id", request.endpoint_or_tool)
            p = next((item for item in self._mock_pages if item["id"] == page_id or item["title"] == page_id), None)
            if p:
                return IntegrationResponse(status_code=200, data=p)
            return IntegrationResponse(status_code=404, error_message=f"Notion page '{page_id}' not found.")

        elif action in ["POST", "APPEND_BLOCK", "APPEND"]:
            page_id = request.params.get("page_id") or request.body.get("page_id", "page_001")
            text = request.params.get("text") or request.body.get("text", "")
            block_type = request.params.get("type", "paragraph")

            page = next((item for item in self._mock_pages if item["id"] == page_id), None)
            if page:
                new_block = {"type": block_type, "text": text}
                page["blocks"].append(new_block)
                page["last_edited_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                return IntegrationResponse(status_code=200, data={"status": "appended", "block": new_block, "page_id": page_id})
            return IntegrationResponse(status_code=404, error_message=f"Notion page '{page_id}' not found.")

        elif action in ["QUERY_DATABASE", "QUERY"]:
            return IntegrationResponse(status_code=200, data={"object": "list", "results": self._mock_pages})

        return IntegrationResponse(status_code=400, error_message=f"Unsupported Notion action '{action}'")
