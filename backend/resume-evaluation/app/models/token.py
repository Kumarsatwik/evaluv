from sqlmodel import SQLModel, Field, Column
from datetime import datetime, timezone
import uuid
import sqlalchemy as sa


class TokenBlacklist(SQLModel, table=True):
    __tablename__ = "token_blacklist"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    jti: str = Field(index=True, unique=True)  # JWT ID
    user_id: uuid.UUID
    expires_at: datetime = Field(sa_column=Column(sa.TIMESTAMP(timezone=True)))
    created_at: datetime = Field(sa_column=Column(sa.TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)))


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    token: str = Field(index=True, unique=True)
    user_id: uuid.UUID
    expires_at: datetime = Field(sa_column=Column(sa.TIMESTAMP(timezone=True)))
    is_active: bool = True
    created_at: datetime = Field(sa_column=Column(sa.TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)))
