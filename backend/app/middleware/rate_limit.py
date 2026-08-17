import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limite simples por IP para uma única instância da API."""

    PUBLIC_PATHS = {"/", "/health", "/api/v1/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, *, requests: int, window_seconds: int) -> None:
        super().__init__(app)
        self.requests = requests
        self.window_seconds = window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        now = time.monotonic()
        key = request.client.host if request.client else "unknown"
        with self.lock:
            bucket = self.hits[key]
            while bucket and bucket[0] <= now - self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Limite de requisições excedido."},
                    headers={"Retry-After": str(self.window_seconds)},
                )
            bucket.append(now)
        return await call_next(request)
