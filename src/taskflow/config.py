"""Application configuration, read from environment variables.

Every setting has a safe local-development default so the app runs
out of the box; production deployments are expected to override
`TASKFLOW_SECRET_KEY` at minimum.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the taskflow API.

    Attributes:
        database_url: SQLAlchemy async connection string.
        secret_key: HMAC signing key for JWT access tokens.
        jwt_algorithm: Algorithm used to sign/verify JWTs.
        access_token_expire_minutes: How long an issued access token
            remains valid.
    """

    database_url: str
    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int


def get_settings() -> Settings:
    """Builds a `Settings` instance from environment variables.

    Returns:
        A `Settings` instance. Reads `TASKFLOW_DATABASE_URL`,
        `TASKFLOW_SECRET_KEY`, `TASKFLOW_JWT_ALGORITHM`, and
        `TASKFLOW_ACCESS_TOKEN_EXPIRE_MINUTES`, each with a development
        default if unset.
    """
    return Settings(
        database_url=os.environ.get(
            "TASKFLOW_DATABASE_URL", "sqlite+aiosqlite:///./taskflow.db"
        ),
        secret_key=os.environ.get(
            "TASKFLOW_SECRET_KEY", "dev-only-secret-change-me-in-production"
        ),
        jwt_algorithm=os.environ.get("TASKFLOW_JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(
            os.environ.get("TASKFLOW_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        ),
    )
