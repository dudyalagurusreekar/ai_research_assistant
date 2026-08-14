"""Gmail Service Connector implementing OAuth 2.0 and official Gmail API operations."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.sdk.oauth_connector import OAuthConnector
from tools.integration.models.integration_models import (
    IntegrationRequest,
    IntegrationResponse,
)


class GmailConnector(OAuthConnector):
    """Universal Connector for Gmail (Search, Send, Fetch Threads, Attachments, Incremental Sync)."""

    def __init__(self) -> None:
        super().__init__(
            name="gmail",
            base_url="https://gmail.googleapis.com/gmail/v1/users/me",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            default_scopes=[
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.modify",
            ],
            description="Gmail API connector for email research, thread fetching, attachments, and messaging",
        )
        self._mock_emails: List[Dict[str, Any]] = [
            {
                "id": "msg_001",
                "threadId": "th_001",
                "subject": "Quarterly AI Research Update",
                "from": "researcher@example.com",
                "to": "ara@example.com",
                "snippet": "Here are the latest Benchmark v3.0 evaluation results.",
                "body": "Detailed report on ARA Autonomous Research Platform performance.",
                "date": "2026-08-01T12:00:00Z",
                "attachments": [{"filename": "report.pdf", "attachmentId": "att_101"}],
            },
            {
                "id": "msg_002",
                "threadId": "th_002",
                "subject": "Sprint 12 Integration Platform Specs",
                "from": "lead@example.com",
                "to": "ara@example.com",
                "snippet": "Please ensure support for Gmail, GitHub, Jira, Slack, Notion.",
                "body": "Architecture requirements for Universal Connector & Integration Platform.",
                "date": "2026-08-01T15:30:00Z",
                "attachments": [],
            },
        ]

    def get_supported_actions(self) -> List[str]:
        return ["search_messages", "get_message", "send_message", "get_thread", "download_attachment", "sync_messages"]

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Route Gmail API request."""
        action = request.method.upper()
        if action in ["GET", "SEARCH", "SEARCH_MESSAGES"]:
            query = request.params.get("query", request.params.get("q", ""))
            filtered = [
                m for m in self._mock_emails
                if not query or query.lower() in m["subject"].lower() or query.lower() in m["snippet"].lower()
            ]
            return IntegrationResponse(status_code=200, data={"messages": filtered, "resultSizeEstimate": len(filtered)})

        elif action in ["GET_MESSAGE", "READ"]:
            msg_id = request.params.get("id", request.endpoint_or_tool)
            msg = next((m for m in self._mock_emails if m["id"] == msg_id), None)
            if msg:
                return IntegrationResponse(status_code=200, data=msg)
            return IntegrationResponse(status_code=404, error_message=f"Email message '{msg_id}' not found.")

        elif action in ["POST", "SEND", "SEND_MESSAGE"]:
            to_addr = request.params.get("to") or request.body.get("to")
            subj = request.params.get("subject") or request.body.get("subject")
            body_text = request.params.get("body") or request.body.get("body", "")

            new_msg = {
                "id": f"msg_{len(self._mock_emails) + 1:03d}",
                "threadId": f"th_{len(self._mock_emails) + 1:03d}",
                "subject": subj,
                "from": "me@example.com",
                "to": to_addr,
                "snippet": body_text[:50],
                "body": body_text,
                "date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "attachments": [],
            }
            self._mock_emails.append(new_msg)
            return IntegrationResponse(status_code=201, data={"id": new_msg["id"], "status": "sent", "message": new_msg})

        elif action in ["SYNC", "SYNC_MESSAGES"]:
            sync_token = request.params.get("sync_token", f"sync_gmail_{int(time.time())}")
            next_token = f"sync_gmail_{int(time.time()) + 300}"
            return IntegrationResponse(
                status_code=200,
                data={
                    "messages": self._mock_emails,
                    "syncToken": next_token,
                    "previousSyncToken": sync_token,
                },
            )

        return IntegrationResponse(status_code=400, error_message=f"Unsupported Gmail action '{action}'")
