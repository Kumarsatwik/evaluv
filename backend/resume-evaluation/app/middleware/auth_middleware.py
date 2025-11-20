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

