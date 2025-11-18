"""
Redis-based rate limiting middleware
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import time
from ..utils.redis_client import redis_client
from ..config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting middleware"""

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)

        try:
            # Check rate limit
            rate_limit_result = await redis_client.check_rate_limit(
                identifier=client_ip,
                limit=settings.RATE_LIMIT_REQUESTS,
                window=settings.RATE_LIMIT_WINDOW
            )

            # Set rate limit headers
            response = await call_next(request)

            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit_result["remaining"]))
            response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset"])
            response.headers["X-RateLimit-Window"] = str(settings.RATE_LIMIT_WINDOW)

            return response

        except Exception as e:
            # If Redis is unavailable, allow the request but log the error
            print(f"Rate limiting error: {e}")
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(settings.RATE_LIMIT_REQUESTS - 1)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + settings.RATE_LIMIT_WINDOW)
            response.headers["X-RateLimit-Window"] = str(settings.RATE_LIMIT_WINDOW)
            return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Try X-Forwarded-For header first (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP if multiple are provided
            return forwarded_for.split(",")[0].strip()

        # Try X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to request.client.host (direct connection)
        return request.client.host if request.client else "unknown"


class RateLimitExceededException(HTTPException):
    """Custom exception for rate limit exceeded"""

    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )
