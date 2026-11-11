"""Async SQLAlchemy engine, session factory, and declarative base.

Kept as small factory functions (rather than only module-level globals)
so tests can build an isolated in-memory engine instead of sharing the
app's real database.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from taskflow.config import get_settings


class Base(DeclarativeBase):
    """Declarative base class shared by every ORM model in this package."""


def create_engine_and_sessionmaker(
    database_url: str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Creates an async engine and a session factory bound to it.

    Args:
        database_url: A SQLAlchemy async connection string, e.g.
            `sqlite+aiosqlite:///./taskflow.db`.

    Returns:
        A `(engine, session_factory)` tuple.
    """
    engine = create_async_engine(database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


_settings = get_settings()
engine, SessionLocal = create_engine_and_sessionmaker(_settings.database_url)


async def init_models(bind_engine: AsyncEngine = engine) -> None:
    """Creates every table known to `Base.metadata`, if not already present.

    This project uses `create_all` instead of a migration tool (such as
    Alembic) to keep the project's scope focused; see the README
    "Limitations" section.

    Args:
        bind_engine: The engine to create tables on. Defaults to the
            module-level engine built from application settings.
    """
    async with bind_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped async DB session."""
    async with SessionLocal() as session:
        yield session


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """FastAPI dependency exposing the session factory itself.

    Unlike `get_db` (one request-scoped session), this is for code that
    needs to open its *own* session outside the request's lifecycle --
    chiefly background tasks, which run after the response (and the
    request-scoped session) may already be gone. Overridden in tests the
    same way as `get_db`, so background tasks exercised by a test use the
    test's in-memory database rather than the real one.

    Returns:
        The session factory to use.
    """
    return SessionLocal
