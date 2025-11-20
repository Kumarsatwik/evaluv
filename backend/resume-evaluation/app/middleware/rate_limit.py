"""
Redis-based rate limiting middleware
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Optional
import time
from ..utils.redis_client import redis_client
from ..config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)

        try:
            result = await redis_client.check_rate_limit(
                identifier=client_ip,
                limit=settings.RATE_LIMIT_REQUESTS,
                window=settings.RATE_LIMIT_WINDOW
            )

            if not result["allowed"]:
                retry_after = max(1, int(result["reset"] - time.time()))
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": str(retry_after)}
                )

            response = await call_next(request)

            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(max(0, result["remaining"]))
            response.headers["X-RateLimit-Reset"] = str(result["reset"])
            response.headers["X-RateLimit-Window"] = str(settings.RATE_LIMIT_WINDOW)

            return response

        except Exception as e:
            # If Redis is down, don’t block the request; just signal fallback mode
            response = await call_next(request)

            now = int(time.time())
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(settings.RATE_LIMIT_REQUESTS - 1)
            response.headers["X-RateLimit-Reset"] = str(now + settings.RATE_LIMIT_WINDOW)
            response.headers["X-RateLimit-Window"] = str(settings.RATE_LIMIT_WINDOW)

            return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


class RateLimitExceededException(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )
