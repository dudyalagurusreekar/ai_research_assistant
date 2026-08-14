"""Unit tests for Password Hashing, Policy Validation, and JWT Token Engine."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
import jwt
from core.auth.password import PasswordHasher, PasswordPolicyValidator
from core.auth.jwt import jwt_manager


def test_password_hasher_hash_and_verify():
    plain = "SuperSecret123!"
    hashed = PasswordHasher.hash_password(plain)

    assert hashed != plain
    assert PasswordHasher.verify_password(plain, hashed) is True
    assert PasswordHasher.verify_password("WrongPassword123!", hashed) is False


def test_password_policy_validator():
    # Valid password
    is_valid, errors = PasswordPolicyValidator.validate("ValidPass123!")
    assert is_valid is True
    assert len(errors) == 0

    # Short password
    is_valid, errors = PasswordPolicyValidator.validate("Short1!")
    assert is_valid is False
    assert any("at least 8 characters" in e for e in errors)

    # Missing uppercase / special char
    is_valid, errors = PasswordPolicyValidator.validate("weakpass123")
    assert is_valid is False
    assert len(errors) >= 2


def test_jwt_manager_access_and_refresh_tokens():
    user_id = "usr-jwt-test-100"
    email = "jwt@ara-research.org"

    # Issue tokens
    access_token = jwt_manager.create_access_token(user_id=user_id, email=email, role="Admin")
    refresh_token = jwt_manager.create_refresh_token(user_id=user_id)

    assert isinstance(access_token, str)
    assert isinstance(refresh_token, str)

    # Decode and verify payload
    payload = jwt_manager.decode_token(access_token)
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["role"] == "Admin"
    assert payload["type"] == "access"

    rf_payload = jwt_manager.decode_token(refresh_token)
    assert rf_payload["sub"] == user_id
    assert rf_payload["type"] == "refresh"


def test_jwt_token_revocation_blacklist():
    user_id = "usr-revoke-99"
    token = jwt_manager.create_access_token(user_id=user_id, email="r@ara-research.org")
    
    payload = jwt_manager.decode_token(token)
    jti = payload["jti"]

    assert jwt_manager.is_token_revoked(jti) is False

    # Revoke JTI
    jwt_manager.revoke_token(jti, ttl_seconds=60)
    assert jwt_manager.is_token_revoked(jti) is True

    # Decoding blacklisted token must raise InvalidTokenError
    with pytest.raises(jwt.InvalidTokenError):
        jwt_manager.decode_token(token)
