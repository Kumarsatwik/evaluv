from fastapi import HTTPException, status, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime
from ..services.user_services import UserService
from ..services.auth_service import AuthService
from ..schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserLoginRequest,
    TokenResponse
)
from ..schemas.auth import RefreshTokenRequest, TokenBlacklistRequest, AuthResponse, ChangePasswordRequest
from ..utils.security import verify_token, verify_password_strength
from ..utils.exceptions import (
    InvalidCredentialsException,
    UserNotFoundException,
    DuplicateUserException,
    InsufficientPermissionsException
)
from ..config import settings
from ..models.user import UserCreate, UserUpdate


class AuthController:
    """Controller for authentication related operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)
        self.auth_service = AuthService(session)

    async def register(self, user_create: UserCreateRequest) -> UserResponse:
        """Register a new user"""
        if not verify_password_strength(user_create.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements"
            )

        try:
            db_user = await self.user_service.create_user(
                UserCreate(**user_create.model_dump())
            )
            return UserResponse.model_validate(db_user)
        except DuplicateUserException:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email or username already exists"
            )

    async def login(self, login_data: UserLoginRequest) -> TokenResponse:
        """Login user and return tokens"""
        user = await self.user_service.authenticate_user(
            login_data.username,
            login_data.password
        )

        if not user:
            raise InvalidCredentialsException()

        access_token, refresh_token = await self.auth_service.generate_tokens(
            user.id,
            user.role
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def refresh_token(self, refresh_request: RefreshTokenRequest) -> TokenResponse:
        """Refresh access token using refresh token"""
        user_id = await self.auth_service.validate_refresh_token(refresh_request.refresh_token)
        if not user_id:
            raise InvalidCredentialsException()

        # Get user to get role
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        # Generate new tokens
        access_token, new_refresh_token = await self.auth_service.generate_tokens(
            user.id,
            user.role
        )

        # Revoke old refresh token
        await self.auth_service.revoke_refresh_token(refresh_request.refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def logout(self, token_blacklist: TokenBlacklistRequest, request: Request) -> AuthResponse:
        """Logout user and blacklist token"""
        payload = verify_token(token_blacklist.token)
        if not payload:
            raise InvalidCredentialsException()

        # Blacklist the access token
        expires_at = datetime.fromtimestamp(payload.get("exp"))
        await self.auth_service.blacklist_token(
            payload.get("jti"),
            payload.get("user_id"),
            expires_at
        )

        # Revoke refresh token if provided in request state (e.g., from refresh token endpoint)
        if hasattr(request, 'state') and hasattr(request.state, 'refresh_token'):
            await self.auth_service.revoke_refresh_token(request.state.refresh_token)

        return AuthResponse(message="Successfully logged out")

    async def get_current_user(self, request: Request) -> UserResponse:
        """Get current user info"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        user = await self.user_service.get_user_by_id(request.state.user["id"])

        if not user:
            raise UserNotFoundException()

        return UserResponse.model_validate(user)

    async def update_current_user(self, user_update: UserUpdateRequest, request: Request) -> UserResponse:
        """Update current user info"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        user = await self.user_service.update_user(
            request.state.user["id"],
            UserUpdate(**user_update.model_dump(exclude_unset=True))
        )

        return UserResponse.model_validate(user)

    async def change_password(self, change_request: ChangePasswordRequest, request: Request) -> AuthResponse:
        """Change user password"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        if not verify_password_strength(change_request.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password does not meet security requirements"
            )

        success = await self.user_service.change_password(
            request.state.user["id"],
            change_request.old_password,
            change_request.new_password
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect"
            )

        return AuthResponse(message="Password changed successfully")

    async def get_all_users(self, request: Request) -> list[dict]:
        """Get all users (admin only)"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        if request.state.user["role"] != "admin":
            raise InsufficientPermissionsException()

        # Implementation for getting all users would go here
        # For now, return placeholder
        users = await self.user_service.get_all_users()
        return [UserResponse.model_validate(user) for user in users]

    @staticmethod
    def require_role(required_role: str):
        """Dependency to check user role"""
        def role_checker(request: Request):
            if not hasattr(request.state, 'user') or not request.state.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )

            if request.state.user["role"] != required_role:
                raise InsufficientPermissionsException()

            return request.state.user

        return role_checker
