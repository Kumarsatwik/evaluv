from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import uuid
from ..utils.security import (
    create_access_token,
)
from ..utils.redis_client import redis_client


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted using Redis"""
        return await redis_client.is_token_blacklisted(jti)

    async def blacklist_token(self, jti: str, user_id: UUID, expires_at: datetime):
        """Blacklist a token using Redis with expiration"""
        import time
        expires_at_timestamp = expires_at.timestamp()
        await redis_client.blacklist_token(jti, str(user_id), expires_at_timestamp)

    async def create_refresh_token(self, user_id: UUID) -> str:
        """Create and store refresh token in Redis"""
        refresh_token = str(uuid.uuid4())
        await redis_client.store_refresh_token(refresh_token, str(user_id))
        return refresh_token

    async def validate_refresh_token(self, token: str) -> Optional[UUID]:
        """Validate refresh token from Redis"""
        user_id_str = await redis_client.validate_refresh_token(token)
        return UUID(user_id_str) if user_id_str else None

    async def revoke_refresh_token(self, token: str):
        """Revoke refresh token from Redis"""
        await redis_client.revoke_refresh_token(token)

    async def generate_tokens(self, user_id: UUID, role: str) -> tuple[str, str]:
        """Generate access and refresh tokens"""
        # Create access token
        access_data = {
            "sub": str(user_id),
            "user_id": str(user_id),
            "role": role,
            "jti": str(uuid.uuid4())
        }
        access_token = create_access_token(
            data=access_data,
            expires_delta=timedelta(minutes=30)
        )
        
        # Create refresh token
        refresh_token = await self.create_refresh_token(user_id)
        
        return access_token, refresh_token
