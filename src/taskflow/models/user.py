"""The User ORM model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from taskflow.database import Base


class User(Base):
    """A registered account.

    Attributes:
        id: Primary key.
        email: Unique login identifier.
        hashed_password: A bcrypt hash; the plaintext password is never
            stored.
        display_name: A human-friendly name shown in the UI/API responses.
        created_at: When the account was created, in UTC.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
