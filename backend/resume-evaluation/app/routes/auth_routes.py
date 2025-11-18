from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from ..database import get_async_session
from ..controllers.auth_controller import AuthController
from ..schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserLoginRequest,
    TokenResponse
)
from ..schemas.auth import RefreshTokenRequest, TokenBlacklistRequest, AuthResponse, ChangePasswordRequest


def get_auth_controller(session: AsyncSession = Depends(get_async_session)) -> AuthController:
    """Dependency to get AuthController instance"""
    return AuthController(session)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_create: UserCreateRequest,
    controller: AuthController = Depends(get_auth_controller)
):
    """Register a new user"""
    return await controller.register(user_create)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLoginRequest,
    controller: AuthController = Depends(get_auth_controller)
):
    """Login user and return tokens"""
    return await controller.login(login_data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    controller: AuthController = Depends(get_auth_controller)
):
    """Refresh access token using refresh token"""
    return await controller.refresh_token(refresh_request)


@router.post("/logout", response_model=AuthResponse)
async def logout(
    token_blacklist: TokenBlacklistRequest,
    request: Request,
    controller: AuthController = Depends(get_auth_controller)
):
    """Logout user and blacklist token"""
    return await controller.logout(token_blacklist, request)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    controller: AuthController = Depends(get_auth_controller)
):
    """Get current user info"""
    return await controller.get_current_user(request)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdateRequest,
    request: Request,
    controller: AuthController = Depends(get_auth_controller)
):
    """Update current user info"""
    return await controller.update_current_user(user_update, request)


@router.post("/change-password", response_model=AuthResponse)
async def change_password(
    change_request: ChangePasswordRequest,
    request: Request,
    controller: AuthController = Depends(get_auth_controller)
):
    """Change user password"""
    return await controller.change_password(change_request, request)


# Protected routes with role-based access
@router.get("/admin/users", response_model=list[UserResponse])
async def get_all_users(
    request: Request,
    controller: AuthController = Depends(get_auth_controller)
):
    """Get all users (admin only)"""
    return await controller.get_all_users(request)
