"""Request/response schemas for projects and project membership."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProjectCreate(BaseModel):
    """Request body for `POST /projects`."""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)


class ProjectRead(BaseModel):
    """Response body describing a project."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    owner_id: int
    created_at: datetime


class MemberAdd(BaseModel):
    """Request body for `POST /projects/{project_id}/members`."""

    email: EmailStr


class MemberRead(BaseModel):
    """Response body describing one project membership."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: str
