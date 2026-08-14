"""Unit test for SecretsManager."""

import pytest

from core.platform_infra.components.secrets_manager import SecretsManager


def test_secrets_encryption_and_masking():
    secrets = SecretsManager()
    key = "OPENAI_API_KEY"
    val = "sk-proj-1234567890abcdef"

    secret_item = secrets.set_secret(key, val)
    assert secret_item.encrypted_value != val

    retrieved = secrets.get_secret(key)
    assert retrieved == val

    masked = secrets.mask_string(f"Using key: {val}")
    assert val not in masked
    assert "*****" in masked
