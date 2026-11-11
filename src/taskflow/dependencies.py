"""Shared FastAPI dependencies: authentication and project authorization."""

from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taskflow.database import get_db
from taskflow.models.membership import OWNER_ROLE, ProjectMembership
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


async def get_project_membership(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectMembership:
    """Resolves the current user's membership in a project.

    Used as a path-level dependency on every `/projects/{project_id}/...`
    route, so a route handler can assume the caller is already a member
    of the project by the time its own body runs.

    Args:
        project_id: The project id from the URL path.
        current_user: The authenticated user.
        db: The request-scoped database session.

    Returns:
        The current user's `ProjectMembership` row for this project.

    Raises:
        HTTPException: 403 if the current user is not a member of the
            project. (A project that does not exist and a project the
            user cannot see are deliberately reported identically, as a
            403, to avoid leaking which project ids exist.)
    """
    result = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == current_user.id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )
    return membership


def require_project_owner(membership: ProjectMembership = Depends(get_project_membership)) -> ProjectMembership:
    """Narrows `get_project_membership` to owner-only routes.

    Args:
        membership: The current user's membership, from
            `get_project_membership`.

    Returns:
        The same membership, unchanged.

    Raises:
        HTTPException: 403 if the current user's role is not
            `OWNER_ROLE`.
    """
    if membership.role != OWNER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can perform this action",
        )
    return membership
