"""The Project ORM model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taskflow.database import Base

if TYPE_CHECKING:
    from taskflow.models.membership import ProjectMembership
    from taskflow.models.task import Task


class Project(Base):
    """A project that owns a set of tasks and has a membership list.

    Attributes:
        id: Primary key.
        name: Display name.
        description: Free-text description.
        owner_id: The `User` who created the project.
        created_at: When the project was created, in UTC.
        members: This project's `ProjectMembership` rows.
        tasks: This project's `Task` rows.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    members: Mapped[list["ProjectMembership"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
