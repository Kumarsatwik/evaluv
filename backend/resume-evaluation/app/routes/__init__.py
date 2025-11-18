"""Routes package initialization"""

# Import routers to make them available at package level
from .auth_routes import router as auth_router
from .user_routes import router as user_router

__all__ = ["auth_router", "user_router"]
