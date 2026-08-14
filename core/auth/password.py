"""Password Hashing, Verification, and Policy Validation Engine."""

import re
import hashlib
from typing import Tuple, List

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
    HAS_PASSLIB = True
except Exception:
    pwd_context = None
    HAS_PASSLIB = False


class PasswordHasher:
    """Production password hashing and verification helper."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash plain text password securely using Argon2 or PBKDF2 fallback."""
        if HAS_PASSLIB and pwd_context:
            return pwd_context.hash(password)
        
        # Salted PBKDF2-HMAC-SHA256 fallback
        salt = "ara_secure_salt_v1"
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return f"pbkdf2_sha256${key.hex()}"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plain text password against stored hash."""
        if not plain_password or not hashed_password:
            return False

        if HAS_PASSLIB and pwd_context and not hashed_password.startswith("pbkdf2_sha256$"):
            try:
                return pwd_context.verify(plain_password, hashed_password)
            except Exception:
                pass

        if hashed_password.startswith("pbkdf2_sha256$"):
            expected = PasswordHasher.hash_password(plain_password)
            return expected == hashed_password

        # Fallback comparison
        return PasswordHasher.hash_password(plain_password) == hashed_password


class PasswordPolicyValidator:
    """Enterprise Password Complexity & Security Policy Validator."""

    MIN_LENGTH = 8

    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """Validate password against complexity policy. Returns (is_valid, list_of_errors)."""
        errors = []

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long.")
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", password):
            errors.append("Password must contain at least one numeric digit.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
            errors.append("Password must contain at least one special character.")

        return len(errors) == 0, errors
