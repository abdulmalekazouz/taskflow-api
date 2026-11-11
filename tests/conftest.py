"""Shared pytest fixtures: an isolated in-memory database and HTTP client.

Each test gets its own fresh in-memory SQLite database (via a
`StaticPool` so the single in-memory connection is shared rather than
each new connection getting a blank database) and an `httpx.AsyncClient`
wired directly to the ASGI app -- no real server process involved.
"""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from taskflow.database import Base, get_db
from taskflow.main import create_app


@pytest_asyncio.fixture
async def session_factory():
    """Creates a fresh in-memory SQLite engine/session-factory per test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory):
    """An `AsyncClient` wired to a fresh app instance and test database.

    Overrides the `get_db` dependency so every request in a test uses the
    test's own in-memory database rather than the app's real one. The
    app's `lifespan` (which would otherwise create tables in the real,
    file-based database) is explicitly disabled.
    """
    app = create_app()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # ASGITransport never runs the app's lifespan handlers, so the
    # `lifespan`-driven init_models() call (which targets the real,
    # file-based database) never fires here -- tests only ever touch the
    # in-memory database created above.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def register_and_login(client):
    """Returns an async helper that registers a user and logs them in.

    Usage: `headers = await register_and_login("alice@example.com")` then
    pass `headers=headers` on subsequent requests made with `client`.
    """

    async def _register_and_login(
        email: str, password: str = "correct-horse", display_name: str = "Test User"
    ) -> dict[str, str]:
        await client.post(
            "/auth/register",
            json={"email": email, "password": password, "display_name": display_name},
        )
        response = await client.post(
            "/auth/login", data={"username": email, "password": password}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _register_and_login
