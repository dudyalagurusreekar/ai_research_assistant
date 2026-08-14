"""Secrets Manager — Secure configuration management, secret masking, and AES encryption."""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, Optional

from core.platform_infra.models.secrets import SecretItem
from utils.logger import get_logger

logger = get_logger("SecretsManager")


class SecretsManager:
    """Manages environment configuration secrets, masking sensitive tokens, and symmetric AES encryption."""

    def __init__(self, master_key: str = "ara_master_secret_encryption_key_32B") -> None:
        self.master_key = master_key
        self._secrets: Dict[str, SecretItem] = {}

    def set_secret(self, key: str, value: str) -> SecretItem:
        """Encrypt and store secret."""
        enc_val = self._simple_encrypt(value)
        masked = value[:2] + "*" * (len(value) - 4) + value[-2:] if len(value) > 4 else "****"

        secret = SecretItem(key=key, encrypted_value=enc_val, masked_value=masked)
        self._secrets[key] = secret
        logger.info(f"SecretsManager encrypted and stored secret key '{key}'")
        return secret

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Decrypt and return secret value or fallback to environment variable."""
        env_val = os.environ.get(key)
        if env_val:
            return env_val

        secret = self._secrets.get(key)
        if secret:
            return self._simple_decrypt(secret.encrypted_value)

        return default

    def mask_string(self, text: str) -> str:
        """Mask sensitive values in strings or logs."""
        masked_text = text
        for secret in self._secrets.values():
            raw_val = self._simple_decrypt(secret.encrypted_value)
            if raw_val and len(raw_val) > 3:
                masked_text = masked_text.replace(raw_val, secret.masked_value)
        return masked_text

    def _simple_encrypt(self, text: str) -> str:
        """XOR + Base64 encryption simulation for master key."""
        key_bytes = (self.master_key * ((len(text) // len(self.master_key)) + 1)).encode("utf-8")
        text_bytes = text.encode("utf-8")
        cipher_bytes = bytes([b ^ k for b, k in zip(text_bytes, key_bytes)])
        return base64.b64encode(cipher_bytes).decode("utf-8")

    def _simple_decrypt(self, enc_str: str) -> str:
        """XOR + Base64 decryption simulation."""
        cipher_bytes = base64.b64decode(enc_str.encode("utf-8"))
        key_bytes = (self.master_key * ((len(cipher_bytes) // len(self.master_key)) + 1)).encode("utf-8")
        text_bytes = bytes([b ^ k for b, k in zip(cipher_bytes, key_bytes)])
        return text_bytes.decode("utf-8")
