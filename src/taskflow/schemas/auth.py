"""Request/response schemas for registration, login, and the current user."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Request body for `POST /auth/register`."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)


class UserRead(BaseModel):
    """Response body describing a user, with no password information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    display_name: str
    created_at: datetime


class Token(BaseModel):
    """Response body for `POST /auth/login`."""

    access_token: str
    token_type: str = "bearer"
