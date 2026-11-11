"""The ProjectMembership ORM model: who belongs to which project."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taskflow.database import Base

if TYPE_CHECKING:
    from taskflow.models.project import Project

OWNER_ROLE = "owner"
MEMBER_ROLE = "member"


class ProjectMembership(Base):
    """Links a user to a project with a role.

    Attributes:
        id: Primary key.
        project_id: The project this membership belongs to.
        user_id: The member's user id.
        role: Either `OWNER_ROLE` or `MEMBER_ROLE`.
        project: The owning `Project`.
    """

    __tablename__ = "project_memberships"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(20), default=MEMBER_ROLE)

    project: Mapped["Project"] = relationship(back_populates="members")
