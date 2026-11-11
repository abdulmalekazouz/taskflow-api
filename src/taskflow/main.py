"""FastAPI application factory and entry point.

Run locally with:

    uvicorn taskflow.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from taskflow.api import auth, notifications, projects, tasks
from taskflow.database import init_models
from taskflow.middleware import RateLimitConfig, RateLimitMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Creates database tables on startup.

    Args:
        _app: The FastAPI application instance (unused, required by the
            `lifespan` context-manager signature FastAPI expects).

    Yields:
        Control back to FastAPI for the lifetime of the application.
    """
    await init_models()
    yield


def create_app(rate_limit: RateLimitConfig | None = RateLimitConfig()) -> FastAPI:
    """Builds the taskflow FastAPI application.

    Args:
        rate_limit: Rate-limit parameters for `RateLimitMiddleware`, or
            `None` to skip installing the middleware entirely (used by
            most of this project's own tests, so a large shared test
            suite firing many requests from the same client doesn't trip
            the limiter; see `tests/test_rate_limit.py` for a dedicated
            test of the middleware itself).

    Returns:
        A configured `FastAPI` instance with its lifespan handler
        registered. Routers are added by later modules via
        `app.include_router`.
    """
    app = FastAPI(
        title="taskflow",
        description="An async project/task-management REST API.",
        version="0.1.0",
        lifespan=lifespan,
    )
    if rate_limit is not None:
        app.add_middleware(RateLimitMiddleware, config=rate_limit)

    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(tasks.router)
    app.include_router(notifications.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        """Liveness check.

        Returns:
            A simple JSON status payload.
        """
        return {"status": "ok"}

    return app


app = create_app()
