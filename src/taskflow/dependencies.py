"""Shared FastAPI dependencies, chiefly `get_current_user`."""

from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taskflow.database import get_db
from taskflow.models.user import User
from taskflow.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """Resolves the authenticated user from a bearer JWT.

    Args:
        token: The bearer token extracted from the `Authorization` header
            by `oauth2_scheme`.
        db: The request-scoped database session.

    Returns:
        The `User` the token was issued for.

    Raises:
        HTTPException: 401 if the token is invalid/expired, or if it no
            longer corresponds to an existing user.
    """
    try:
        email = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise _CREDENTIALS_ERROR from exc

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise _CREDENTIALS_ERROR
    return user
