"""Registration, login, and "who am I" endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taskflow.database import get_db
from taskflow.dependencies import get_current_user
from taskflow.models.user import User
from taskflow.schemas.auth import Token, UserCreate, UserRead
from taskflow.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """Creates a new user account.

    Args:
        payload: The requested email, password, and display name.
        db: The request-scoped database session.

    Returns:
        The newly created user.

    Raises:
        HTTPException: 400 if the email is already registered.
    """
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered"
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Token:
    """Exchanges an email/password for a JWT access token.

    Note: this endpoint accepts the standard OAuth2 password-grant form
    (`username`/`password` fields, per the spec `OAuth2PasswordRequestForm`
    models) -- pass the user's email as `username`.

    Args:
        form_data: The submitted email (as `username`) and password.
        db: The request-scoped database session.

    Returns:
        A bearer access token.

    Raises:
        HTTPException: 401 if the email/password combination is invalid.
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Returns the authenticated user's own profile.

    Args:
        current_user: The user resolved from the bearer token.

    Returns:
        The current user.
    """
    return current_user
