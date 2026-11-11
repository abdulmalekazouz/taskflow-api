"""Request/response schemas for notifications."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    """Response body describing one notification."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    created_at: datetime
    read: bool
