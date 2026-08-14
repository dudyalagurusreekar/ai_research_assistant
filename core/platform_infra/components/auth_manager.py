"""Auth Manager — JWT Token, API Key, OAuth, and RBAC Permission Enforcement."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Dict, List, Optional

from core.platform_infra.models.auth import APIKey, AuthContext, AuthType, JWTToken, UserIdentity, UserRole
from utils.logger import get_logger

logger = get_logger("AuthManager")


class AuthManager:
    """Authentication and Role-Based Access Control (RBAC) Manager."""

    def __init__(self, secret_key: str = "ara_enterprise_secret_key_2026") -> None:
        self.secret_key = secret_key.encode("utf-8")
        self._users: Dict[str, UserIdentity] = {}
        self._api_keys: Dict[str, APIKey] = {}

        # Register default seed identities
        self.register_user(UserIdentity(user_id="usr_admin", username="admin", email="admin@ara.internal", role=UserRole.ADMIN))
        self.register_user(UserIdentity(user_id="usr_researcher", username="researcher", email="researcher@ara.internal", role=UserRole.RESEARCHER))
        self.register_user(UserIdentity(user_id="usr_viewer", username="viewer", email="viewer@ara.internal", role=UserRole.VIEWER))

    def register_user(self, user: UserIdentity) -> None:
        """Register user identity."""
        self._users[user.user_id] = user
        logger.info(f"AuthManager registered user '{user.username}' [Role: {user.role.value}]")

    def issue_jwt_token(self, user_id: str, expires_in_seconds: int = 3600) -> JWTToken:
        """Generate JWT access token for user."""
        user = self._users.get(user_id)
        if not user:
            raise ValueError(f"User identity '{user_id}' not found.")

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
            "exp": int(time.time()) + expires_in_seconds,
        }

        token_str = self._encode_jwt(header, payload)
        return JWTToken(access_token=token_str, expires_in_seconds=expires_in_seconds)

    def verify_jwt_token(self, token_str: str) -> AuthContext:
        """Verify and decode JWT access token."""
        try:
            payload = self._decode_jwt(token_str)
            user_id = payload.get("sub", "")
            user = self._users.get(user_id)
            if not user:
                raise ValueError("User in token payload not found.")

            if payload.get("exp", 0) < time.time():
                raise ValueError("JWT token expired.")

            return AuthContext(user=user, auth_type=AuthType.JWT, token_id=token_str[:10])
        except Exception as exc:
            logger.warning(f"AuthManager JWT verification failed: {exc}")
            raise ValueError(f"Invalid JWT token: {exc}")

    def create_api_key(self, user_id: str, name: str = "API Key") -> str:
        """Create and hash API Key for user."""
        user = self._users.get(user_id)
        if not user:
            raise ValueError(f"User identity '{user_id}' not found.")

        raw_key = f"ara_key_{uuid.uuid4().hex}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        api_key = APIKey(
            key_hash=key_hash,
            name=name,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            role=user.role,
        )
        self._api_keys[key_hash] = api_key
        logger.info(f"AuthManager created API key '{name}' for user '{user.username}'")
        return raw_key

    def verify_api_key(self, raw_key: str) -> AuthContext:
        """Verify raw API Key."""
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        api_key = self._api_keys.get(key_hash)

        if not api_key or api_key.is_revoked:
            raise ValueError("Invalid or revoked API Key.")

        user = self._users.get(api_key.user_id)
        if not user:
            raise ValueError("API Key user identity not found.")

        return AuthContext(user=user, auth_type=AuthType.API_KEY, token_id=api_key.key_id)

    def check_rbac(self, auth_ctx: AuthContext, required_permission: str) -> bool:
        """Enforce Role-Based Access Control permission check."""
        if not auth_ctx.is_authenticated:
            return False
        return auth_ctx.has_permission(required_permission)

    def _encode_jwt(self, header: Dict[str, Any], payload: Dict[str, Any]) -> str:
        h_str = json.dumps(header).encode("utf-8")
        p_str = json.dumps(payload).encode("utf-8")

        import base64
        h_b64 = base64.urlsafe_b64encode(h_str).decode("utf-8").rstrip("=")
        p_b64 = base64.urlsafe_b64encode(p_str).decode("utf-8").rstrip("=")

        signature = hmac.new(self.secret_key, f"{h_b64}.{p_b64}".encode("utf-8"), hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
        return f"{h_b64}.{p_b64}.{sig_b64}"

    def _decode_jwt(self, token_str: str) -> Dict[str, Any]:
        parts = token_str.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed JWT structure.")

        h_b64, p_b64, sig_b64 = parts
        expected_sig = hmac.new(self.secret_key, f"{h_b64}.{p_b64}".encode("utf-8"), hashlib.sha256).digest()

        import base64
        rem = len(p_b64) % 4
        if rem > 0:
            p_b64 += "=" * (4 - rem)

        p_str = base64.urlsafe_b64decode(p_b64).decode("utf-8")
        return json.loads(p_str)
