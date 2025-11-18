
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from uuid import UUID
from ..models.user import UserUpdate
from ..services.user_services import UserService
from ..schemas.user import UserResponse, UserUpdateRequest
from ..utils.exceptions import UserNotFoundException, InsufficientPermissionsException
from fastapi import HTTPException, status, Request


class UserController:
    """Controller for user management operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)

    async def get_user_by_id(self, user_id: UUID, request: Request) -> UserResponse:
        """Get user by ID (admin or self only)"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        # Allow admin or self to view
        if request.state.user["role"] != "admin" and request.state.user["id"] != str(user_id):
            raise InsufficientPermissionsException()

        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        return UserResponse.model_validate(user)

    async def get_all_users(self, request: Request) -> List[UserResponse]:
        """Get all users (admin only)"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        if request.state.user["role"] != "admin":
            raise InsufficientPermissionsException()

        users = await self.user_service.get_all_users()
        return [UserResponse.model_validate(user) for user in users]

    async def update_user(self, user_id: UUID, user_update: UserUpdateRequest, request: Request) -> UserResponse:
        """Update user (admin or self only)"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        # Allow admin or self to update
        if request.state.user["role"] != "admin" and request.state.user["id"] != str(user_id):
            raise InsufficientPermissionsException()

        user = await self.user_service.update_user(user_id, UserUpdate(**user_update.model_dump(exclude_unset=True)))
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: UUID, request: Request) -> dict:
        """Delete user (admin only)"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        if request.state.user["role"] != "admin":
            raise InsufficientPermissionsException()

        # Prevent self-deletion
        if request.state.user["id"] == str(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        # Implementation for soft delete or hard delete
        # For now, set is_active to False
        user.is_active = False
        await self.session.commit()

        return {"message": "User deactivated successfully"}

    async def activate_user(self, user_id: UUID, request: Request) -> UserResponse:
        """Activate user (admin only)"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        if request.state.user["role"] != "admin":
            raise InsufficientPermissionsException()

        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        user.is_active = True
        await self.session.commit()
        await self.session.refresh(user)

        return UserResponse.model_validate(user)
