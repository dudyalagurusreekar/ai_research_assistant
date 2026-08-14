"""Secrets models — Secure configuration and AES key containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class EncryptionConfig:
    """AES encryption configuration."""

    algorithm: str = "AES-GCM-256"
    key_version: int = 1


@dataclass
class SecretItem:
    """Encrypted secret metadata item."""

    key: str
    encrypted_value: str
    key_version: int = 1
    masked_value: str = "********"
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
