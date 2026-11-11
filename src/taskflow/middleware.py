"""A simple in-memory, fixed-window request-rate limiter."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate-limit parameters.

    Attributes:
        max_requests: How many requests a single client IP may make
            within `window_seconds`.
        window_seconds: The size of the sliding time window, in seconds.
    """

    max_requests: int = 120
    window_seconds: float = 60.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limits each client IP to a fixed number of requests per time window.

    This is a single-process, in-memory limiter: a reasonable demo of the
    pattern, not a production-grade one. It does not coordinate across
    multiple processes/workers -- a real deployment behind more than one
    worker would need a shared store (e.g. Redis) instead. See the
    README "Limitations" section.
    """

    def __init__(self, app, config: RateLimitConfig | None = None) -> None:
        """Initializes the middleware.

        Args:
            app: The ASGI application to wrap.
            config: Rate-limit parameters; defaults to `RateLimitConfig()`.
        """
        super().__init__(app)
        self._config = config or RateLimitConfig()
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        """Rejects the request with 429 if its client IP is over the limit.

        Args:
            request: The incoming request.
            call_next: Calls the next handler in the middleware chain.

        Returns:
            A 429 JSON response if the client has exceeded the limit for
            the current window, otherwise the downstream response.
        """
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - self._config.window_seconds

        hits = self._hits[client_ip]
        while hits and hits[0] < window_start:
            hits.pop(0)

        if len(hits) >= self._config.max_requests:
            return JSONResponse(
                {"detail": "Rate limit exceeded. Please try again later."},
                status_code=429,
            )

        hits.append(now)
        return await call_next(request)
