"""The Notification ORM model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from taskflow.database import Base


class Notification(Base):
    """An in-app notification for one user.

    Stands in for what a production system would instead deliver as a
    real email or push notification -- see the README "Limitations"
    section.

    Attributes:
        id: Primary key.
        user_id: The notified user.
        message: Human-readable notification text.
        created_at: When the notification was generated, in UTC.
        read: Whether the user has marked it as read.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    read: Mapped[bool] = mapped_column(Boolean, default=False)
