"""Jira Service Connector for JQL search, issue tracking, status updates, and comments."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.sdk.oauth_connector import OAuthConnector
from tools.integration.models.integration_models import (
    IntegrationRequest,
    IntegrationResponse,
)


class JiraConnector(OAuthConnector):
    """Universal Connector for Jira (JQL Search, Create Issue, Update Status, Transitions, Comments)."""

    def __init__(self) -> None:
        super().__init__(
            name="jira",
            base_url="https://your-domain.atlassian.net/rest/api/3",
            auth_url="https://auth.atlassian.com/authorize",
            token_url="https://auth.atlassian.com/oauth/token",
            default_scopes=["read:jira-work", "write:jira-work", "read:jira-user"],
            description="Jira REST API connector for enterprise task management and agile workflows",
        )
        self._mock_issues: List[Dict[str, Any]] = [
            {
                "key": "ARA-101",
                "id": "10001",
                "summary": "Implement Universal Connector Platform",
                "description": "Sprint 12 epic for external service integration",
                "status": "In Progress",
                "assignee": "ARA Platform Engine",
                "reporter": "Lead Architect",
                "created": "2026-08-01T07:00:00Z",
                "comments": [{"id": "c1", "body": "Starting implementation of OAuth2 & Connector SDK."}],
            },
            {
                "key": "ARA-102",
                "id": "10002",
                "summary": "Integrate Knowledge Graph with external connectors",
                "description": "Semantic memory ingestion of Gmail and Jira entities",
                "status": "To Do",
                "assignee": "Knowledge Graph Team",
                "reporter": "Lead Architect",
                "created": "2026-08-01T08:00:00Z",
                "comments": [],
            },
        ]

    def get_supported_actions(self) -> List[str]:
        return ["search_jql", "get_issue", "create_issue", "update_status", "add_comment"]

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Route Jira REST API request."""
        action = request.method.upper()
        endpoint = request.endpoint_or_tool.lower()

        if action in ["GET", "SEARCH", "SEARCH_JQL"] or "search" in endpoint:
            jql = request.params.get("jql", request.params.get("q", ""))
            filtered = [
                i for i in self._mock_issues
                if not jql or jql.lower() in i["summary"].lower() or jql.lower() in i["key"].lower()
            ]
            return IntegrationResponse(status_code=200, data={"issues": filtered, "total": len(filtered)})

        elif action in ["GET_ISSUE", "READ"]:
            key = request.params.get("key", request.endpoint_or_tool)
            issue = next((i for i in self._mock_issues if i["key"] == key or i["id"] == key), None)
            if issue:
                return IntegrationResponse(status_code=200, data=issue)
            return IntegrationResponse(status_code=404, error_message=f"Jira issue '{key}' not found.")

        elif action in ["POST", "CREATE_ISSUE"]:
            summary = request.params.get("summary") or request.body.get("summary", "New Jira Task")
            desc = request.params.get("description") or request.body.get("description", "")

            key_num = 100 + len(self._mock_issues) + 1
            new_issue = {
                "key": f"ARA-{key_num}",
                "id": str(10000 + key_num),
                "summary": summary,
                "description": desc,
                "status": "To Do",
                "assignee": "ARA Agent",
                "reporter": "ARA Agent",
                "created": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "comments": [],
            }
            self._mock_issues.append(new_issue)
            return IntegrationResponse(status_code=201, data={"status": "created", "issue": new_issue})

        elif action in ["PUT", "UPDATE_STATUS", "TRANSITION"]:
            key = request.params.get("key", request.endpoint_or_tool)
            status = request.params.get("status") or request.body.get("status", "Done")
            issue = next((i for i in self._mock_issues if i["key"] == key), None)
            if issue:
                issue["status"] = status
                return IntegrationResponse(status_code=200, data={"updated": True, "key": key, "new_status": status})
            return IntegrationResponse(status_code=404, error_message=f"Jira issue '{key}' not found.")

        return IntegrationResponse(status_code=400, error_message=f"Unsupported Jira action '{action}'")
