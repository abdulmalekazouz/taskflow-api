"""The Task ORM model."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taskflow.database import Base

if TYPE_CHECKING:
    from taskflow.models.project import Project


class TaskStatus(str, enum.Enum):
    """The lifecycle states a task can be in."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(Base):
    """A single unit of work within a project.

    Attributes:
        id: Primary key.
        project_id: The owning project.
        title: Short task title.
        description: Free-text details.
        status: Current `TaskStatus`.
        assignee_id: The `User` responsible for this task, if assigned.
        created_at: When the task was created, in UTC.
        due_date: An optional deadline.
        project: The owning `Project`.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(2000), default="")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="tasks")
