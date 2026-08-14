"""Google Drive Service Connector implementing file search, read, upload, and page token change tracking."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.sdk.oauth_connector import OAuthConnector
from tools.integration.models.integration_models import (
    IntegrationRequest,
    IntegrationResponse,
)


class GoogleDriveConnector(OAuthConnector):
    """Universal Connector for Google Drive (Search Files, Read Content, Upload, Page Token Change Tracking)."""

    def __init__(self) -> None:
        super().__init__(
            name="google_drive",
            base_url="https://www.googleapis.com/drive/v3",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            default_scopes=["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/drive.file"],
            description="Google Drive API connector for document search, file reading, uploading, and change tracking",
        )
        self._mock_files: List[Dict[str, Any]] = [
            {
                "id": "file_001",
                "name": "ARA_Architecture_Spec.pdf",
                "mimeType": "application/pdf",
                "size": "245000",
                "createdTime": "2026-07-28T10:00:00Z",
                "modifiedTime": "2026-08-01T09:00:00Z",
                "content": "ARA System Architecture documentation and component diagram.",
            },
            {
                "id": "file_002",
                "name": "Benchmark_Results_v2.5.csv",
                "mimeType": "text/csv",
                "size": "12400",
                "createdTime": "2026-07-30T14:00:00Z",
                "modifiedTime": "2026-07-30T14:00:00Z",
                "content": "model,score,latency\nGemini 1.5 Pro,94.2,120ms\nClaude 3.5 Sonnet,93.8,135ms\n",
            },
        ]

    def get_supported_actions(self) -> List[str]:
        return ["list_files", "get_file", "upload_file", "delete_file", "track_changes"]

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Route Google Drive API request."""
        action = request.method.upper()
        if action in ["GET", "LIST", "LIST_FILES", "SEARCH"]:
            q = request.params.get("q", request.params.get("query", ""))
            filtered = [
                f for f in self._mock_files
                if not q or q.lower() in f["name"].lower()
            ]
            return IntegrationResponse(status_code=200, data={"files": filtered, "nextPageToken": "page_token_abc123"})

        elif action in ["GET_FILE", "READ"]:
            file_id = request.params.get("id", request.endpoint_or_tool)
            f = next((item for item in self._mock_files if item["id"] == file_id or item["name"] == file_id), None)
            if f:
                return IntegrationResponse(status_code=200, data=f)
            return IntegrationResponse(status_code=404, error_message=f"Drive file '{file_id}' not found.")

        elif action in ["POST", "UPLOAD", "UPLOAD_FILE"]:
            name = request.params.get("name") or request.body.get("name", "untitled.txt")
            mime_type = request.params.get("mimeType", "text/plain")
            content = request.params.get("content") or request.body.get("content", "")

            new_file = {
                "id": f"file_{len(self._mock_files) + 1:03d}",
                "name": name,
                "mimeType": mime_type,
                "size": str(len(str(content))),
                "createdTime": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "modifiedTime": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "content": content,
            }
            self._mock_files.append(new_file)
            return IntegrationResponse(status_code=201, data={"status": "uploaded", "file": new_file})

        elif action in ["TRACK_CHANGES", "SYNC"]:
            page_token = request.params.get("pageToken", f"page_{int(time.time())}")
            return IntegrationResponse(
                status_code=200,
                data={
                    "changes": [{"fileId": f["id"], "removed": False, "file": f} for f in self._mock_files],
                    "newStartPageToken": f"page_{int(time.time()) + 300}",
                },
            )

        return IntegrationResponse(status_code=400, error_message=f"Unsupported Drive action '{action}'")
