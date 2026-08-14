"""Calendar Service Connector for event scheduling, free-busy availability, and delta sync."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.sdk.oauth_connector import OAuthConnector
from tools.integration.models.integration_models import (
    IntegrationRequest,
    IntegrationResponse,
)


class CalendarConnector(OAuthConnector):
    """Universal Connector for Calendar Providers (Google Calendar, Outlook Calendar, iCal)."""

    def __init__(self) -> None:
        super().__init__(
            name="calendar",
            base_url="https://www.googleapis.com/calendar/v3",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            default_scopes=["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"],
            description="Calendar provider API connector for event scheduling, free/busy checks, and delta sync",
        )
        self._mock_events: List[Dict[str, Any]] = [
            {
                "id": "evt_001",
                "summary": "ARA Sprint 12 Architecture Review",
                "location": "Google Meet",
                "start": {"dateTime": "2026-08-02T10:00:00Z"},
                "end": {"dateTime": "2026-08-02T11:00:00Z"},
                "attendees": [{"email": "ara-lead@example.com"}, {"email": "engineer@example.com"}],
                "status": "confirmed",
            },
            {
                "id": "evt_002",
                "summary": "Benchmark v3.0 Evaluation Demo",
                "location": "Virtual",
                "start": {"dateTime": "2026-08-02T14:00:00Z"},
                "end": {"dateTime": "2026-08-02T15:00:00Z"},
                "attendees": [{"email": "benchmarks@example.com"}],
                "status": "confirmed",
            },
        ]

    def get_supported_actions(self) -> List[str]:
        return ["list_events", "create_event", "update_event", "free_busy_check", "delta_sync"]

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Route Calendar API request."""
        action = request.method.upper()
        endpoint = request.endpoint_or_tool.lower()

        if action in ["GET", "LIST", "LIST_EVENTS"] or "events" in endpoint:
            q = request.params.get("q", request.params.get("query", ""))
            filtered = [
                e for e in self._mock_events
                if not q or q.lower() in e["summary"].lower()
            ]
            return IntegrationResponse(status_code=200, data={"items": filtered, "summary": "Primary Calendar"})

        elif action in ["POST", "CREATE_EVENT"]:
            summary = request.params.get("summary") or request.body.get("summary", "New Calendar Event")
            start_time = request.params.get("start") or request.body.get("start", "2026-08-02T16:00:00Z")
            end_time = request.params.get("end") or request.body.get("end", "2026-08-02T17:00:00Z")

            new_evt = {
                "id": f"evt_{len(self._mock_events) + 1:03d}",
                "summary": summary,
                "location": "Virtual",
                "start": {"dateTime": start_time},
                "end": {"dateTime": end_time},
                "attendees": [],
                "status": "confirmed",
            }
            self._mock_events.append(new_evt)
            return IntegrationResponse(status_code=201, data={"status": "created", "event": new_evt})

        elif action in ["FREE_BUSY", "AVAILABILITY"]:
            busy_slots = [
                {"start": e["start"]["dateTime"], "end": e["end"]["dateTime"]} for e in self._mock_events
            ]
            return IntegrationResponse(status_code=200, data={"calendars": {"primary": {"busy": busy_slots}}})

        elif action in ["DELTA_SYNC", "SYNC"]:
            sync_token = request.params.get("syncToken", f"cal_token_{int(time.time())}")
            return IntegrationResponse(
                status_code=200,
                data={
                    "items": self._mock_events,
                    "nextSyncToken": f"cal_token_{int(time.time()) + 300}",
                },
            )

        return IntegrationResponse(status_code=400, error_message=f"Unsupported Calendar action '{action}'")
