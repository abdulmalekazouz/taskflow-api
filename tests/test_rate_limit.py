"""Tests for RateLimitMiddleware, in isolation from the shared `client` fixture.

The shared `client` fixture disables rate limiting entirely (see its
docstring in conftest.py) so the rest of the suite can fire many requests
without tripping it. This file builds its own tiny-limit app instead.
"""

from httpx import ASGITransport, AsyncClient

from taskflow.main import create_app
from taskflow.middleware import RateLimitConfig


async def test_requests_within_the_limit_succeed():
    app = create_app(rate_limit=RateLimitConfig(max_requests=3, window_seconds=60))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(3):
            response = await client.get("/health")
            assert response.status_code == 200


async def test_requests_over_the_limit_are_rejected_with_429():
    app = create_app(rate_limit=RateLimitConfig(max_requests=3, window_seconds=60))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(3):
            await client.get("/health")

        response = await client.get("/health")
        assert response.status_code == 429
        assert "Rate limit" in response.json()["detail"]
