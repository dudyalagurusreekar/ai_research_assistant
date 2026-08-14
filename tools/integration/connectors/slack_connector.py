"""Slack Service Connector for channels, messaging, thread reading, and webhooks."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.sdk.oauth_connector import OAuthConnector
from tools.integration.models.integration_models import (
    IntegrationRequest,
    IntegrationResponse,
)


class SlackConnector(OAuthConnector):
    """Universal Connector for Slack (Channels, Message Posting, Threads, Search, Webhooks)."""

    def __init__(self) -> None:
        super().__init__(
            name="slack",
            base_url="https://slack.com/api",
            auth_url="https://slack.com/oauth/v2/authorize",
            token_url="https://slack.com/api/oauth.v2.access",
            default_scopes=["channels:read", "chat:write", "channels:history", "search:read"],
            description="Slack Web API connector for team messaging, channel search, and automated alerts",
        )
        self._mock_channels: List[Dict[str, Any]] = [
            {"id": "C01ABC123", "name": "general", "is_channel": True, "num_members": 15},
            {"id": "C02DEF456", "name": "ai-research-updates", "is_channel": True, "num_members": 8},
        ]
        self._mock_messages: List[Dict[str, Any]] = [
            {
                "ts": "1722513600.000100",
                "user": "U01USER",
                "text": "Sprint 12 Universal Connector implementation has begun!",
                "channel": "C02DEF456",
            }
        ]

    def get_supported_actions(self) -> List[str]:
        return ["list_channels", "post_message", "read_thread", "search_messages", "incoming_webhook"]

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Route Slack Web API request."""
        action = request.method.upper()
        endpoint = request.endpoint_or_tool.lower()

        if action in ["GET", "LIST_CHANNELS"] or "channels" in endpoint:
            return IntegrationResponse(status_code=200, data={"ok": True, "channels": self._mock_channels})

        elif action in ["POST", "POST_MESSAGE", "SEND"] or "chat" in endpoint:
            channel = request.params.get("channel") or request.body.get("channel", "general")
            text = request.params.get("text") or request.body.get("text", "")

            msg = {
                "ts": f"{time.time():.6f}",
                "user": "U_ARA_BOT",
                "text": text,
                "channel": channel,
            }
            self._mock_messages.append(msg)
            return IntegrationResponse(status_code=200, data={"ok": True, "channel": channel, "ts": msg["ts"], "message": msg})

        elif action in ["READ_THREAD", "THREAD"]:
            thread_ts = request.params.get("thread_ts", "1722513600.000100")
            thread_msgs = [m for m in self._mock_messages if m["ts"] == thread_ts]
            return IntegrationResponse(status_code=200, data={"ok": True, "messages": thread_msgs})

        elif action in ["SEARCH", "SEARCH_MESSAGES"]:
            query = request.params.get("query", request.params.get("q", ""))
            filtered = [m for m in self._mock_messages if not query or query.lower() in m["text"].lower()]
            return IntegrationResponse(status_code=200, data={"ok": True, "messages": {"matches": filtered, "total": len(filtered)}})

        return IntegrationResponse(status_code=400, error_message=f"Unsupported Slack action '{action}'")
