"""Listing and acknowledging the current user's notifications."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taskflow.database import get_db
from taskflow.dependencies import get_current_user
from taskflow.models.notification import Notification
from taskflow.models.user import User
from taskflow.schemas.notification import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[Notification]:
    """Lists the current user's notifications, newest first.

    Args:
        current_user: The authenticated user.
        db: The request-scoped database session.

    Returns:
        The user's notifications.
    """
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Notification:
    """Marks one of the current user's notifications as read.

    Args:
        notification_id: The notification to mark as read.
        current_user: The authenticated user.
        db: The request-scoped database session.

    Returns:
        The updated notification.

    Raises:
        HTTPException: 404 if the notification doesn't exist or doesn't
            belong to the current user.
    """
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.read = True
    await db.commit()
    await db.refresh(notification)
    return notification
