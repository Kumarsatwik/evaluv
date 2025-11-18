from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import uuid
from ..models.token import TokenBlacklist, RefreshToken
from ..utils.security import (
    create_access_token, 
)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        statement = select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        result = await self.session.exec(statement)
        token = result.first()
        return token is not None

    async def blacklist_token(self, jti: str, user_id: UUID, expires_at: datetime):
        """Blacklist a token"""
        blacklisted_token = TokenBlacklist(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at
        )
        self.session.add(blacklisted_token)
        await self.session.commit()

    async def create_refresh_token(self, user_id: UUID) -> str:
        """Create and store refresh token"""
        refresh_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days
        
        db_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=user_id,
            expires_at=expires_at
        )
        
        self.session.add(db_refresh_token)
        await self.session.commit()
        
        return refresh_token

    async def validate_refresh_token(self, token: str) -> Optional[UUID]:
        """Validate refresh token"""
        statement = select(RefreshToken).where(
            RefreshToken.token == token,
            RefreshToken.is_active == True,
            RefreshToken.expires_at > datetime.utcnow()
        )
        result = await self.session.exec(statement)
        refresh_token = result.first()
        
        if not refresh_token:
            return None
        
        return refresh_token.user_id

    async def revoke_refresh_token(self, token: str):
        """Revoke refresh token"""
        statement = select(RefreshToken).where(RefreshToken.token == token)
        result = await self.session.exec(statement)
        refresh_token = result.first()
        
        if refresh_token:
            refresh_token.is_active = False
            await self.session.commit()

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