"""Background notification delivery.

Stands in for a real email/push-notification integration: instead of
actually sending mail, it stores an in-app `Notification` row. See the
README "Limitations" section.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from taskflow.models.notification import Notification


async def notify_assignment(
    session_factory: async_sessionmaker[AsyncSession], user_id: int, message: str
) -> None:
    """Persists a notification, intended to run as a FastAPI background task.

    Runs after the triggering request's response has already been sent,
    so it deliberately opens its own fresh database session (via
    `session_factory`) instead of reusing the request-scoped session,
    which may already be closing by that point. The factory is passed in
    (via the `get_session_factory` dependency) rather than imported as a
    module-level global, so tests can point it at an isolated in-memory
    database instead of the real one.

    Args:
        session_factory: A session factory, e.g. from
            `taskflow.database.get_session_factory`.
        user_id: The user to notify.
        message: The notification text.
    """
    async with session_factory() as session:
        session.add(Notification(user_id=user_id, message=message))
        await session.commit()
