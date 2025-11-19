from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid
import sqlalchemy as sa

if TYPE_CHECKING:
    from .user import User


class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(index=True)
    description: str = Field()
    skills: str = Field()  
    experience: str = Field()  
    location: Optional[str] = Field(default=None)
    salary_range: Optional[str] = Field(default=None)
    job_type: str = Field(default="full-time")  # e.g., full-time, part-time, contract
    status: str = Field(default="active")  # active, inactive, closed
    embedding_status: str = Field(default="pending") # pending, completed, failed
    qdrant_point_id: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(sa_column=Column(sa.TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)))
    updated_at: datetime = Field(sa_column=Column(sa.TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)))

    # Relationships
    created_by: uuid.UUID = Field(foreign_key="users.id")
    creator: "User" = Relationship(back_populates="jobs")
