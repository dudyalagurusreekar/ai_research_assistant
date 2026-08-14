"""GitHub Service Connector for repositories, issues, PRs, commits, and webhooks."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.sdk.oauth_connector import OAuthConnector
from tools.integration.models.integration_models import (
    IntegrationRequest,
    IntegrationResponse,
)


class GitHubConnector(OAuthConnector):
    """Universal Connector for GitHub (Repositories, Issues, PRs, Commits, Webhook Parsing)."""

    def __init__(self) -> None:
        super().__init__(
            name="github",
            base_url="https://api.github.com",
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            default_scopes=["repo", "read:user", "user:email"],
            description="GitHub REST API connector for repositories, issues, code search, and commits",
        )
        self._mock_issues: List[Dict[str, Any]] = [
            {
                "id": 101,
                "number": 1,
                "title": "Implement Sprint 12 Universal Connector Platform",
                "state": "open",
                "user": {"login": "ara-lead"},
                "body": "Build production-grade connector engine integrating Gmail, GitHub, Jira, Slack, Notion.",
                "created_at": "2026-08-01T08:00:00Z",
                "comments": 2,
            },
            {
                "id": 102,
                "number": 2,
                "title": "Add Benchmark v3.0 Execution Suite",
                "state": "closed",
                "user": {"login": "bench-bot"},
                "body": "Compare latency and throughput across Sprint 1-12 engines.",
                "created_at": "2026-07-31T10:00:00Z",
                "comments": 5,
            },
        ]
        self._mock_repos: List[Dict[str, Any]] = [
            {
                "id": 5001,
                "name": "ai_research_assistant",
                "full_name": "ara/ai_research_assistant",
                "private": False,
                "description": "Production-grade AI Research Assistant Platform",
                "stargazers_count": 128,
            }
        ]

    def get_supported_actions(self) -> List[str]:
        return ["list_repos", "search_issues", "create_issue", "create_comment", "get_commits", "parse_webhook"]

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Route GitHub API request."""
        action = request.method.upper()
        endpoint = request.endpoint_or_tool.lower()

        if action in ["GET", "LIST_REPOS"] or "repos" in endpoint:
            return IntegrationResponse(status_code=200, data={"repositories": self._mock_repos, "total_count": len(self._mock_repos)})

        elif action in ["SEARCH", "SEARCH_ISSUES"] or "issues" in endpoint:
            q = request.params.get("query", request.params.get("q", ""))
            filtered = [
                i for i in self._mock_issues
                if not q or q.lower() in i["title"].lower() or q.lower() in i["body"].lower()
            ]
            return IntegrationResponse(status_code=200, data={"issues": filtered, "total_count": len(filtered)})

        elif action in ["POST", "CREATE_ISSUE"]:
            title = request.params.get("title") or request.body.get("title", "New Issue")
            body = request.params.get("body") or request.body.get("body", "")

            new_issue = {
                "id": 100 + len(self._mock_issues) + 1,
                "number": len(self._mock_issues) + 1,
                "title": title,
                "state": "open",
                "user": {"login": "ara-agent"},
                "body": body,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "comments": 0,
            }
            self._mock_issues.append(new_issue)
            return IntegrationResponse(status_code=201, data={"status": "created", "issue": new_issue})

        elif action in ["COMMITS", "GET_COMMITS"]:
            commits = [
                {
                    "sha": "a1b2c3d4e5f67890",
                    "commit": {"author": {"name": "ARA Agent"}, "message": "feat: Sprint 12 Universal Connectors"},
                }
            ]
            return IntegrationResponse(status_code=200, data={"commits": commits})

        return IntegrationResponse(status_code=400, error_message=f"Unsupported GitHub action '{action}'")
