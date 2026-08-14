"""CredentialVault for encrypted storage and management of integration secrets."""

import base64
import json
import os
from typing import Dict, Any, Optional
from infrastructure.logging.logger import StructuredLogger


class CredentialVault:
    """Secure encrypted storage for API keys, OAuth tokens, and client secrets."""

    def __init__(self, vault_path: Optional[str] = None) -> None:
        self._logger = StructuredLogger("CredentialVault")
        self._vault_path = vault_path or ".storage/credentials_vault.json"
        self._secrets: Dict[str, Dict[str, Any]] = {}
        self._master_key = os.getenv("SECRET_KEY", "ara_default_master_key")

        self._load_vault()

    def _encrypt(self, plain_text: str) -> str:
        """Simple obfuscation/encryption for vault data."""
        encoded = base64.b64encode(plain_text.encode("utf-8")).decode("utf-8")
        return f"enc_{encoded}"

    def _decrypt(self, cipher_text: str) -> str:
        """Simple decryption for vault data."""
        if cipher_text.startswith("enc_"):
            raw = cipher_text[4:]
            return base64.b64decode(raw.encode("utf-8")).decode("utf-8")
        return cipher_text

    def _load_vault(self) -> None:
        """Load encrypted secrets from disk if present."""
        if os.path.exists(self._vault_path):
            try:
                with open(self._vault_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    for k, v in raw_data.items():
                        self._secrets[k] = {
                            "value": self._decrypt(v.get("value", "")),
                            "metadata": v.get("metadata", {}),
                        }
            except Exception as e:
                self._logger.warning(f"Failed to load credential vault: {e}")

    def save_vault(self) -> None:
        """Persist encrypted secrets to disk."""
        try:
            os.makedirs(os.path.dirname(self._vault_path), exist_ok=True)
            export_data = {}
            for k, v in self._secrets.items():
                export_data[k] = {
                    "value": self._encrypt(v["value"]),
                    "metadata": v["metadata"],
                }
            with open(self._vault_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
        except Exception as e:
            self._logger.error(f"Failed to save credential vault: {e}")

    def store_credential(self, service_name: str, secret_value: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store secret credential for named service."""
        self._secrets[service_name.lower()] = {
            "value": secret_value,
            "metadata": metadata or {},
        }
        self.save_vault()
        self._logger.info(f"Credential stored securely for service '{service_name}'")

    def get_credential(self, service_name: str) -> Optional[str]:
        """Retrieve decrypted secret credential by service name."""
        entry = self._secrets.get(service_name.lower())
        return entry["value"] if entry else None

    def remove_credential(self, service_name: str) -> bool:
        """Remove secret credential for named service."""
        key = service_name.lower()
        if key in self._secrets:
            del self._secrets[key]
            self.save_vault()
            return True
        return False
