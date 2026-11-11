"""Request/response schemas for tasks, including a paginated list response."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from taskflow.models.task import TaskStatus


class TaskCreate(BaseModel):
    """Request body for `POST /projects/{project_id}/tasks`."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    assignee_id: int | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    """Request body for `PATCH /projects/{project_id}/tasks/{task_id}`.

    Every field is optional; only the fields present in the request are
    changed (a standard partial-update/PATCH semantics).
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None
    assignee_id: int | None = None
    due_date: datetime | None = None


class TaskRead(BaseModel):
    """Response body describing a task."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str
    status: TaskStatus
    assignee_id: int | None
    created_at: datetime
    due_date: datetime | None


class TaskPage(BaseModel):
    """A page of tasks, for `GET /projects/{project_id}/tasks`."""

    items: list[TaskRead]
    total: int
    page: int
    page_size: int
