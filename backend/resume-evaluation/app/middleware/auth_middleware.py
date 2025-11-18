from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
from ..utils.security import verify_token
from ..services.auth_service import AuthService
from ..database import get_async_session


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        # Add current user info to request state if token is present
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Verify token
            payload = verify_token(token)
            if payload:
                # Check if token is blacklisted
                async for session in get_async_session():
                    auth_service = AuthService(session)
                    if await auth_service.is_token_blacklisted(payload.get("jti")):
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"detail": "Token has been blacklisted"}
                        )
                
                # Add user info to request state
                request.state.user = {
                    "id": payload.get("user_id"),
                    "role": payload.get("role"),
                    "sub": payload.get("sub")
                }
        
        response = await call_next(request)
        return response


# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window: int = 3600):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests = {}

    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = request.client.host
        
        # Get current timestamp
        current_time = int(time.time())
        window_start = current_time - (current_time % self.window)
        
        # Initialize client data if not exists
        if client_ip not in self.requests:
            self.requests[client_ip] = {}
        
        # Clean old requests
        for timestamp in list(self.requests[client_ip].keys()):
            if timestamp < window_start:
                del self.requests[client_ip][timestamp]
        
        # Count requests in current window
        request_count = sum(self.requests[client_ip].values())
        
        if request_count >= self.max_requests:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Record this request
        if window_start not in self.requests[client_ip]:
            self.requests[client_ip][window_start] = 0
        self.requests[client_ip][window_start] += 1
        
        response = await call_next(request)
        return response
