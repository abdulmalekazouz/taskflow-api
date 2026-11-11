"""FastAPI application factory and entry point.

Run locally with:

    uvicorn taskflow.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from taskflow.api import auth, projects, tasks
from taskflow.database import init_models


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


def create_app() -> FastAPI:
    """Builds the taskflow FastAPI application.

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
    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(tasks.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        """Liveness check.

        Returns:
            A simple JSON status payload.
        """
        return {"status": "ok"}

    return app


app = create_app()
