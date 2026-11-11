"""Password hashing and JWT access-token creation/verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from taskflow.config import get_settings


def hash_password(password: str) -> str:
    """Hashes a plaintext password with bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash, as a UTF-8 string, suitable for storing in the
        database.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Checks a plaintext password against a bcrypt hash.

    Args:
        password: The plaintext password a user supplied.
        hashed_password: The stored bcrypt hash to check against.

    Returns:
        True if `password` matches `hashed_password`.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Creates a signed JWT access token.

    Args:
        subject: The token subject -- this project uses the user's email.
        expires_delta: How long the token should remain valid. Defaults
            to `access_token_expire_minutes` from application settings.

    Returns:
        The encoded JWT string.
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Decodes and validates a JWT access token.

    Args:
        token: The encoded JWT string.

    Returns:
        The token's subject (the user's email).

    Raises:
        jwt.PyJWTError: If the token is invalid, malformed, expired, or
            its signature does not match.
    """
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    return payload["sub"]
