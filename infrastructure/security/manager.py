"""Security Manager handling secrets, sanitization, validation, and permissions."""

import os
import re
from typing import Any, Dict, Optional, Set


class SecurityManager:
    """Central Security Manager for API keys, secret storage, sanitization, and permissions."""

    def __init__(self, allowed_permissions: Optional[Set[str]] = None) -> None:
        self._secrets: Dict[str, str] = {}
        self._permissions: Set[str] = allowed_permissions or {"read", "write", "execute"}

    def set_secret(self, key: str, value: str) -> None:
        """Store a secret in memory."""
        self._secrets[key] = value

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a secret from memory or environment variables."""
        if key in self._secrets:
            return self._secrets[key]
        return os.getenv(key, default)

    def sanitize_input(self, raw_input: str) -> str:
        """Sanitize raw text input to prevent injection attacks."""
        if not raw_input:
            return ""
        # Remove dangerous control characters and script tags
        sanitized = re.sub(r"<script.*?>.*?</script>", "", raw_input, flags=re.DOTALL | re.IGNORECASE)
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", sanitized)
        return sanitized.strip()

    def sanitize_output(self, raw_output: str) -> str:
        """Mask secrets and sensitive keys from output strings."""
        sanitized = raw_output
        for secret_val in self._secrets.values():
            if secret_val and len(secret_val) > 4:
                sanitized = sanitized.replace(secret_val, "***REDACTED***")
        return sanitized

    def check_permission(self, required_permission: str) -> bool:
        """Verify if a required permission is granted."""
        return required_permission in self._permissions

    def grant_permission(self, permission: str) -> None:
        """Grant a permission."""
        self._permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        """Revoke a permission."""
        self._permissions.discard(permission)
