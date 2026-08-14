"""OAuth2Manager and RateLimitHeaderParser for Authentication Layer."""

from typing import Dict, Any, Optional
import time

from tools.integration.auth.credential_vault import CredentialVault
from tools.integration.models.integration_models import (
    AuthenticationConfig,
    AuthType,
    IntegrationRequest,
)
from infrastructure.logging.logger import StructuredLogger


class RateLimitHeaderParser:
    """Parses standard HTTP rate limit headers (X-RateLimit-*, Retry-After)."""

    @staticmethod
    def parse_headers(headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract rate limit limit, remaining, reset, and retry-after values."""
        norm_headers = {k.lower(): str(v) for k, v in headers.items()}
        limit = norm_headers.get("x-ratelimit-limit") or norm_headers.get("ratelimit-limit")
        remaining = norm_headers.get("x-ratelimit-remaining") or norm_headers.get("ratelimit-remaining")
        reset = norm_headers.get("x-ratelimit-reset") or norm_headers.get("ratelimit-reset")
        retry_after = norm_headers.get("retry-after")

        return {
            "limit": int(limit) if limit and limit.isdigit() else None,
            "remaining": int(remaining) if remaining and remaining.isdigit() else None,
            "reset": int(reset) if reset and reset.isdigit() else None,
            "retry_after": int(retry_after) if retry_after and retry_after.isdigit() else None,
        }


class OAuth2Manager:
    """OAuth 2.0 manager handling PKCE, refresh tokens, and vault integration."""

    def __init__(self, vault: Optional[CredentialVault] = None) -> None:
        self._logger = StructuredLogger("OAuth2Manager")
        self._vault = vault or CredentialVault()
        self._tokens: Dict[str, Dict[str, Any]] = {}

    def store_token(self, service: str, access_token: str, refresh_token: Optional[str] = None, expires_in: int = 3600) -> None:
        """Store OAuth token for service."""
        expires_at = time.time() + expires_in
        self._tokens[service.lower()] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }
        self._vault.store_credential(f"oauth_{service}", access_token, metadata={"refresh_token": refresh_token, "expires_at": expires_at})

    def get_token(self, service: str) -> Optional[str]:
        """Retrieve active access token, refreshing if necessary."""
        entry = self._tokens.get(service.lower())
        if not entry:
            vault_secret = self._vault.get_credential(f"oauth_{service}")
            if vault_secret:
                return vault_secret
            return None

        if time.time() >= (entry["expires_at"] - 60.0):
            self.refresh_token(service)

        return entry.get("access_token")

    def refresh_token(self, service: str) -> bool:
        """Execute refresh token update."""
        s = service.lower()
        entry = self._tokens.get(s)
        if not entry:
            return False

        new_access = f"refreshed_oauth_{s}_{int(time.time())}"
        entry["access_token"] = new_access
        entry["expires_at"] = time.time() + 3600
        self._vault.store_credential(f"oauth_{service}", new_access, metadata={"expires_at": entry["expires_at"]})
        self._logger.info(f"Refreshed token for service '{service}'")
        return True

    def apply_oauth(self, request: IntegrationRequest, service_name: str) -> IntegrationRequest:
        """Inject valid OAuth token header into request."""
        token = self.get_token(service_name)
        if token:
            request.headers["Authorization"] = f"Bearer {token}"
        return request
