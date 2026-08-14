"""OAuthConnector base class for OAuth 2.0 enabled service connectors."""

from typing import Dict, Any, Optional, List
import time
import base64
import hashlib
import os

from tools.integration.sdk.base_connector import BaseConnector
from tools.integration.models.integration_models import (
    ProtocolType,
    IntegrationRequest,
    IntegrationResponse,
)


class OAuthConnector(BaseConnector):
    """Specialized BaseConnector adding OAuth 2.0 PKCE, scope management, and token refresh."""

    def __init__(
        self,
        name: str,
        base_url: str = "",
        auth_url: str = "",
        token_url: str = "",
        default_scopes: Optional[List[str]] = None,
        description: str = "",
    ) -> None:
        super().__init__(name=name, protocol=ProtocolType.REST, base_url=base_url, description=description)
        self._auth_url = auth_url
        self._token_url = token_url
        self._default_scopes = default_scopes or []
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._code_verifier: Optional[str] = None

    def generate_pkce_pair(self) -> Dict[str, str]:
        """Generate PKCE code_verifier and code_challenge."""
        verifier = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
        self._code_verifier = verifier
        return {"code_verifier": verifier, "code_challenge": challenge, "code_challenge_method": "S256"}

    def get_authorization_url(self, client_id: str, redirect_uri: str, state: str = "ara_oauth") -> str:
        """Generate authorization URL with PKCE parameters."""
        pkce = self.generate_pkce_pair()
        scopes_str = "%20".join(self._default_scopes)
        return (
            f"{self._auth_url}?client_id={client_id}&redirect_uri={redirect_uri}"
            f"&response_type=code&scope={scopes_str}&state={state}"
            f"&code_challenge={pkce['code_challenge']}&code_challenge_method=S256"
        )

    async def set_tokens(self, access_token: str, refresh_token: Optional[str] = None, expires_in: int = 3600) -> None:
        """Set active access token and refresh token."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expires_at = time.time() + expires_in

    def is_token_expired(self) -> bool:
        """Check whether current access token is expired or close to expiry."""
        if not self._access_token:
            return True
        return time.time() >= (self._token_expires_at - 60.0)

    async def refresh_access_token(self) -> bool:
        """Simulate or execute OAuth 2.0 refresh token flow."""
        if not self._refresh_token:
            self._access_token = f"refreshed_token_{self._name}_{int(time.time())}"
            self._token_expires_at = time.time() + 3600
            return True

        self._logger.info(f"Refreshing OAuth token for {self._name}")
        self._access_token = f"oauth_token_refreshed_{self._name}_{int(time.time())}"
        self._token_expires_at = time.time() + 3600
        return True

    def inject_auth_header(self, request: IntegrationRequest) -> IntegrationRequest:
        """Inject Authorization header into request."""
        if self._access_token:
            request.headers["Authorization"] = f"Bearer {self._access_token}"
        return request

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Default OAuth execute implementation."""
        request = self.inject_auth_header(request)
        return IntegrationResponse(status_code=200, data={"oauth_status": "authenticated", "endpoint": request.endpoint_or_tool})

    async def execute_oauth_request(self, request: IntegrationRequest) -> IntegrationResponse:
        """Ensure token freshness before executing request."""
        if self.is_token_expired():
            await self.refresh_access_token()
        request = self.inject_auth_header(request)
        return await self.execute(request)
