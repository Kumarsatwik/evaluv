from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from ..database import get_async_session
from ..controllers.user_controller import UserController
from ..schemas.user import UserUpdateRequest, UserResponse


def get_user_controller(session: AsyncSession = Depends(get_async_session)) -> UserController:
    """Dependency to get UserController instance"""
    return UserController(session)


router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    request: Request,
    controller: UserController = Depends(get_user_controller)
):
    """Get user by ID (admin or self)"""
    return await controller.get_user_by_id(user_id, request)


@router.get("/", response_model=list[UserResponse])
async def get_all_users(
    request: Request,
    controller: UserController = Depends(get_user_controller)
):
    """Get all users (admin only)"""
    return await controller.get_all_users(request)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdateRequest,
    request: Request,
    controller: UserController = Depends(get_user_controller)
):
    """Update user by ID (admin or self)"""
    return await controller.update_user(user_id, UserUpdateRequest(**user_update.model_dump()), request)


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    request: Request,
    controller: UserController = Depends(get_user_controller)
):
    """Delete/deactivate user (admin only)"""
    return await controller.delete_user(user_id, request)


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    request: Request,
    controller: UserController = Depends(get_user_controller)
):
    """Activate user (admin only)"""
    return await controller.activate_user(user_id, request)
