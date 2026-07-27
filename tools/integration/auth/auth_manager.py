"""Authentication Manager injecting headers for API Key, Bearer Token, OAuth2, and Basic Auth."""

from typing import Dict, Any
from tools.integration.interfaces.integration_interfaces import IAuthenticationManager
from tools.integration.models.integration_models import IntegrationRequest, AuthenticationConfig, AuthType
from infrastructure.logging.logger import StructuredLogger


class AuthenticationManager(IAuthenticationManager):
    """Manages authentication schemes and injects corresponding HTTP headers or credentials."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("AuthenticationManager")

    def apply_authentication(self, request: IntegrationRequest, auth_config: AuthenticationConfig) -> IntegrationRequest:
        """Inject authentication headers into request based on auth scheme."""
        if not auth_config or auth_config.auth_type == AuthType.NONE:
            return request

        headers = dict(request.headers)

        if auth_config.auth_type == AuthType.API_KEY and auth_config.api_key:
            hdr_name = auth_config.header_name or "X-API-Key"
            headers[hdr_name] = auth_config.api_key
        elif auth_config.auth_type in [AuthType.BEARER_TOKEN, AuthType.OAUTH2, AuthType.JWT] and auth_config.token:
            prefix = auth_config.header_prefix or "Bearer "
            headers["Authorization"] = f"{prefix}{auth_config.token}"
        elif auth_config.auth_type == AuthType.BASIC and auth_config.username:
            import base64
            userpass = f"{auth_config.username}:{auth_config.password or ''}"
            encoded = base64.b64encode(userpass.encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {encoded}"

        if auth_config.extra_headers:
            headers.update(auth_config.extra_headers)

        request.headers = headers
        self._logger.debug(f"Applied '{auth_config.auth_type.value}' auth headers for request '{request.request_id}'")
        return request
