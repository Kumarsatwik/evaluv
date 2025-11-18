from sqlmodel import SQLModel, Field, Column
from typing import Optional
from datetime import datetime, timezone
import uuid
import sqlalchemy as sa


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    full_name: Optional[str] = Field(default=None)
    is_active: bool = True
    is_verified: bool = False
    role: str = Field(default="user")  # user, admin, moderator


class User(UserBase, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(sa_column=Column("hashed_password", sa.String, nullable=False))
    created_at: datetime = Field(sa_column=Column(sa.TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)))
    updated_at: datetime = Field(sa_column=Column(sa.TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)))
    
    # Relationships can be added here if needed
    # posts: List["Post"] = Relationship(back_populates="author")


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime